"""Aplicação web do projeto lab."""

import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.db import banco_responde, obter_engine

logger = logging.getLogger(__name__)

app = FastAPI(title="lab — cadastro de produtos")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/health")
def saude(engine: Annotated[Engine, Depends(obter_engine)]) -> JSONResponse:
    try:
        ok = banco_responde(engine)
    except SQLAlchemyError:
        logger.warning("Verificação de saúde: banco indisponível", exc_info=True)
        ok = False
    if not ok:
        return JSONResponse(status_code=503, content={"status": "erro", "banco": "indisponivel"})
    return JSONResponse(content={"status": "ok", "banco": "ok"})


@app.get("/", response_class=HTMLResponse)
def pagina_inicial(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"titulo": "Cadastro de produtos"})
