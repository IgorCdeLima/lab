import pytest
from sqlalchemy import select

from app.main import CABECALHOS_SEGURANCA
from app.models import Produto
from tests.test_imagens import PNG, VALIDO, enviar  # noqa: F401 (pasta_uploads é autouse lá)

CSP = (
    "default-src 'self'; img-src 'self'; style-src 'self' 'unsafe-inline'; "
    "form-action 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'"
)


def conferir(r):
    assert r.headers["content-security-policy"] == CSP
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    for nome in CABECALHOS_SEGURANCA:  # nenhum duplicado
        assert len(r.headers.get_list(nome)) == 1


@pytest.fixture(autouse=True)
def _uploads(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path))


def test_get_inicio(client):
    r = client.get("/")
    assert r.status_code == 200
    conferir(r)


def test_post_invalido_422(client):
    r = client.post("/produtos", data={}, follow_redirects=False)
    assert r.status_code == 422
    conferir(r)


def test_post_valido_303(client):
    r = client.post("/produtos", data=VALIDO, follow_redirects=False)
    assert r.status_code == 303
    conferir(r)


def test_411_sem_content_length(client):
    def corpo():
        yield b"nome=x"

    r = client.post("/produtos", content=corpo(),
                    headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 411
    conferir(r)


def test_413_acima_do_teto(client):
    r = client.post("/produtos", content=b"x", headers={"content-length": str(11 * 1024 * 1024)})
    assert r.status_code == 413
    conferir(r)


def test_uploads_200(client, sessao):
    enviar(client, PNG)
    nome = sessao.scalars(select(Produto)).one().imagem_arquivo
    r = client.get(f"/uploads/{nome}")
    assert r.status_code == 200
    conferir(r)


def test_uploads_404(client):
    r = client.get("/uploads/x.svg")
    assert r.status_code == 404
    conferir(r)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    conferir(r)
