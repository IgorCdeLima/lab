# Estagio "base": dependencias de execucao, instaladas so com versao exata e hash
# (requirements.txt e gerado por "docker compose run --build --rm lock"; ver ADR-0003).
FROM python:3.13.15-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Pacotes do sistema: a tag 3.13.15-slim (a mais nova em 2026-10-01) ainda traz openssl
# e libpcre2 com correcao pendente (SEC-0002). O upgrade aplica as correcoes de seguranca
# do Debian; as listas do apt sao removidas para nao engordar a imagem.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

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
# --force-reinstall: sem ele o pip ja presente na base nao e baixado e seu hash nao e conferido (SEC-T0014-01).
RUN pip install --no-cache-dir --require-hashes --force-reinstall -r requirements-dev.txt

# Estagio "lock": so para gerar os requirements travados (servico "lock" do Compose).
# Mesma imagem Python da aplicacao. A ferramenta que gera os hashes tambem e instalada
# com versao exata e hash (requirements-lock.txt, gerado por este mesmo servico; SEC-0007).
# Nao entra em "dev" nem em "runtime": o pip-tools nunca chega a essas imagens.
# O usuario (sem root) e definido no servico "lock" do Compose.
FROM python:3.13.15-slim AS lock
WORKDIR /work
COPY requirements-lock.txt .
# --force-reinstall: ver SEC-T0014-01 (confere o hash do pip que ja vem na base).
RUN pip install --no-cache-dir --require-hashes --force-reinstall -r requirements-lock.txt

# Estagio final (padrao): imagem de execucao. So leva app/ e requirements.txt:
# nada de tests/, requirements-dev.txt, pytest, ruff, pip-audit nem pip-tools.
FROM base AS runtime

# Usuario sem privilegio (SEC-0004, RNF-07). /uploads e criada com a posse dele: volume
# NOVO herda essa posse; volume ANTIGO (arquivos de root) precisa do ajuste do README.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
    && mkdir /uploads \
    && chown app:app /uploads
USER 10001:10001

# SEC-T0010-03: cada thread do threadpool ganha uma arena do malloc e a memoria que o Pillow
# libera fica retida nela; o pico subia a cada rodada de WebP de 50 MP ate o OOM. Duas arenas
# estabilizam o pico (medido pela Seguranca: 1751 MiB em 14 rodadas, sem OOM).
ENV MALLOC_ARENA_MAX=2

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
