---
tipo: decisao
status: aceita
decidido_em: 2026-09-30
decidido_por: Igor
substituida_por:
criado: 2026-09-30
tags: [lab, dependencias, supply-chain, seguranca]
---
# ADR-0003 Dependencias travadas com hash via pip-tools

## Contexto

O ADR-0001 diz que "o Dev fixa as versoes estaveis atuais" em `requirements.txt`, sem dizer se isso inclui as dependencias indiretas nem exigir hash. O SEC-0003 (T-0005) mostrou 29 dependencias indiretas do estagio dev sem versao e sem hash, e o mesmo padrao na runtime. Cada build resolve de novo no PyPI; o VER de um commit nao garante o conteudo da imagem reconstruida. O Pillow (ADR-0002) aumentaria esse conjunto.

Avaliacao completa: `docs/avaliacoes/travamento-de-dependencias.md` (pip-tools 88, uv 84, status quo 76, manual 70).

## Decisao

**Decisao (aceita em 2026-09-30):**

1. Dependencias diretas declaradas em `requirements.in` (runtime) e `requirements-dev.in` (dev, com `-c requirements.txt` no topo, fluxo em camadas do pip-tools).
2. `requirements.txt` e `requirements-dev.txt` passam a ser **gerados** por `pip-compile --generate-hashes` e versionados; ninguem os edita a mao.
3. A geracao roda num servico do Compose so para isso (`docker compose run --build --rm lock`), sobre a mesma imagem Python da aplicacao, com pip e pip-tools em versao exata e hash (`requirements-lock.in`/`.txt`, T-0014, SEC-0007); o servico roda sem root, so ve os 3 `.in` (leitura) e os 3 `.txt` (escrita), SEC-0008. Nada do pip-tools entra nas imagens `dev` e `runtime`.
4. O Dockerfile instala com `pip install --require-hashes`.
5. O `audit` passa a auditar os arquivos travados (`pip-audit --require-hashes -r ...`).

Implementacao: cartao T-0009.

## Alternativas consideradas

| Alternativa | Pros | Contras |
|---|---|---|
| pip-tools (escolhida) | Hash e camadas documentados no README oficial; saida e um `requirements.txt` comum | Acoplado a versao do pip; ferramenta extra no servico de travamento |
| uv (`uv pip compile --generate-hashes`) | Mais rapido; mesmo formato de saida (troca barata) | `--generate-hashes` so confirmado no codigo da CLI, nao na pagina de documentacao do `pip compile` |
| Manual (`pip freeze` + `pip hash`) | Sem ferramenta nova | Sujeito a erro; ninguem vai manter |
| Status quo (so diretas, risco aceito) | Nenhum trabalho | Mantem o SEC-0003 aberto; build nao reproduzivel |

## Consequencias

- **Positivas:** fecha o SEC-0003; build reproduzivel; `pip-audit` e VER passam a olhar exatamente o que sera instalado; base para o Pillow (ADR-0002).
- **Negativas / riscos:**
  - Mudar uma dependencia exige regenerar o travado (`run --build --rm lock`) em vez de editar uma linha. Esse comando precisa estar no README.
  - Hash depende da plataforma: gerar fora do container (ex.: Windows) pode produzir um arquivo que nao instala na imagem. Por isso o servico de travamento.
  - Se o pip-tools quebrar com um pip novo, trocar para o uv (mesmos `.in`).

## Relacionadas

- ADR-0001 Stack do projeto (complementa a frase "o Dev fixa as versoes")
- ADR-0002 Imagem decodificada e regravada com Pillow
- [[CWE-829 dependencia sem versao e sem hash se evita com requirements travado com hashes]]
- [[CWE-1395 dependencia vulneravel se evita com auditoria do arquivo travado e da camada do sistema da imagem]]
- SEC-0003
