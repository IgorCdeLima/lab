# lab — cadastro de produtos

Landing page simples para cadastrar produtos com nome, valor, fornecedor e imagem.

Projeto laboratório da equipe de agentes 01_IA. Padrões em [CLAUDE.md](CLAUDE.md); requisitos em [docs/requisitos](docs/requisitos/requisitos.md); stack em [ADR-0001](docs/adr/ADR-0001%20Stack%20do%20projeto.md).

## Pré-requisito

Somente Docker com Docker Compose. Nada precisa ser instalado na máquina.

## Subir

```bash
docker compose up -d --build
```

- Aplicação: <http://localhost:8000>
- Saúde: <http://localhost:8000/health> — `200 {"status": "ok", "banco": "ok"}` com o banco respondendo, `503` caso contrário.

O serviço `app` só inicia depois que o `db` (PostgreSQL) passa no healthcheck. A porta do banco não é publicada na máquina.

Parar: `docker compose down`. **Nunca** use `docker compose down -v`: apaga o volume do banco.

## Testar

```bash
docker compose run --rm --build app pytest
```

Os testes rodam dentro do contêiner, contra o PostgreSQL real do Compose. O código é copiado para a imagem (sem bind mount), por isso o `--build`: sem ele, os testes rodam na última imagem construída. Com a imagem já atualizada, `docker compose run --rm app pytest` basta.

## Configuração

Tudo por variáveis de ambiente, listadas em [.env.example](.env.example). Para personalizar, copie para `.env` (fora do Git) e ajuste.

Sem `.env`, o `docker-compose.yml` usa valores padrão **apenas para desenvolvimento local** (inclusive a senha do banco). Não use esses padrões em nenhum outro ambiente.

| Variável | Padrão (dev local) | Uso |
|---|---|---|
| `POSTGRES_USER` | `lab` | Usuário do banco |
| `POSTGRES_PASSWORD` | `lab_dev_somente_local` | Senha do banco |
| `POSTGRES_DB` | `lab` | Nome do banco |
| `POSTGRES_HOST` | `db` | Host do banco visto pela aplicação |
| `POSTGRES_PORT` | `5432` | Porta do banco vista pela aplicação |
| `APP_PORT` | `8000` | Porta publicada da aplicação |

## Versões

Fixadas em `requirements.txt` e no `Dockerfile` / `docker-compose.yml`, verificadas em 2026-09-28 no PyPI e no Docker Hub.

| Componente | Versão |
|---|---|
| Imagem Python | `python:3.14.7-slim-trixie` |
| Imagem PostgreSQL | `postgres:18.6-alpine` |
| FastAPI / Uvicorn / Jinja2 | 0.141.1 / 0.54.0 / 3.1.6 |
| SQLAlchemy / psycopg | 2.1.1 / 3.3.6 |
| pytest / httpx2 | 9.1.1 / 2.13.1 |

Só as dependências diretas são fixadas; as transitivas ficam a cargo do pip.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `app/` | Aplicação FastAPI (`main.py`), configuração e acesso ao banco |
| `app/templates/` | Páginas Jinja2 |
| `tests/` | Testes pytest |
| `docs/` | Requisitos, modelos e ADRs |
