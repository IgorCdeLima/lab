"""BUG-T0010-03: banco lento ou parado nao pode virar 500 nas paginas."""
import pytest
from sqlalchemy.exc import OperationalError

from app import imagens
from app.main import AVISO_BANCO

from .test_imagens import PNG, enviar


@pytest.fixture(autouse=True)
def uploads(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path))
    return tmp_path


def _banco_fora(*_args, **_kwargs):
    raise OperationalError("SELECT", {}, Exception("connection timeout expired"))


@pytest.fixture
def banco_fora(sessao, monkeypatch):
    monkeypatch.setattr(sessao, "scalars", _banco_fora)


def test_get_inicio_com_banco_fora_e_503_com_aviso(client, banco_fora):
    r = client.get("/")
    assert r.status_code == 503
    assert AVISO_BANCO in r.text
    assert "Traceback" not in r.text
    assert "Nenhum produto cadastrado" not in r.text


def test_422_continua_422_com_banco_fora(client, banco_fora):
    r = client.post("/produtos", data={"nome": "", "valor": "x", "fornecedor": ""})
    assert r.status_code == 422
    assert "Traceback" not in r.text
    assert AVISO_BANCO in r.text


def test_503_servidor_ocupado_continua_503_com_banco_fora(client, banco_fora, monkeypatch):
    def ocupado(_):
        raise imagens.ServidorOcupado

    monkeypatch.setattr(imagens, "processar_imagem", ocupado)
    r = enviar(client, PNG)
    assert r.status_code == 503
    assert imagens.ERRO_OCUPADO in r.text


def test_commit_com_banco_fora_vira_503_e_remove_arquivo(client, sessao, uploads, monkeypatch):
    monkeypatch.setattr(sessao, "commit", _banco_fora)
    r = enviar(client, PNG)
    assert r.status_code == 503
    assert AVISO_BANCO in r.text
    assert list(uploads.iterdir()) == []
