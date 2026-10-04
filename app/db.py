from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import database_url, statement_timeout_ms

_engine: Engine | None = None


class Base(DeclarativeBase):
    pass


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(
            database_url(),
            pool_pre_ping=True,
            connect_args={
                "connect_timeout": 3,
                "options": f"-c statement_timeout={statement_timeout_ms()}",
            },
        )
    return _engine


def get_session() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão por requisição (sobrescrita nos testes)."""
    with sessionmaker(bind=get_engine(), expire_on_commit=False)() as sessao:
        yield sessao


def criar_tabelas() -> None:
    from app import models  # noqa: F401  (registra as tabelas no metadata)

    Base.metadata.create_all(get_engine())
    # create_all não altera tabela existente: bancos criados na T-0002 ganham a coluna nova.
    with get_engine().begin() as conn:
        conn.execute(text("ALTER TABLE produto ADD COLUMN IF NOT EXISTS imagem_arquivo VARCHAR(64)"))


def imagem_referenciada(arquivo: str) -> bool | None:
    """Em conexao nova: True/False se alguma linha usa o arquivo; None se nao deu para conferir."""
    try:
        with get_engine().connect() as conn:
            return conn.execute(
                text("SELECT 1 FROM produto WHERE imagem_arquivo = :a LIMIT 1"), {"a": arquivo}
            ).first() is not None
    except Exception:
        return None


def banco_ok() -> bool:
    """True se o banco responde a uma consulta simples."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
