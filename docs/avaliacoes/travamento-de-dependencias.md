---
tipo: avaliacao-tecnologia
status: rascunho
consultado_em: 2026-09-30
adr: ADR-0003 Dependencias travadas com hash via pip-tools
---
# Avaliacao - Ferramenta para travar as dependencias com hash (SEC-0003)

## Pergunta

Como fixar **todas** as dependencias Python (diretas e indiretas, runtime e dev) com versao exata e hash, para que o build instale sempre o mesmo conjunto e recuse pacote adulterado? Origem: SEC-0003 (29 indiretas do estagio dev sem versao nem hash; o `requirements.txt` da runtime tem o mesmo padrao).

## Restricoes

- Instalacao continua com `pip install` no Dockerfile (ADR-0001), agora com `--require-hashes` ([[CWE-829 dependencia sem versao e sem hash se evita com requirements travado com hashes]]).
- A geracao do arquivo travado roda em container (RNF-01: nada instalado na maquina), na mesma versao de Python e plataforma da imagem (Linux, CPython 3.13), porque as wheels e os hashes dependem disso.
- Nada da ferramenta de travamento entra na imagem runtime.
- O `pip-audit` deve poder auditar o arquivo travado (`-r ... --require-hashes`), conforme [[CWE-1395 dependencia vulneravel se evita com auditoria do arquivo travado e da camada do sistema da imagem]].

## Criterios e pesos

| Criterio | Peso | Por que importa |
|---|---|---|
| Integridade (versao exata + hash de todas, inclusive indiretas) | 30 | E o controle pedido pelo SEC-0003 |
| Compatibilidade com o fluxo atual (`pip install -r`, `pip-audit -r`, camadas runtime/dev) | 20 | Evita reescrever Dockerfile e Compose alem do necessario |
| Funcao de hash documentada em fonte oficial | 20 | Decisao de seguranca nao deve depender de opcao nao documentada |
| Custo operacional (ferramenta nova, comando de atualizacao, erro humano) | 20 | O Dev atualiza dependencias com frequencia (ex.: avisos do Pillow) |
| Velocidade da resolucao | 10 | Projeto pequeno: importa pouco |

## Alternativas

- **A - pip-tools** (`pip-compile --generate-hashes`), com `requirements.in` e `requirements-dev.in` (este com `-c requirements.txt`).
- **B - uv** (`uv pip compile --generate-hashes`), mesmos arquivos `.in`.
- **C - Manual:** `pip freeze` no container e hashes com `pip hash`/`pip download`.
- **D - Status quo:** manter so as diretas fixadas e aceitar o risco.

| Criterio (peso) | A - pip-tools | B - uv | C - Manual | D - Status quo |
|---|---|---|---|---|
| Integridade (30) | 5 - versao + hash de tudo | 5 - idem | 4 - possivel, mas facil esquecer um pacote | 1 - so diretas, sem hash |
| Compatibilidade (20) | 5 - gera `requirements.txt` comum; camadas com `-c` documentadas | 5 - gera `requirements.txt` comum | 5 - idem | 5 - nada muda |
| Hash documentado (20) | 5 - secao "Using hashes" e "layered requirements" no README oficial | 3 - opcao existe no codigo da CLI ("Include distribution hashes in the output file."), mas a pagina de `pip compile` da documentacao nao a cita | 4 - `pip hash` e `--require-hashes` documentados no pip | 5 - nao se aplica |
| Custo operacional (20) | 3 - ferramenta Python extra so no servico de travamento; acoplada a versao do pip (conferir no cartao) | 3 - binario extra so no servico de travamento | 1 - processo manual, sujeito a erro | 5 - nenhum |
| Velocidade (10) | 3 | 5 | 3 | 5 |
| **Total ponderado** (soma peso x nota / 5) | **88** | **84** | **70** | **76** |

## Fatos volateis consultados

| Fato | Valor | Fonte oficial | Data |
|---|---|---|---|
| Versao do pip-tools | 7.6.1, `requires_python >=3.9` | https://pypi.org/pypi/pip-tools/json | 2026-09-30 |
| pip-tools: hashes e camadas | README tem "Using hashes" (`--generate-hashes`) e "Workflow for layered requirements" (`-c requirements.txt` no `dev-requirements.in`); sem aviso de projeto arquivado | https://github.com/jazzband/pip-tools | 2026-09-30 |
| Versao do uv | 0.12.21, licenca MIT OR Apache-2.0 | https://pypi.org/pypi/uv/json | 2026-09-30 |
| uv: hashes | `--generate-hashes` existe no codigo da CLI; `docs/pip/compile.md` nao o menciona | https://raw.githubusercontent.com/astral-sh/uv/main/crates/uv-cli/src/lib.rs e https://github.com/astral-sh/uv/blob/main/docs/pip/compile.md | 2026-09-30 |
| pip: modo `--require-hashes` | todo requisito precisa de `==` e hash; um `--hash` liga o modo para tudo | https://pip.pypa.io/en/stable/topics/secure-installs/ (via [[CWE-829 dependencia sem versao e sem hash se evita com requirements travado com hashes]], verificado em 2026-09-30) | 2026-09-30 |

A data de publicacao das versoes nao foi confirmada (o resumo do PyPI veio inconsistente). O Dev confere a versao mais nova no PyPI ao implementar.

## Recomendacao

**A - pip-tools** (ADR-0003, `proposta`). Vence por pouco o uv (88 x 84) pela documentacao oficial da funcao de hash e do fluxo em camadas, que e exatamente o caso runtime/dev do projeto.

**Riscos:** o pip-tools depende de APIs internas do pip; se uma versao nova do pip o quebrar, o servico de travamento fica sem funcionar ate atualizar. Mitigacao: fixar a versao do pip e do pip-tools no servico de travamento.

**O que faria mudar de ideia:** se o pip-tools nao funcionar com o pip da imagem, ou se a documentacao do uv passar a descrever `--generate-hashes`, trocar para B: os arquivos `.in` e o formato de saida sao os mesmos, entao a troca e barata.
