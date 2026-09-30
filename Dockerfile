# Estagio "base": dependencias de execucao.
FROM python:3.13.15-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

# Estagio "dev": base + dependencias de teste. Usado so pelo servico "test" do Compose.
# tests/ entra por volume (o .dockerignore o deixa fora da imagem).
# A imagem so leva app/ e requirements.txt; nada de tests/ nem requirements-dev.txt.
FROM base AS dev
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Estagio final (padrao): imagem de execucao, sem tests/ e sem pytest/httpx.
FROM base AS runtime

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
