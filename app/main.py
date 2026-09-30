from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import db
from app.models import Produto
from app.validacao import validar_produto


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.criar_tabelas()
    yield


app = FastAPI(title="Cadastro de produtos", lifespan=lifespan)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def formatar_reais(valor: Decimal) -> str:
    """Decimal -> 'R$ 1.234,56'."""
    s = f"{valor:,.2f}"  # 1,234.56
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


templates.env.filters["reais"] = formatar_reais


def _pagina(request: Request, sessao: Session, status_code=200, erros=None, valores=None):
    produtos = sessao.scalars(
        select(Produto).order_by(Produto.criado_em.desc(), Produto.id.desc())
    ).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"produtos": produtos, "erros": erros or {}, "valores": valores or {}},
        status_code=status_code,
    )


@app.get("/", response_class=HTMLResponse)
def inicio(request: Request, sessao: Annotated[Session, Depends(db.get_session)]):
    return _pagina(request, sessao)


@app.post("/produtos")
def cadastrar(
    request: Request,
    sessao: Annotated[Session, Depends(db.get_session)],
    nome: Annotated[str, Form()] = "",
    valor: Annotated[str, Form()] = "",
    fornecedor: Annotated[str, Form()] = "",
):
    dados, erros = validar_produto(nome, valor, fornecedor)
    if erros:
        return _pagina(
            request,
            sessao,
            status_code=422,
            erros=erros,
            valores={"nome": nome, "valor": valor, "fornecedor": fornecedor},
        )
    sessao.add(Produto(**dados))
    sessao.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health():
    if db.banco_ok():
        return {"status": "ok", "banco": "ok"}
    return JSONResponse(status_code=503, content={"status": "erro", "banco": "indisponivel"})
