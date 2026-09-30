import pytest
from sqlalchemy import select

from app import imagens
from app.models import Produto

VALIDO = {"nome": "Caneta", "valor": "12,50", "fornecedor": "Papelaria X"}
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 50
JPG = b"\xff\xd8\xff\xe0" + b"0" * 50
WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"0" * 50


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
    assert (pasta_uploads / p.imagem_arquivo).read_bytes() == conteudo
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
    conteudo = PNG + b"0" * (imagens.TAMANHO_MAXIMO - len(PNG))
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
    assert list(pasta_uploads.iterdir()) == []


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
    assert r.content == PNG
    assert r.headers["content-type"] == "image/png"
    assert r.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("nome", ["..%2f..%2fetc%2fpasswd", "inexistente.png", "a" * 32 + ".png", "x.svg"])
def test_servico_de_arquivo_recusa_nomes_invalidos(client, nome):
    assert client.get(f"/uploads/{nome}").status_code == 404


def test_nome_do_produto_escapado_no_alt(client, sessao):
    enviar(client, PNG, nome='"><script>x</script>')
    assert "<script>x</script>" not in client.get("/").text
