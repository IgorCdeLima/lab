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
