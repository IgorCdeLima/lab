"""Acesso ao PostgreSQL via SQLAlchemy."""

from functools import lru_cache

from sqlalchemy import URL, Engine, create_engine, text

from app.config import obter_config

# Evita que a verificação de saúde fique presa se o banco não responder.
TEMPO_LIMITE_CONEXAO_S = 3


def criar_engine(url: URL) -> Engine:
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": TEMPO_LIMITE_CONEXAO_S},
    )


@lru_cache
def obter_engine() -> Engine:
    return criar_engine(obter_config().url_banco())


def banco_responde(engine: Engine) -> bool:
    """Executa uma consulta trivial; True se o banco respondeu."""
    with engine.connect() as conexao:
        return conexao.execute(text("SELECT 1")).scalar_one() == 1
