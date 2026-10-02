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
docker compose run --build --rm lock   # regenera os 3 requirements*.txt (precisa de internet)
docker compose down              # para (NUNCA use down -v: apaga o banco)
```

**Por que `--build`:** `docker compose run` nao reconstroi uma imagem que ja existe. O codigo de `app/` e as dependencias ficam dentro da imagem; sem `--build`, `test` pode testar codigo velho e `audit` pode auditar dependencias velhas (confirmado na T-0009: sem `--build` o teste passou com o codigo quebrado e o `audit` nao viu uma dependencia vulneravel).

**Dependencias:** todas (diretas e indiretas) ficam travadas com versao exata e hash e sao instaladas com `pip install --require-hashes` ([ADR-0003](docs/adr/ADR-0003%20Dependencias%20travadas%20com%20hash%20via%20pip-tools.md)). Para atualizar ou incluir uma: edite `requirements.in` (aplicacao) ou `requirements-dev.in` (desenvolvimento), rode `docker compose run --build --rm lock` e faca commit dos `.in` **e** dos dois `requirements*.txt`. Nao edite os `requirements*.txt` a mao nem gere-os fora do container (o hash depende da plataforma).

- Aplicação: <http://localhost:8000> — saúde: <http://localhost:8000/health>
- Funciona sem `.env`, com valores padrão **somente para desenvolvimento local**. Para alterar, copie `.env.example` para `.env` (fora do Git).

## Seguranca da imagem

**Usuario sem privilegio (RNF-07):** a imagem `runtime` (servico `app`) roda como `app` (uid 10001); `docker compose exec app id -u` mostra `10001`. A imagem `dev` (`test`, `lint`, `audit`) continua como root (risco aceito: nao publica porta).

**Volume `uploads` antigo:** volume criado por imagem anterior tem arquivos de root, e o `app` nao consegue gravar nele (`PermissionError`). Volume **novo** herda a posse de `/uploads` da imagem e nao precisa de nada. Para ajustar um volume antigo uma vez, sem apagar nada (rode na pasta do projeto, depois do build):

```
docker compose run --rm --no-deps -u 0 --entrypoint chown app -R 10001:10001 /uploads
```

**Pacotes do sistema (RNF-09):** o estagio `base` roda `apt-get update && apt-get upgrade -y` (a tag de patch mais nova de `python:3.13-slim` ainda trazia openssl e libpcre2 com correcao pendente). O build em cache nao repete o upgrade: para pegar correcoes novas, reconstrua com `docker compose build --pull --no-cache app`. Conferencia:

```
docker compose run --rm --no-deps -u 0 --entrypoint sh app -c 'apt-get update -qq >/dev/null; apt list --upgradable'
```

A lista deve vir vazia (ou sem pacote de seguranca).

**Varredura da imagem:** o `pip-audit` so olha pacotes Python; a camada do sistema precisa de outra varredura, feita na maquina (precisa do `osv-scanner`). A tag e obrigatoria:

```
docker compose build app
osv-scanner scan image <projeto>-app:latest    # ex.: t-0008-endurecer-imagem-app:latest
```

Regra: CVE **com** correcao disponivel se corrige (atualize a imagem); CVE **sem** correcao nao e ignorada: vira registro de seguranca (`SEC-`) com triagem (usa o recurso afetado? e alcancavel?) e e revista a cada varredura. Resultado da T-0008 (2026-10-01): 17 pacotes Debian com 55 vulnerabilidades listadas, **nenhuma com correcao disponivel** (mais 26 de menor relevancia ocultadas pelo `osv-scanner`); openssl e libpcre2 limpos.
