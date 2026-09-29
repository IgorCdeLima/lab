"""Configuração da aplicação, lida de variáveis de ambiente (ver .env.example)."""

import os
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy import URL


class ConfiguracaoIncompleta(RuntimeError):
    """Falta uma variável de ambiente obrigatória."""


@dataclass(frozen=True)
class Config:
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str
    postgres_port: int

    def url_banco(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


def _obrigatoria(nome: str) -> str:
    valor = os.environ.get(nome)
    if not valor:
        raise ConfiguracaoIncompleta(f"Variável de ambiente obrigatória não definida: {nome}")
    return valor


@lru_cache
def obter_config() -> Config:
    return Config(
        postgres_user=_obrigatoria("POSTGRES_USER"),
        postgres_password=_obrigatoria("POSTGRES_PASSWORD"),
        postgres_db=_obrigatoria("POSTGRES_DB"),
        postgres_host=os.environ.get("POSTGRES_HOST", "db"),
        postgres_port=int(os.environ.get("POSTGRES_PORT", "5432")),
    )
