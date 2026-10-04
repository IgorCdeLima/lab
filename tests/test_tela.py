"""T-0013: tela de cadastro (estrutura, estados, acessibilidade) e rota /static."""
import re
from pathlib import Path

import pytest

from app import imagens
from app.main import AVISO_BANCO

from .test_cabecalhos import CSP, conferir
from .test_imagens import PNG, enviar
from .test_produtos import post

RAIZ = Path(__file__).resolve().parents[1]
ESTATICOS = RAIZ / "app" / "static"


@pytest.fixture(autouse=True)
def _uploads(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path))


def _sem_estilo_nem_script_inline(html):
    assert not re.search(r"<style", html, re.I)
    assert not re.search(r"\sstyle\s*=", html, re.I)
    assert not re.search(r"\son[a-z]+\s*=", html, re.I)
    for tag in re.findall(r"<script\b[^>]*>", html, re.I):
        assert "src=" in tag, tag
    assert not re.search(r"<script\b[^>]*>(?!\s*</script>)", html, re.I)


# --- estrutura e estados -----------------------------------------------------------------


def test_html_sem_style_nem_script_inline_em_todos_os_estados(client, sessao, monkeypatch):
    post(client)
    paginas = [client.get("/").text, post(client, nome="").text]
    r = client.post("/produtos", data={"nome": "x", "valor": "1", "fornecedor": "y"},
                    files={"imagem": ("a.png", b"nao e imagem", "image/png")})
    paginas.append(r.text)
    for html in paginas:
        _sem_estilo_nem_script_inline(html)


def test_assets_ligados_na_ordem(client):
    html = client.get("/").text
    i1 = html.index('href="/static/tokens.css"')
    i2 = html.index('href="/static/cadastro.css"')
    i3 = html.index('<script src="/static/carrossel.js" defer>')
    assert i1 < i2 < i3
    assert "https://" not in html and "http://" not in html


def test_csp_sem_unsafe_inline(client):
    csp = client.get("/").headers["content-security-policy"]
    assert csp == CSP
    assert "unsafe-inline" not in csp
    assert "style-src 'self';" in csp and "script-src 'self';" in csp


def test_estado_vazio(client):
    html = client.get("/").text
    assert "Nenhum produto cadastrado." in html
    assert "cabecalho__contagem" not in html
    assert "data-carrossel" not in html


def test_contagem_singular_e_plural(client):
    post(client)
    assert re.search(r'cabecalho__contagem">1 produto<', client.get("/").text)
    post(client, nome="Outro")
    assert re.search(r'cabecalho__contagem">2 produtos<', client.get("/").text)


def test_carrossel_mais_recente_primeiro_e_sem_destaque(client):
    for nome in ("Primeiro", "Segundo", "Terceiro"):
        assert post(client, nome=nome).status_code == 303
    html = client.get("/").text
    assert html.index("Terceiro") < html.index("Segundo") < html.index("Primeiro")
    assert 'id="carrossel"' in html and 'aria-controls="carrossel"' in html
    assert "carrossel-nav" in html and "hidden" in html


def test_produto_sem_imagem_e_com_imagem(client, sessao):
    post(client, nome="SemFoto")
    assert "cartao__foto--vazia" in client.get("/").text
    enviar(client, PNG)
    html = client.get("/").text
    assert 'src="/uploads/' in html and 'alt="Imagem de ' in html


def test_cartao_com_limites_no_dom(client):
    longo = "a" * 120
    post(client, nome=longo, fornecedor=longo, valor="99.999.999,99")
    html = client.get("/").text
    assert longo in html and f'title="{longo}"' in html
    assert "R$ 99.999.999,99" in html


# --- erros: acessibilidade ---------------------------------------------------------------


def test_erro_em_cada_campo_tem_aria_e_texto_literal(client):
    r = client.post("/produtos", data={"nome": "", "valor": "x", "fornecedor": ""})
    html = r.text
    assert r.status_code == 422
    for campo, texto in [
        ("nome", "Informe o nome."),
        ("valor", "Valor inválido. Use o formato 1234,56 (até duas casas decimais)."),
        ("fornecedor", "Informe o fornecedor."),
    ]:
        assert re.search(rf'<input id="{campo}"[^>]*aria-invalid="true"', html)
        assert re.search(rf'<input id="{campo}"[^>]*aria-describedby="{campo}-erro', html)
        assert f'class="msg-erro" id="{campo}-erro"' in html
        assert f'<a href="#{campo}">' in html and texto in html
    assert 'role="alert"' in html
    assert "Corrija os campos marcados para cadastrar." in html


def test_autofocus_so_no_primeiro_campo_com_erro(client):
    html = client.post("/produtos", data={"nome": "ok", "valor": "x", "fornecedor": ""}).text
    assert html.count("autofocus") == 1
    assert re.search(r'<input id="valor"[^>]*autofocus', html)
    html = client.post("/produtos", data={"nome": "", "valor": "x", "fornecedor": ""}).text
    assert html.count("autofocus") == 1 and re.search(r'<input id="nome"[^>]*autofocus', html)


def test_valores_preservados_e_dica_de_reenvio(client):
    html = client.post("/produtos", data={"nome": "Caneta", "valor": "4799,999", "fornecedor": "F"}).text
    assert 'value="Caneta"' in html and 'value="4799,999"' in html
    assert "Se você tinha escolhido uma imagem, escolha de novo." in html
    assert "imagem-reenvio" in html


def test_sem_erro_nao_mostra_dica_de_reenvio(client):
    assert "escolha de novo" not in client.get("/").text


def test_fornecedor_de_109_caracteres_nao_da_erro_de_120(client):
    r = post(client, fornecedor="f" * 109)
    assert r.status_code == 303


def test_erro_de_imagem_estado_4(client):
    r = client.post("/produtos", data={"nome": "x", "valor": "1", "fornecedor": "y"},
                    files={"imagem": ("a.png", b"nao e imagem", "image/png")})
    html = r.text
    assert r.status_code == 422
    assert "campo-arquivo--erro" in html
    assert re.search(r'<input id="imagem"[^>]*aria-invalid="true"[^>]*aria-describedby="imagem-erro', html)
    assert "Escolha outro arquivo, ou cadastre sem imagem. JPEG, PNG ou WebP, até 2 MB." in html
    assert 'href="#imagem"' in html
    assert "escolha de novo" not in html  # a dica de reenvio so vale com a imagem sem erro


def test_servidor_ocupado_estado_5(client, monkeypatch):
    def ocupado(_):
        raise imagens.ServidorOcupado

    monkeypatch.setattr(imagens, "processar_imagem", ocupado)
    r = enviar(client, PNG)
    html = r.text
    assert r.status_code == 503
    assert imagens.ERRO_OCUPADO in html and "campo-arquivo--erro" in html
    assert "Escolha a mesma imagem de novo e envie em instantes, ou cadastre sem imagem." in html
    assert "Escolha outro arquivo" not in html


# --- banco fora ---------------------------------------------------------------------------


def _fora(*_a, **_k):
    from sqlalchemy.exc import OperationalError

    raise OperationalError("SELECT", {}, Exception("fora"))


def test_get_com_banco_fora_estado_6(client, sessao, monkeypatch):
    monkeypatch.setattr(sessao, "scalars", _fora)
    r = client.get("/")
    html = r.text
    assert r.status_code == 503
    assert re.search(r'<div class="aviso" role="alert">', html) and AVISO_BANCO in html
    assert "Lista indisponível no momento." in html
    assert "Nenhum produto cadastrado." not in html
    assert "cabecalho__contagem" not in html and "data-carrossel" not in html
    _sem_estilo_nem_script_inline(html)


def test_post_com_banco_fora_estado_7_um_so_alerta(client, sessao, monkeypatch):
    monkeypatch.setattr(sessao, "commit", _fora)
    monkeypatch.setattr(sessao, "scalars", _fora)
    r = client.post("/produtos", data={"nome": "N", "valor": "1", "fornecedor": "F"})
    html = r.text
    assert r.status_code == 503
    assert "Não foi possível cadastrar." in html and "Os dados digitados foram mantidos." in html
    assert html.count(AVISO_BANCO) == 1  # no resumo; sem o aviso do topo
    assert html.count('role="alert"') == 1
    assert "aria-invalid" not in html and "autofocus" not in html
    assert 'value="N"' in html and "Lista indisponível no momento." in html
    assert "Nenhum produto cadastrado." not in html


def test_422_com_lista_falhando_mostra_aviso_e_resumo(client, sessao, monkeypatch):
    monkeypatch.setattr(sessao, "scalars", _fora)
    html = client.post("/produtos", data={"nome": "", "valor": "1", "fornecedor": "F"}).text
    assert 'class="aviso"' in html and "Corrija os campos marcados" in html
    assert "Lista indisponível no momento." in html


# --- /static ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "arquivo,tipo",
    [("tokens.css", "text/css"), ("cadastro.css", "text/css"), ("carrossel.js", "text/javascript")],
)
def test_static_servido_com_cabecalhos(client, arquivo, tipo):
    r = client.get(f"/static/{arquivo}")
    assert r.status_code == 200
    assert r.headers["content-type"].split(";")[0] == tipo
    assert r.headers["x-content-type-options"] == "nosniff"
    conferir(r)


@pytest.mark.parametrize(
    "caminho",
    [
        "/static/", "/static", "/static/../app/main.py", "/static/%2e%2e/app/main.py",
        "/static/..%2fapp%2fmain.py", "/static/%2e%2e%2fapp%2fmain.py", "/static/nao-existe.css",
        "/static/../static/tokens.css/../../main.py",
    ],
)
def test_static_nao_lista_nem_sai_da_pasta(client, caminho):
    r = client.get(caminho, follow_redirects=False)
    assert r.status_code in (404, 307)
    assert "import" not in r.text and "FastAPI" not in r.text
    if r.status_code == 307:  # /static -> /static/ (redirect do Starlette); o destino e 404
        assert client.get(r.headers["location"]).status_code == 404


def test_pasta_estatica_so_tem_os_3_arquivos():
    assert sorted(p.name for p in ESTATICOS.iterdir()) == [
        "cadastro.css", "carrossel.js", "tokens.css",
    ]


def test_tokens_identico_ao_do_design():
    origem = RAIZ / "docs" / "design" / "sistema" / "tokens.css"
    if not origem.exists():  # a imagem de teste nao leva docs/
        pytest.skip("docs/ fora do container de teste")
    assert (ESTATICOS / "tokens.css").read_bytes() == origem.read_bytes()


def test_estaticos_sem_recurso_externo():
    for arq in ESTATICOS.iterdir():
        texto = arq.read_text(encoding="utf-8")
        assert not re.search(r"https?://|@import", texto), arq.name
