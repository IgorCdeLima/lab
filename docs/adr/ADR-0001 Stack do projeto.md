---
tipo: decisao
status: aceita
decidido_em: 2026-09-28
decidido_por: Igor
substituida_por:
criado: 2026-09-28
tags: [lab, stack]
---
# ADR-0001 Stack do projeto

## Contexto

Projeto laboratório pequeno: uma página de cadastro e listagem de produtos com imagem. Restrições dadas: Python, Docker e PostgreSQL. Objetivo principal é validar o fluxo da equipe de agentes, então a stack deve ser simples, testável e sem etapa de build de front-end.

## Decisão

- **FastAPI** com páginas renderizadas no servidor (**Jinja2**) e formulários HTML comuns — sem framework JavaScript.
- **PostgreSQL** em contêiner; acesso via **SQLAlchemy 2** com driver **psycopg 3**.
- **pytest** + cliente de teste do FastAPI, rodando contra um PostgreSQL real no Compose.
- **Docker Compose** com serviços `app` e `db`; volumes para dados e uploads.
- Imagens gravadas no volume de uploads; o banco guarda só o nome do arquivo gerado.
- Versões: o Dev fixa as versões estáveis atuais (fato volátil — verificar na documentação oficial) em `requirements.txt` e nas imagens Docker.

## Alternativas consideradas

| Alternativa | Prós | Contras |
|---|---|---|
| Django | Admin e formulários prontos | Mais pesado e opinativo para uma página só |
| Flask | Muito simples | Menos validação embutida; FastAPI dá tipagem e testes fáceis |
| Front-end separado (React etc.) | Interface mais rica | Build de JS, dois projetos — foge do objetivo |
| Imagem no banco (bytea) | Um só lugar | Banco cresce e fica lento; backup pesado |

## Consequências

- **Positivas:** um único serviço Python, testes simples, sem Node.
- **Negativas / riscos:** migrações de banco ficam para uma tarefa futura (início com criação de tabelas pela aplicação).
