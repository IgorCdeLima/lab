import os

from sqlalchemy.engine import URL


def database_url() -> str:
    """Monta a URL do banco a partir de variáveis de ambiente."""
    usuario = os.environ.get("POSTGRES_USER", "lab")
    senha = os.environ.get("POSTGRES_PASSWORD", "lab_dev_local")  # padrão só p/ dev local
    host = os.environ.get("POSTGRES_HOST", "db")
    porta = os.environ.get("POSTGRES_PORT", "5432")
    banco = os.environ.get("POSTGRES_DB", "lab")
    return URL.create(
        "postgresql+psycopg",
        username=usuario,
        password=senha,
        host=host,
        port=int(porta),
        database=banco,
    ).render_as_string(hide_password=False)


def statement_timeout_ms() -> int:
    """Tempo maximo de uma consulta, em ms (SEC-T0015-03). Padrao 5000; nao e segredo."""
    try:
        valor = int(os.environ.get("DB_STATEMENT_TIMEOUT_MS", "5000"))
    except ValueError:
        return 5000
    return valor if valor > 0 else 5000


def uploads_dir() -> str:
    """Pasta (volume) onde as imagens enviadas são salvas."""
    return os.environ.get("UPLOADS_DIR", "/uploads")
