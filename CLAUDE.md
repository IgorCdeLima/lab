# Projeto lab — cadastro de produtos

Projeto laboratório da equipe 01_IA: uma pequena landing page para cadastrar produtos (nome, valor, fornecedor e imagem) e exibi-los.

**Regras globais do ambiente:** `D:\01_IA\CLAUDE.md` — leia antes de trabalhar. Elas valem aqui também.

## Stack

Ver `docs/adr/ADR-0001 Stack do projeto.md`: Python + FastAPI (páginas renderizadas no servidor com Jinja2), PostgreSQL, SQLAlchemy, pytest, tudo rodando com Docker Compose.

## Como rodar

- Subir: `docker compose up -d --build`
- Testes: `docker compose run --rm app pytest`
- Parar: `docker compose down` (**nunca** `down -v`, que apaga o banco)

### Portas por worktree

Vários worktrees podem rodar ao mesmo tempo. Os volumes já são separados (o nome do projeto Compose vem da pasta), mas a porta não. Use:

| Quem | Onde | Porta | Comando (Bash) |
|---|---|---|---|
| Humano | cópia principal (`main`) | 8000 | `docker compose up -d --build` |
| Dev | worktree `T-000N-...` | 8000 + N (T-0002 → 8002) | `APP_PORT=8002 docker compose up -d --build` |
| Revisor | worktree da tarefa, projeto próprio | 8100 + N (T-0002 → 8102) | `APP_PORT=8102 docker compose -p t0002-rev up -d --build` |

No PowerShell: `$env:APP_PORT=8002; docker compose up -d --build`. Ao terminar, pare com `docker compose down` (com `-p` se usou) — **sem** `-v`; volumes de teste a remover vão para "Passos do humano" do cartão.

Configuração por variáveis de ambiente em `.env` (fora do Git). O modelo versionado é `.env.example`. **Nunca** coloque segredos no código, no `docker-compose.yml` ou em commits.

## Onde fica cada coisa

| Pasta | Conteúdo |
|---|---|
| `docs/requisitos/` | Requisitos e critérios de aceite |
| `docs/modelos/` | Diagramas em Mermaid (contexto, domínio, ER) |
| `docs/adr/` | Decisões de arquitetura do projeto |
| `qualidade/` | `VER-`, `BUG-`, `SEC-` do projeto — só revisor, segurança e coordenador escrevem |

## Padrões

- Valores monetários: `Decimal` / `NUMERIC(10,2)`, **nunca** `float`.
- Toda funcionalidade nova vem com teste automatizado.
- Documentação (`docs/`) é atualizada no mesmo commit da mudança que a afeta.
- Commits: `tipo(escopo): descrição`, em português. Os trailers são adicionados pelo hook do Git.
