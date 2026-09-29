from fastapi.testclient import TestClient

from app import db
from app.main import app

client = TestClient(app)


def test_saude_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "banco": "ok"}


def test_saude_com_banco_indisponivel(monkeypatch):
    monkeypatch.setenv("POSTGRES_HOST", "host-inexistente.invalid")
    monkeypatch.setattr(db, "_engine", None)  # força novo engine com o host inválido
    try:
        r = client.get("/health")
    finally:
        db._engine = None
    assert r.status_code == 503
    assert r.json()["banco"] != "ok"


def test_pagina_inicial():
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "<title>Cadastro de produtos</title>" in r.text
