from sqlalchemy import URL

from app.db import criar_engine, obter_engine
from app.main import app


def test_saude_ok_com_banco_disponivel(cliente):
    resposta = cliente.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


def test_saude_503_com_banco_indisponivel(cliente):
    # Porta sem nenhum serviço escutando: a conexão falha de verdade.
    url_invalida = URL.create(
        "postgresql+psycopg", username="x", password="x", host="127.0.0.1", port=1, database="x"
    )
    engine_indisponivel = criar_engine(url_invalida)
    app.dependency_overrides[obter_engine] = lambda: engine_indisponivel

    resposta = cliente.get("/health")

    assert resposta.status_code == 503
    assert resposta.json()["status"] == "erro"
    assert resposta.json()["banco"] == "indisponivel"
