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


# SEC-T0015-03: consulta que passa do statement_timeout vira 503, nunca 500.


@pytest.fixture
def banco_travado(engine_teste, monkeypatch, uploads):
    """Outra conexao segura lock exclusivo em `produto`; app usa o engine real com timeout curto."""
    from sqlalchemy.orm import sessionmaker

    from app import db
    from app.main import app

    # engine real da aplicacao (com as opcoes de timeout), apontado para o banco de teste
    monkeypatch.setenv("DB_STATEMENT_TIMEOUT_MS", "500")
    monkeypatch.setenv("POSTGRES_DB", engine_teste.url.database)
    monkeypatch.setattr(db, "_engine", None)
    engine = db.get_engine()
    segura = engine_teste.connect()
    trans = segura.begin()
    segura.exec_driver_sql("LOCK TABLE produto IN ACCESS EXCLUSIVE MODE")

    def sessao_real():
        with sessionmaker(bind=engine, expire_on_commit=False)() as s:
            yield s

    app.dependency_overrides[db.get_session] = sessao_real
    yield
    app.dependency_overrides.clear()
    trans.rollback()
    segura.close()
    engine.dispose()


def test_statement_timeout_configurado_no_engine(engine_teste, monkeypatch):
    from app import db

    monkeypatch.setenv("POSTGRES_DB", engine_teste.url.database)
    monkeypatch.setattr(db, "_engine", None)
    try:
        with db.get_engine().connect() as conn:
            assert conn.exec_driver_sql("SHOW statement_timeout").scalar() == "5s"
    finally:
        db.get_engine().dispose()
        monkeypatch.setattr(db, "_engine", None)


def test_get_com_tabela_travada_e_503_com_aviso(banco_travado):
    from fastapi.testclient import TestClient

    from app.main import app

    r = TestClient(app).get("/")
    assert r.status_code == 503
    assert AVISO_BANCO in r.text


def test_post_com_tabela_travada_e_503_sem_arquivo_orfao(banco_travado, uploads):
    from fastapi.testclient import TestClient

    from app.main import app

    r = enviar(TestClient(app), PNG)
    assert r.status_code == 503
    assert AVISO_BANCO in r.text
    assert list(uploads.iterdir()) == []
