"""Aplicação web do projeto lab."""

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError

from app.config import ConfiguracaoIncompleta
from app.db import banco_responde, obter_engine

logger = logging.getLogger(__name__)

app = FastAPI(title="lab — cadastro de produtos")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/health")
def saude() -> JSONResponse:
    # O engine é obtido dentro do try: configuração incompleta também é "banco indisponível".
    try:
        ok = banco_responde(obter_engine())
    except (SQLAlchemyError, ConfiguracaoIncompleta):
        logger.warning("Verificação de saúde: banco indisponível", exc_info=True)
        ok = False
    if not ok:
        return JSONResponse(status_code=503, content={"status": "erro", "banco": "indisponivel"})
    return JSONResponse(content={"status": "ok", "banco": "ok"})


@app.get("/", response_class=HTMLResponse)
def pagina_inicial(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"titulo": "Cadastro de produtos"})
