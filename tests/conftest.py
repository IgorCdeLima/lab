"""Testes usam um banco separado (`<POSTGRES_DB>_test`), nunca o da aplicação."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.config import database_url
from app.db import Base, get_session
from app.main import app


@pytest.fixture(scope="session")
def engine_teste():
    url_admin = make_url(database_url())
    nome = url_admin.database + "_test"
    admin = create_engine(url_admin, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        existe = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": nome}
        ).scalar()
        if not existe:
            conn.execute(text(f'CREATE DATABASE "{nome}"'))
    admin.dispose()
    engine = create_engine(url_admin.set(database=nome))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def sessao(engine_teste):
    """Sessão dentro de uma transação externa, revertida ao fim de cada teste."""
    conn = engine_teste.connect()
    trans = conn.begin()
    s = sessionmaker(
        bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
    )()
    yield s
    s.close()
    trans.rollback()
    conn.close()


@pytest.fixture
def client(sessao):
    app.dependency_overrides[get_session] = lambda: sessao
    # sem `with`: o lifespan (create_all no banco da aplicação) não roda nos testes
    yield TestClient(app)
    app.dependency_overrides.clear()
