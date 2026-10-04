import pytest

from app.config import statement_timeout_ms


@pytest.mark.parametrize(
    "valor,esperado",
    [
        (None, 5000),
        ("1500", 1500),
        ("2147483647", 2147483647),
        ("2147483648", 5000),
        ("99999999999", 5000),
        ("0", 5000),
        ("-1", 5000),
        ("abc", 5000),
    ],
)
def test_statement_timeout_ms(monkeypatch, valor, esperado):
    if valor is None:
        monkeypatch.delenv("DB_STATEMENT_TIMEOUT_MS", raising=False)
    else:
        monkeypatch.setenv("DB_STATEMENT_TIMEOUT_MS", valor)
    assert statement_timeout_ms() == esperado
