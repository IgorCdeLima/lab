# Estagio "base": dependencias de execucao.
FROM python:3.13.15-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

# Estagio "dev": base + ferramentas de desenvolvimento (pytest, ruff, pip-audit).
# Usado pelos servicos "test", "lint" e "audit" do Compose.
# Leva app/, requirements.txt e requirements-dev.txt; tests/ entra por volume
# (o .dockerignore o deixa fora da imagem).
FROM base AS dev
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Estagio final (padrao): imagem de execucao. So leva app/ e requirements.txt:
# nada de tests/, requirements-dev.txt, pytest, ruff nem pip-audit.
FROM base AS runtime

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
