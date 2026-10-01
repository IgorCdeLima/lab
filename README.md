# lab — cadastro de produtos

Landing page simples para cadastrar produtos com nome, valor, fornecedor e imagem.

Projeto laboratório da equipe de agentes 01_IA. Padrões em [CLAUDE.md](CLAUDE.md); requisitos em [docs/requisitos](docs/requisitos/requisitos.md).

## Como rodar

Requer apenas Docker com Compose.

```
docker compose up -d --build     # sobe app e db (o app espera o banco ficar saudável)
docker compose run --build --rm test   # testes (imagem propria com pytest, contra o PostgreSQL do Compose)
docker compose run --build --rm lint   # lint (ruff, config no pyproject.toml)
docker compose run --build --rm audit  # vulnerabilidades dos arquivos travados e da imagem (pip-audit; precisa de internet)
docker compose run --build --rm lock   # regenera requirements.txt e requirements-dev.txt (precisa de internet)
docker compose down              # para (NUNCA use down -v: apaga o banco)
```

**Por que `--build`:** `docker compose run` nao reconstroi uma imagem que ja existe. O codigo de `app/` e as dependencias ficam dentro da imagem; sem `--build`, `test` pode testar codigo velho e `audit` pode auditar dependencias velhas (confirmado na T-0009: sem `--build` o teste passou com o codigo quebrado e o `audit` nao viu uma dependencia vulneravel).

**Dependencias:** todas (diretas e indiretas) ficam travadas com versao exata e hash e sao instaladas com `pip install --require-hashes` ([ADR-0003](docs/adr/ADR-0003%20Dependencias%20travadas%20com%20hash%20via%20pip-tools.md)). Para atualizar ou incluir uma: edite `requirements.in` (aplicacao) ou `requirements-dev.in` (desenvolvimento), rode `docker compose run --build --rm lock` e faca commit dos `.in` **e** dos dois `requirements*.txt`. Nao edite os `requirements*.txt` a mao nem gere-os fora do container (o hash depende da plataforma).

- Aplicação: <http://localhost:8000> — saúde: <http://localhost:8000/health>
- Funciona sem `.env`, com valores padrão **somente para desenvolvimento local**. Para alterar, copie `.env.example` para `.env` (fora do Git).
