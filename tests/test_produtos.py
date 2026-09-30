from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.main import formatar_reais
from app.models import Produto
from app.validacao import interpretar_valor

VALIDO = {"nome": "Caneta", "valor": "12,50", "fornecedor": "Papelaria X"}


def post(client, **campos):
    return client.post("/produtos", data={**VALIDO, **campos}, follow_redirects=False)


def test_cadastro_valido(client, sessao):
    r = post(client)
    assert r.status_code == 303
    p = sessao.scalars(select(Produto)).one()
    assert (p.nome, p.valor, p.fornecedor) == ("Caneta", Decimal("12.50"), "Papelaria X")
    assert isinstance(p.valor, Decimal)


def test_nome_e_fornecedor_sem_espacos_nas_pontas(client, sessao):
    post(client, nome="  Caneta  ", fornecedor="  Fornec  ")
    p = sessao.scalars(select(Produto)).one()
    assert (p.nome, p.fornecedor) == ("Caneta", "Fornec")


@pytest.mark.parametrize("campo", ["nome", "valor", "fornecedor"])
@pytest.mark.parametrize("vazio", ["", "   "])
def test_campos_obrigatorios(client, sessao, campo, vazio):
    r = post(client, **{campo: vazio})
    assert r.status_code == 422
    assert "Informe" in r.text
    assert sessao.scalars(select(Produto)).all() == []


@pytest.mark.parametrize("campo", ["nome", "fornecedor"])
def test_limite_120_caracteres(client, sessao, campo):
    assert post(client, **{campo: "a" * 120}).status_code == 303
    r = post(client, **{campo: "a" * 121})
    assert r.status_code == 422
    assert "120 caracteres" in r.text
    assert len(sessao.scalars(select(Produto)).all()) == 1


@pytest.mark.parametrize(
    "valor",
    ["0", "0,00", "-5", "abc", "1,234", "10,5,5", "1e3", "100000000,00", "99999999,99x",
     "1.2345", "1.234.56", "12.345,678", "1.23.4",
     "1" * 27, "1" * 30, "1" * 200],
)
def test_valor_invalido(client, sessao, valor):
    r = post(client, valor=valor)
    assert r.status_code == 422
    assert sessao.scalars(select(Produto)).all() == []


def test_valor_maximo_aceito(client, sessao):
    assert post(client, valor="99.999.999,99").status_code == 303
    assert sessao.scalars(select(Produto)).one().valor == Decimal("99999999.99")


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("1234,56", "1234.56"),
        ("1.234,56", "1234.56"),
        ("12", "12.00"),
        ("12,5", "12.50"),
        ("12.5", "12.50"),
        ("1.234", "1234.00"),
        ("1.000", "1000.00"),
        ("12.345", "12345.00"),
        ("1.005", "1005.00"),
        ("1.234.567", "1234567.00"),
    ],
)
def test_interpretar_valor(texto, esperado):
    assert interpretar_valor(texto) == Decimal(esperado)


@pytest.mark.parametrize("campo", ["nome", "fornecedor"])
@pytest.mark.parametrize("texto", ["a\x00b", "a\x01b", "a\x7fb"])
def test_caracteres_de_controle_recusados(client, sessao, campo, texto):
    r = post(client, **{campo: texto})
    assert r.status_code == 422
    assert "caracteres inválidos" in r.text
    assert sessao.scalars(select(Produto)).all() == []


def test_valor_com_milhar_sem_virgula_grava_milhar(client, sessao):
    assert post(client, valor="1.234").status_code == 303
    assert sessao.scalars(select(Produto)).one().valor == Decimal("1234.00")


def test_erro_preserva_valores_digitados(client):
    r = post(client, nome="Meu produto", valor="abc", fornecedor="Forn")
    assert 'value="Meu produto"' in r.text
    assert 'value="abc"' in r.text
    assert 'value="Forn"' in r.text
    assert "Valor inválido" in r.text


def test_listagem_ordena_por_criado_em(client, sessao):
    # horários explícitos; ids em ordem contrária à data provam que não é só o id
    base = datetime(2026, 1, 1, tzinfo=UTC)
    for nome, dias in [("Meio", 1), ("Novo", 2), ("Antigo", 0)]:
        sessao.add(Produto(nome=nome, valor=Decimal("1.00"), fornecedor="F",
                           criado_em=base + timedelta(days=dias)))
    sessao.flush()
    html = client.get("/").text
    assert html.index("Novo") < html.index("Meio") < html.index("Antigo")


def test_listagem_do_mais_recente_para_o_mais_antigo(client):
    for nome in ["Primeiro", "Segundo", "Terceiro"]:
        post(client, nome=nome)
    html = client.get("/").text
    assert html.index("Terceiro") < html.index("Segundo") < html.index("Primeiro")


def test_valor_formatado_em_reais(client):
    post(client, valor="1234,56")
    assert "R$ 1.234,56" in client.get("/").text


def test_formatar_reais():
    assert formatar_reais(Decimal("0.5")) == "R$ 0,50"
    assert formatar_reais(Decimal("99999999.99")) == "R$ 99.999.999,99"


def test_html_escapado(client):
    post(client, nome="<script>alert(1)</script>", fornecedor='"><b>x</b>')
    html = client.get("/").text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    r = post(client, valor="abc", nome="<img src=x>")
    assert "<img src=x>" not in r.text


def test_lista_vazia(client):
    assert "Nenhum produto cadastrado" in client.get("/").text
