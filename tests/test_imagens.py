import functools
import io
import struct

import pytest
from PIL import Image, ImageCms, ImageFile, features
from PIL.PngImagePlugin import PngInfo
from sqlalchemy import select

from app import imagens
from app.models import Produto

VALIDO = {"nome": "Caneta", "valor": "12,50", "fornecedor": "Papelaria X"}


def gerar(formato, tamanho=(16, 16), modo="RGB", cor=(200, 30, 30), **opcoes):
    buf = io.BytesIO()
    Image.new(modo, tamanho, cor).save(buf, formato, **opcoes)
    return buf.getvalue()


PNG = gerar("PNG")
JPG = gerar("JPEG")
WEBP = gerar("WEBP")


@pytest.fixture(autouse=True)
def pasta_uploads(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path))
    return tmp_path


def enviar(client, conteudo, arquivo="foto.png", tipo="image/png", **campos):
    return client.post(
        "/produtos",
        data={**VALIDO, **campos},
        files={"imagem": (arquivo, conteudo, tipo)},
        follow_redirects=False,
    )


@pytest.mark.parametrize("conteudo,ext", [(PNG, "png"), (JPG, "jpg"), (WEBP, "webp")])
def test_upload_valido(client, sessao, pasta_uploads, conteudo, ext):
    assert enviar(client, conteudo).status_code == 303
    p = sessao.scalars(select(Produto)).one()
    assert p.imagem_arquivo.endswith("." + ext)
    gravado = Image.open(pasta_uploads / p.imagem_arquivo)
    assert gravado.format == {"png": "PNG", "jpg": "JPEG", "webp": "WEBP"}[ext]
    assert imagens.NOME_VALIDO.fullmatch(p.imagem_arquivo)


def test_nome_gerado_pela_aplicacao(client, sessao, pasta_uploads):
    enviar(client, PNG, arquivo="../../etc/passwd.png")
    p = sessao.scalars(select(Produto)).one()
    assert "passwd" not in p.imagem_arquivo and "/" not in p.imagem_arquivo
    assert [f.name for f in pasta_uploads.iterdir()] == [p.imagem_arquivo]


def test_tipo_validado_pelo_conteudo_nao_pela_extensao(client, sessao, pasta_uploads):
    r = enviar(client, b"<script>alert(1)</script>", arquivo="x.png", tipo="image/png")
    assert r.status_code == 422
    assert "JPEG, PNG ou WebP" in r.text
    assert sessao.scalars(select(Produto)).all() == []
    assert list(pasta_uploads.iterdir()) == []


def test_svg_recusado(client, sessao):
    r = enviar(client, b"<svg xmlns='http://www.w3.org/2000/svg'/>", arquivo="a.svg", tipo="image/svg+xml")
    assert r.status_code == 422


def test_png_com_extensao_txt_e_aceito_pelo_conteudo(client, sessao):
    assert enviar(client, PNG, arquivo="foto.txt", tipo="text/plain").status_code == 303
    assert sessao.scalars(select(Produto)).one().imagem_arquivo.endswith(".png")


def test_tamanho_excedido(client, sessao, pasta_uploads):
    r = enviar(client, PNG + b"0" * imagens.TAMANHO_MAXIMO)
    assert r.status_code == 422
    assert "2 MB" in r.text
    assert sessao.scalars(select(Produto)).all() == []
    assert list(pasta_uploads.iterdir()) == []


def test_tamanho_exato_aceito(client, sessao):
    conteudo = PNG + b"0" * (imagens.TAMANHO_MAXIMO - len(PNG))  # lixo depois do IEND
    assert len(conteudo) == imagens.TAMANHO_MAXIMO
    assert enviar(client, conteudo).status_code == 303


def test_imagem_de_3mb_volta_como_422_na_pagina_com_campos_preservados(client, sessao, pasta_uploads):
    r = enviar(client, PNG + b"0" * (3 * 1024 * 1024), nome="Preservado", valor="9,90")
    assert r.status_code == 422
    assert "A imagem deve ter no máximo 2 MB." in r.text
    assert 'value="Preservado"' in r.text and 'value="9,90"' in r.text
    assert sessao.scalars(select(Produto)).all() == []
    assert list(pasta_uploads.iterdir()) == []


def test_requisicao_acima_do_teto_recusada_por_content_length(client, sessao):
    r = client.post("/produtos", content=b"x", headers={"content-length": str(11 * 1024 * 1024)})
    assert r.status_code == 413


def test_post_chunked_sem_content_length_recusado(client, sessao):
    def corpo():
        yield b"nome=x"

    r = client.post("/produtos", content=corpo(),
                    headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 411
    assert sessao.scalars(select(Produto)).all() == []


def test_commit_falhou_remove_arquivo(client, sessao, pasta_uploads, monkeypatch):
    def falha():
        raise RuntimeError("banco caiu")

    monkeypatch.setattr(sessao, "commit", falha)
    with pytest.raises(RuntimeError):
        enviar(client, PNG)
    assert list(pasta_uploads.iterdir()) == []  # nem arquivo nem temporário


def test_sem_imagem(client, sessao):
    r = client.post("/produtos", data=VALIDO, follow_redirects=False)
    assert r.status_code == 303
    assert sessao.scalars(select(Produto)).one().imagem_arquivo is None
    assert "sem imagem" in client.get("/").text


def test_campo_de_arquivo_vazio_do_navegador(client, sessao):
    r = client.post("/produtos", data=VALIDO, files={"imagem": ("", b"", "application/octet-stream")},
                    follow_redirects=False)
    assert r.status_code == 303
    assert sessao.scalars(select(Produto)).one().imagem_arquivo is None


def test_erro_de_campo_nao_salva_imagem(client, sessao, pasta_uploads):
    assert enviar(client, PNG, nome="").status_code == 422
    assert list(pasta_uploads.iterdir()) == []


def test_listagem_exibe_imagem_e_servico_de_arquivo(client, sessao):
    enviar(client, PNG)
    nome = sessao.scalars(select(Produto)).one().imagem_arquivo
    assert f'src="/uploads/{nome}"' in client.get("/").text
    r = client.get(f"/uploads/{nome}")
    assert r.status_code == 200
    assert r.content.startswith(b"\x89PNG")
    assert r.headers["content-type"] == "image/png"
    assert r.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("nome", ["..%2f..%2fetc%2fpasswd", "inexistente.png", "a" * 32 + ".png", "x.svg"])
def test_servico_de_arquivo_recusa_nomes_invalidos(client, nome):
    assert client.get(f"/uploads/{nome}").status_code == 404


def test_nome_do_produto_escapado_no_alt(client, sessao):
    enviar(client, PNG, nome='"><script>x</script>')
    assert "<script>x</script>" not in client.get("/").text


# ---------------------------------------------------------------- T-0010: Pillow

CORROMPIDA = "A imagem está corrompida ou não pôde ser lida."
DIMENSAO = "A imagem deve ter no máximo 10.000 px de lado e 50 megapixels."
SCRIPT = b"<script>alert(1)</script>"


def gravado(sessao, pasta):
    p = sessao.scalars(select(Produto)).one()
    return Image.open(pasta / p.imagem_arquivo), (pasta / p.imagem_arquivo).read_bytes()


def exif_com(orientacao=None, marcador=b"MARCA-EXIF-UNICA"):
    ex = Image.Exif()
    if orientacao:
        ex[0x0112] = orientacao
    ex[0x010F] = marcador.decode()  # Make
    ex.get_ifd(0x8825)[1] = "S"  # GPS: LatitudeRef
    return ex


def test_webp_tem_suporte_na_wheel():
    assert features.check("webp") is True


def test_jpeg_grande_regravado_com_dimensoes(client, sessao, pasta_uploads):
    assert enviar(client, gerar("JPEG", (1200, 800))).status_code == 303
    im, _ = gravado(sessao, pasta_uploads)
    assert im.format == "JPEG" and im.size == (1200, 800)


def test_png_com_transparencia_mantem_alfa(client, sessao, pasta_uploads):
    r = enviar(client, gerar("PNG", (8, 8), "RGBA", (255, 0, 0, 100)))
    assert r.status_code == 303
    im, _ = gravado(sessao, pasta_uploads)
    assert im.format == "PNG" and im.mode == "RGBA" and im.getpixel((0, 0))[3] == 100


def test_png_paleta_com_transparencia(client, sessao, pasta_uploads):
    base = Image.new("P", (8, 8), 0)
    base.putpalette([255, 0, 0] * 256)
    buf = io.BytesIO()
    base.save(buf, "PNG", transparency=0)
    assert enviar(client, buf.getvalue()).status_code == 303
    im, _ = gravado(sessao, pasta_uploads)
    assert im.convert("RGBA").getpixel((0, 0))[3] == 0


def test_jpeg_orientacao_6_gravado_girado_e_sem_exif(client, sessao, pasta_uploads):
    conteudo = gerar("JPEG", (40, 20), exif=exif_com(6))
    assert Image.open(io.BytesIO(conteudo)).getexif()[0x0112] == 6
    assert enviar(client, conteudo).status_code == 303
    im, bruto = gravado(sessao, pasta_uploads)
    assert im.size == (20, 40)
    assert len(im.getexif()) == 0 and "exif" not in im.info
    assert b"MARCA-EXIF-UNICA" not in bruto


def test_png_com_extensao_jpg(client, sessao):
    assert enviar(client, PNG, arquivo="foto.jpg", tipo="image/jpeg").status_code == 303
    assert sessao.scalars(select(Produto)).one().imagem_arquivo.endswith(".png")


@pytest.mark.parametrize("formato,ext", [("JPEG", "jpg"), ("PNG", "png"), ("WEBP", "webp")])
def test_poliglota_script_anexado_nao_chega_ao_arquivo(client, sessao, pasta_uploads, formato, ext):
    assert enviar(client, gerar(formato) + SCRIPT).status_code == 303
    nome = sessao.scalars(select(Produto)).one().imagem_arquivo
    assert nome.endswith(ext)
    assert SCRIPT not in (pasta_uploads / nome).read_bytes()
    r = client.get(f"/uploads/{nome}")
    assert r.headers["content-type"] == imagens.TIPOS[ext]
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]


def test_jpeg_aleatorio_e_corrompido(client, sessao, pasta_uploads):
    r = enviar(client, b"\xff\xd8\xff" + bytes(range(256)) * 4, nome="Fica")
    assert r.status_code == 422 and CORROMPIDA in r.text
    assert 'value="Fica"' in r.text
    assert list(pasta_uploads.iterdir()) == []


@pytest.mark.parametrize("formato", ["PNG", "JPEG", "WEBP"])
def test_cortada_pela_metade(client, formato):
    img = Image.effect_noise((200, 200), 80).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, formato)
    r = enviar(client, buf.getvalue()[: buf.tell() // 2])
    assert r.status_code == 422 and CORROMPIDA in r.text


def test_riff_webp_com_corpo_de_png(client, pasta_uploads):
    r = enviar(client, b"RIFF\x00\x00\x00\x00WEBP" + PNG)
    assert r.status_code == 422 and CORROMPIDA in r.text


@pytest.mark.parametrize("formato", ["GIF", "BMP", "TIFF"])
def test_outros_formatos_recusados_sem_decodificar(client, monkeypatch, formato):
    def nao_deve_chamar(self):
        raise AssertionError("load chamado")

    monkeypatch.setattr(ImageFile.ImageFile, "load", nao_deve_chamar)
    r = enviar(client, gerar(formato), arquivo="x.jpg", tipo="image/jpeg")
    assert r.status_code == 422 and "JPEG, PNG ou WebP" in r.text


def test_formatos_restritos_no_open(monkeypatch):
    visto = {}
    original = Image.open

    def espiao(*a, **kw):
        visto.update(kw)
        return original(*a, **kw)

    monkeypatch.setattr(Image, "open", espiao)
    imagens.processar_imagem(PNG)
    assert visto["formats"] == ["JPEG", "PNG", "WEBP"]


def test_tiff_com_assinatura_jpeg_nao_decodifica(monkeypatch):
    monkeypatch.setattr(ImageFile.ImageFile, "load", lambda self: pytest.fail("load"))
    ext, dados, erro = imagens.processar_imagem(b"\xff\xd8\xff" + gerar("TIFF"))
    assert erro == CORROMPIDA and dados is None


@pytest.mark.parametrize(
    "tamanho",
    [(20_000, 20_000), (8_000, 8_000), (10_001, 10)],
)
def test_dimensao_acima_do_limite_sem_decodificar(client, monkeypatch, pasta_uploads, tamanho):
    conteudo = gerar("PNG", tamanho, "1", 0)
    assert len(conteudo) < 200_000

    def nao_deve_chamar(self):
        raise AssertionError("load chamado")

    monkeypatch.setattr(ImageFile.ImageFile, "load", nao_deve_chamar)
    r = enviar(client, conteudo)
    assert r.status_code == 422 and DIMENSAO in r.text
    assert list(pasta_uploads.iterdir()) == []


def test_limite_exato_de_area_e_de_lado_aceito(client):
    assert enviar(client, gerar("PNG", (10_000, 5_000), "1", 0)).status_code == 303
    assert enviar(client, gerar("PNG", (10_000, 1), "1", 0)).status_code == 303


def test_decompression_bomb_vira_mensagem_de_dimensao(monkeypatch):
    def bomba(*a, **kw):
        raise Image.DecompressionBombError("x")

    monkeypatch.setattr(Image, "open", bomba)
    assert imagens.processar_imagem(PNG)[2] == DIMENSAO


def test_max_image_pixels_nao_foi_desligado():
    assert Image.MAX_IMAGE_PIXELS is not None
    assert imagens.AREA_MAXIMA == 50_000_000 and imagens.LADO_MAXIMO == 10_000


def _png_solido():
    return gerar("PNG", (64, 64), "RGB", (10, 20, 30))


def _chunk_trocado(png, tipo, novo_tamanho):
    i = png.index(tipo) - 4
    return png[:i] + struct.pack(">I", novo_tamanho) + png[i + 4 :]


def test_png_idat_tamanho_zero_syntaxerror(client):
    ruim = _chunk_trocado(_png_solido(), b"IDAT", 0)
    with pytest.raises(SyntaxError):
        Image.open(io.BytesIO(ruim)).load()
    r = enviar(client, ruim)
    assert r.status_code == 422 and CORROMPIDA in r.text


def test_png_ihdr_tamanho_12_valueerror(client):
    ruim = _chunk_trocado(_png_solido(), b"IHDR", 12)
    with pytest.raises(ValueError):
        Image.open(io.BytesIO(ruim)).load()
    r = enviar(client, ruim)
    assert r.status_code == 422 and CORROMPIDA in r.text


def _mutacoes():
    import random

    rng = random.Random(20261001)
    bases = []
    for f in ("JPEG", "PNG", "WEBP"):
        img = Image.effect_noise((48, 48), 60).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, f)
        bases.append(buf.getvalue())
    casos = []
    for n in range(330):
        b = bytearray(bases[n % 3])
        modo = rng.choice(["troca", "corta", "insere"])
        if modo == "troca":
            for _ in range(rng.randint(1, 8)):
                b[rng.randrange(len(b))] = rng.randrange(256)
        elif modo == "corta":
            del b[rng.randrange(8, len(b)) :]
        else:
            pos = rng.randrange(len(b))
            b[pos:pos] = bytes(rng.randrange(256) for _ in range(rng.randint(1, 64)))
        casos.append(bytes(b))
    return casos


@pytest.mark.parametrize("conteudo", _mutacoes())
def test_arquivos_mutados_nunca_dao_500(client, pasta_uploads, conteudo):
    r = enviar(client, conteudo)
    assert r.status_code in (303, 422)
    if r.status_code == 422:
        for proibido in ("Traceback", "PIL", "Error"):
            assert proibido not in r.text


def test_mpo_vira_jpeg_de_um_quadro(client, sessao, pasta_uploads):
    buf = io.BytesIO()
    a, b = Image.new("RGB", (32, 32), "red"), Image.new("RGB", (32, 32), "blue")
    a.save(buf, "MPO", save_all=True, append_images=[b])
    assert Image.open(io.BytesIO(buf.getvalue())).format == "MPO"
    assert enviar(client, buf.getvalue()).status_code == 303
    im, _ = gravado(sessao, pasta_uploads)
    assert im.format == "JPEG" and getattr(im, "n_frames", 1) == 1


def test_apng_e_webp_animado_viram_um_quadro(client, sessao, pasta_uploads):
    quadros = [Image.new("RGB", (16, 16), c) for c in ("red", "blue", "green", "black")]
    buf = io.BytesIO()
    quadros[0].save(buf, "PNG", save_all=True, append_images=quadros[1:])
    assert Image.open(io.BytesIO(buf.getvalue())).n_frames == 4
    assert enviar(client, buf.getvalue()).status_code == 303
    buf2 = io.BytesIO()
    quadros[0].save(buf2, "WEBP", save_all=True, append_images=quadros[1:2])
    assert enviar(client, buf2.getvalue()).status_code == 303
    for p in sessao.scalars(select(Produto)).all():
        assert getattr(Image.open(pasta_uploads / p.imagem_arquivo), "n_frames", 1) == 1


def _tudo_de_metadados(formato):
    marcadores = {b"MARCA-EXIF-UNICA", b"MARCA-XMP-UNICA", b"MARCA-COM-UNICA", b"MARCA-TXT-UNICA"}
    xmp = b'<x:xmpmeta xmlns:x="adobe:ns:meta/">MARCA-XMP-UNICA</x:xmpmeta>'
    ex = exif_com(marcador=b"MARCA-EXIF-UNICA")
    if formato == "JPEG":
        return marcadores, gerar("JPEG", exif=ex, xmp=xmp, comment=b"MARCA-COM-UNICA")
    if formato == "WEBP":
        return marcadores, gerar("WEBP", exif=ex, xmp=xmp)
    info = PngInfo()
    info.add_text("Comment", "MARCA-TXT-UNICA")
    info.add_itxt("XML:com.adobe.xmp", xmp.decode(), zip=False)
    return marcadores, gerar("PNG", pnginfo=info, exif=ex)


@pytest.mark.parametrize("formato", ["JPEG", "PNG", "WEBP"])
def test_sem_metadados_no_arquivo_gravado(client, sessao, pasta_uploads, formato):
    marcadores, conteudo = _tudo_de_metadados(formato)
    assert any(m in conteudo for m in marcadores)
    assert enviar(client, conteudo).status_code == 303
    im, bruto = gravado(sessao, pasta_uploads)
    assert not any(m in bruto for m in marcadores)
    assert len(im.getexif()) == 0
    for chave in ("exif", "xmp", "comment", "XML:com.adobe.xmp", "Comment"):
        assert chave not in im.info
    assert not getattr(im, "text", {})


@functools.cache  # createProfile grava a hora no cabecalho: gerar 2x numa virada de segundo difere
def _icc_srgb():
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


@pytest.mark.parametrize("formato", ["JPEG", "PNG", "WEBP"])
def test_icc_valido_mantido_e_reserializado(client, sessao, pasta_uploads, formato):
    base = _icc_srgb()
    assert enviar(client, gerar(formato, icc_profile=base)).status_code == 303
    im, _ = gravado(sessao, pasta_uploads)
    assert im.info.get("icc_profile") == base


@pytest.mark.parametrize("formato", ["JPEG", "PNG", "WEBP"])
def test_icc_com_script_anexado_e_limpo(client, sessao, pasta_uploads, formato):
    sujo = _icc_srgb() + SCRIPT + b"A" * 200_000
    assert enviar(client, gerar(formato, icc_profile=sujo)).status_code == 303
    im, _ = gravado(sessao, pasta_uploads)
    lido = im.info.get("icc_profile")
    assert lido is not None and SCRIPT not in lido and lido == _icc_srgb()


@pytest.mark.parametrize("formato", ["JPEG", "PNG", "WEBP"])
def test_icc_aleatorio_descartado(client, sessao, pasta_uploads, formato):
    lixo = bytes(range(256)) * 4
    assert enviar(client, gerar(formato, icc_profile=lixo)).status_code == 303
    im, _ = gravado(sessao, pasta_uploads)
    assert "icc_profile" not in im.info


def test_codigo_nao_transforma_cores():
    fonte = open(imagens.__file__, encoding="utf-8").read()
    proibidos = ("buildTransform", "profileToProfile", "applyTransform", "MAX_IMAGE_PIXELS", "LOAD_TRUNCATED")
    for proibido in proibidos:
        assert proibido not in fonte


def test_servidor_ocupado_nao_chama_o_pillow_e_da_503(client, sessao, pasta_uploads, monkeypatch):
    import threading

    monkeypatch.setattr(imagens, "_VAGAS", threading.BoundedSemaphore(1))
    imagens._VAGAS.acquire()
    monkeypatch.setattr(imagens, "ESPERA_MAXIMA", 0.05)
    monkeypatch.setattr(Image, "open", lambda *a, **k: pytest.fail("Pillow chamado"))
    r = enviar(client, PNG, nome="Mantido", valor="7,00")
    assert r.status_code == 503
    assert "Servidor ocupado, tente de novo." in r.text
    assert 'value="Mantido"' in r.text and 'value="7,00"' in r.text
    assert sessao.scalars(select(Produto)).all() == []
    assert list(pasta_uploads.iterdir()) == []


def test_vaga_e_liberada_mesmo_com_erro():
    for _ in range(imagens.DECODIFICACOES_SIMULTANEAS + 2):
        imagens.processar_imagem(b"\x89PNG\r\n\x1a\n" + b"0" * 20)
    assert imagens._VAGAS.acquire(timeout=0.1)
    imagens._VAGAS.release()


def test_escrita_falha_nao_deixa_arquivo_nem_temporario(pasta_uploads, monkeypatch):
    def falha(*a, **k):
        raise OSError("disco cheio")

    monkeypatch.setattr(imagens.os, "replace", falha)
    with pytest.raises(OSError):
        imagens.salvar(PNG, "png")
    assert list(pasta_uploads.iterdir()) == []


def test_escrita_do_temporario_falha(pasta_uploads, monkeypatch):
    def falha(self, dados):
        self.touch()
        raise OSError("disco cheio")

    monkeypatch.setattr(imagens.Path, "write_bytes", falha)
    with pytest.raises(OSError):
        imagens.salvar(PNG, "png")
    assert list(pasta_uploads.iterdir()) == []


def test_pillow_so_recebe_bytes():
    import re
    fonte = open(imagens.__file__, encoding="utf-8").read()
    assert re.findall(r"Image\.open\((io\.BytesIO\(conteudo\))", fonte) == ["io.BytesIO(conteudo)"]
    assert fonte.count("Image.open(") == 1


def test_png_16_bits_em_cinza_preserva_os_niveis():
    """BUG-T0010-01: I;16 era gravado todo branco; agora e reescalado para 8 bits."""
    gradiente = (
        Image.linear_gradient("L").convert("I").point(lambda v: v * 257).convert("I;16")
    )
    buf = io.BytesIO()
    gradiente.save(buf, "PNG")
    with Image.open(io.BytesIO(buf.getvalue())) as entrada:
        assert entrada.mode == "I;16"
    ext, dados, erro = imagens.processar_imagem(buf.getvalue())
    assert erro is None and ext == "png"
    with Image.open(io.BytesIO(dados)) as saida:
        assert saida.mode == "L"
        assert saida.getpixel((0, 0)) == 0
        assert saida.getpixel((0, 255)) == 255
        assert saida.getpixel((0, 128)) == 128
        assert len(set(saida.get_flattened_data())) >= 250


def test_png_16_bits_valor_unico_nao_vira_branco():
    buf = io.BytesIO()
    Image.new("I;16", (4, 4), 30000).save(buf, "PNG")
    _, dados, erro = imagens.processar_imagem(buf.getvalue())
    assert erro is None
    with Image.open(io.BytesIO(dados)) as saida:
        assert saida.convert("L").getpixel((0, 0)) == 117
