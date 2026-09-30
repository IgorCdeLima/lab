import re
from decimal import Decimal

VALOR_MAXIMO = Decimal("99999999.99")
# Regra do valor (pt-BR): vírgula é o separador decimal e ponto é milhar.
#   1234 | 1234,56 | 1.234 | 1.234,56 | 1.234.567 -> ponto = milhar (grupos de 3 dígitos)
#   1234.56 | 12.5 -> ponto decimal só sem vírgula e com 1-2 casas
# Assim "1.234" é mil duzentos e trinta e quatro (nunca 1,23). Mais de 2 casas é erro (sem arredondar).
_MILHAR = re.compile(r"(\d+|\d{1,3}(\.\d{3})+)(,\d{1,2})?")
_PONTO_DECIMAL = re.compile(r"\d+\.\d{1,2}")
_CONTROLE = re.compile(r"[\x00-\x1f\x7f]")  # PostgreSQL não guarda NUL; controles não fazem sentido


def interpretar_valor(texto: str) -> Decimal | None:
    """Converte texto em Decimal (nunca float); None se o formato for inválido."""
    texto = texto.strip()
    if _MILHAR.fullmatch(texto):
        normal = texto.replace(".", "").replace(",", ".")
    elif _PONTO_DECIMAL.fullmatch(texto):
        normal = texto
    else:
        return None
    return Decimal(normal).quantize(Decimal("0.01"))


def validar_produto(nome: str, valor: str, fornecedor: str):
    """Retorna (dados, erros). `dados` só é útil quando `erros` está vazio."""
    erros: dict[str, str] = {}
    nome = nome.strip()
    fornecedor = fornecedor.strip()

    if _CONTROLE.search(nome):
        erros["nome"] = "O nome contém caracteres inválidos."
    elif not nome:
        erros["nome"] = "Informe o nome."
    elif len(nome) > 120:
        erros["nome"] = "O nome deve ter no máximo 120 caracteres."

    if _CONTROLE.search(fornecedor):
        erros["fornecedor"] = "O fornecedor contém caracteres inválidos."
    elif not fornecedor:
        erros["fornecedor"] = "Informe o fornecedor."
    elif len(fornecedor) > 120:
        erros["fornecedor"] = "O fornecedor deve ter no máximo 120 caracteres."

    numero = None
    if not valor.strip():
        erros["valor"] = "Informe o valor."
    else:
        numero = interpretar_valor(valor)
        if numero is None:
            erros["valor"] = "Valor inválido. Use o formato 1234,56 (até duas casas decimais)."
        elif numero <= 0:
            erros["valor"] = "O valor deve ser maior que zero."
        elif numero > VALOR_MAXIMO:
            erros["valor"] = "O valor máximo é R$ 99.999.999,99."

    return {"nome": nome, "valor": numero, "fornecedor": fornecedor}, erros
