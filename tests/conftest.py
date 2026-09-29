import pytest
from fastapi.testclient import TestClient

from app.config import obter_config
from app.db import obter_engine
from app.main import app


def _limpar_caches():
    obter_engine.cache_clear()
    obter_config.cache_clear()


@pytest.fixture
def cliente():
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture
def ambiente(monkeypatch):
    """Permite alterar variáveis de ambiente; config e engine são recriados com elas."""
    _limpar_caches()
    yield monkeypatch
    monkeypatch.undo()
    _limpar_caches()
