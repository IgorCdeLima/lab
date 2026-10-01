from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.datastructures import MutableHeaders

from app import db, imagens
from app.models import Produto
from app.validacao import validar_produto


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.criar_tabelas()
    yield


CABECALHOS_SEGURANCA = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self'; style-src 'self' 'unsafe-inline'; "
        "form-action 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'"
    ),
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


class CabecalhosSeguranca:
    """Middleware ASGI puro: define (substitui, nunca duplica) os cabeçalhos em toda resposta.

    Envolve o app inteiro (ver `AppComCabecalhos`): cobre 411/413 e o 500 do ServerErrorMiddleware.
    'unsafe-inline' só em style-src: o CSS está num <style> do template (RNF-08, T-0007).
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def enviar(msg):
            if msg["type"] == "http.response.start":
                msg.setdefault("headers", [])  # a chave é opcional no ASGI
                cab = MutableHeaders(scope=msg)
                for nome, valor in CABECALHOS_SEGURANCA.items():
                    cab[nome] = valor
            await send(msg)

        await self.app(scope, receive, enviar)


class AppComCabecalhos(FastAPI):
    """FastAPI cujo ponto de entrada ASGI é envolvido por `CabecalhosSeguranca`.

    `add_middleware` não basta: o `ServerErrorMiddleware` do Starlette fica por fora de todo
    middleware do usuário, e a resposta 500 dele sairia sem os cabeçalhos (SEC-0006).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._com_cabecalhos = CabecalhosSeguranca(super().__call__)

    async def __call__(self, scope, receive, send):
        await self._com_cabecalhos(scope, receive, send)


app = AppComCabecalhos(title="Cadastro de produtos", lifespan=lifespan)


LIMITE_REQUISICAO = 10 * 1024 * 1024  # teto anti-DoS, bem acima dos 2 MB da imagem


@app.middleware("http")
async def limitar_requisicao(request: Request, call_next):
    """Teto anti-DoS. Imagens de 2 a 10 MB passam e recebem 422 com mensagem na página.

    POST sem Content-Length (chunked) é recusado com 411: navegadores sempre enviam o cabeçalho.
    """
    if request.method == "POST":
        tamanho = request.headers.get("content-length", "")
        if not tamanho.isdigit():
            return JSONResponse(status_code=411, content={"erro": "Content-Length obrigatório."})
        if int(tamanho) > LIMITE_REQUISICAO:
            return JSONResponse(status_code=413, content={"erro": "Requisição grande demais."})
    return await call_next(request)


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
    imagem: Annotated[UploadFile | None, File()] = None,
):
    dados, erros = validar_produto(nome, valor, fornecedor)
    conteudo = b""
    ext = None
    if imagem is not None and imagem.filename:
        # lê no máximo 1 byte além do limite: nunca carrega arquivo gigante na memória
        conteudo = imagem.file.read(imagens.TAMANHO_MAXIMO + 1)
        if conteudo:
            ext, erro_img = imagens.validar_imagem(conteudo)
            if erro_img:
                erros["imagem"] = erro_img
    if erros:
        return _pagina(
            request,
            sessao,
            status_code=422,
            erros=erros,
            valores={"nome": nome, "valor": valor, "fornecedor": fornecedor},
        )
    arquivo = imagens.salvar(conteudo, ext) if ext else None
    try:
        sessao.add(Produto(**dados, imagem_arquivo=arquivo))
        sessao.commit()
    except Exception:
        if arquivo:
            imagens.remover(arquivo)
        raise
    return RedirectResponse("/", status_code=303)


@app.get("/uploads/{nome}")
def imagem_do_produto(nome: str):
    arquivo = imagens.caminho(nome)
    if arquivo is None:
        raise HTTPException(status_code=404)
    return FileResponse(
        arquivo,
        media_type=imagens.TIPOS[nome.rsplit(".", 1)[1]],
    )


@app.get("/health")
def health():
    if db.banco_ok():
        return {"status": "ok", "banco": "ok"}
    return JSONResponse(status_code=503, content={"status": "erro", "banco": "indisponivel"})
