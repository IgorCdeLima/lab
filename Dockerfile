# Estagio "base": dependencias de execucao, instaladas so com versao exata e hash
# (requirements.txt e gerado por "docker compose run --rm lock"; ver ADR-0003).
FROM python:3.13.15-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt
COPY app ./app

# Estagio "dev": base + ferramentas de desenvolvimento (pytest, ruff, pip-audit).
# Usado pelos servicos "test", "lint" e "audit" do Compose.
# Leva app/, requirements.txt e requirements-dev.txt; tests/ entra por volume
# (o .dockerignore o deixa fora da imagem).
FROM base AS dev
COPY requirements-dev.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements-dev.txt

# Estagio "lock": so para gerar os requirements travados (servico "lock" do Compose).
# Mesma imagem Python da aplicacao, com pip e pip-tools em versao fixa.
# Nao entra em "dev" nem em "runtime": o pip-tools nunca chega a essas imagens.
FROM python:3.13.15-slim AS lock
RUN pip install --no-cache-dir pip==26.2.1 pip-tools==7.6.1
WORKDIR /work

# Estagio final (padrao): imagem de execucao. So leva app/ e requirements.txt:
# nada de tests/, requirements-dev.txt, pytest, ruff, pip-audit nem pip-tools.
FROM base AS runtime

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
