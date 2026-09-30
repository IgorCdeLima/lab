import re
from decimal import Decimal

VALOR_MAXIMO = Decimal("99999999.99")
# 1234,56 | 1.234,56 | 1234 | 1234.56 (ponto decimal só sem vírgula e com 1-2 casas)
_PADROES = (
    re.compile(r"\d+(,\d{1,2})?"),
    re.compile(r"\d{1,3}(\.\d{3})+(,\d{1,2})?"),
    re.compile(r"\d+\.\d{1,2}"),
)


def interpretar_valor(texto: str) -> Decimal | None:
    """Converte texto em Decimal (nunca float); None se o formato for inválido."""
    texto = texto.strip()
    if not any(p.fullmatch(texto) for p in _PADROES):
        return None
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return Decimal(texto).quantize(Decimal("0.01"))


def validar_produto(nome: str, valor: str, fornecedor: str):
    """Retorna (dados, erros). `dados` só é útil quando `erros` está vazio."""
    erros: dict[str, str] = {}
    nome = nome.strip()
    fornecedor = fornecedor.strip()

    if not nome:
        erros["nome"] = "Informe o nome."
    elif len(nome) > 120:
        erros["nome"] = "O nome deve ter no máximo 120 caracteres."

    if not fornecedor:
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
