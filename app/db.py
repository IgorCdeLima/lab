from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import database_url

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            database_url(), pool_pre_ping=True, connect_args={"connect_timeout": 3}
        )
    return _engine


def banco_ok() -> bool:
    """True se o banco responde a uma consulta simples."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
