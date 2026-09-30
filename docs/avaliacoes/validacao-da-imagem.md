---
tipo: avaliacao-tecnologia
status: rascunho
consultado_em: 2026-09-30
adr: ADR-0002 Imagem decodificada e regravada com Pillow
---
# Avaliacao - Validacao da imagem enviada (cabecalho ou Pillow)

## Pergunta

Basta validar a imagem pelo cabecalho (magic bytes), como hoje, ou ela deve ser decodificada e/ou regravada com uma biblioteca de imagem (Pillow, dependencia nova)? Pendencia adiada na T-0003 (observacao do VER-0006 e do VER-0007).

## Situacao atual (T-0003)

- `app/imagens.py` confere so os bytes iniciais: JPEG `FFD8FF`, PNG (8 bytes), WebP `RIFF....WEBP`. Grava **os bytes enviados**, sem alteracao.
- Servido em `/uploads/<32 hex>.<ext>` com `Content-Type` fixo pela extensao gerada e `X-Content-Type-Options: nosniff`.
- Aceito hoje (VER-0006): cabecalho JPEG seguido de lixo (aparece como imagem quebrada) e poliglota JPEG + HTML (servido como `image/jpeg`, o navegador nao interpreta como HTML).
- Os metadados da foto (EXIF, inclusive GPS de celular) sao gravados e servidos a quem abrir a listagem.

## Restricoes

- Stack do ADR-0001 (Python 3.13, FastAPI, Docker). Nada de servico externo.
- Formatos continuam JPEG, PNG e WebP; limite de 2 MB por arquivo enviado (requisitos, T-0003).
- Uso local, sem autenticacao (requisitos, questoes em aberto). **Premissa:** continua assim; exposicao publica mudaria os pesos (ver "O que faria mudar de ideia").

## Criterios e pesos

Definidos antes das notas. Pesos somam 100. Notas de 1 (pior) a 5 (melhor).

| Criterio | Peso | Por que importa |
|---|---|---|
| Seguranca do arquivo gravado e servido | 25 | Arquivo com conteudo arbitrario (poliglota, lixo apos o cabecalho) fica no volume e e servido; hoje mitigado por `nosniff` e tipo fixo |
| Risco da propria dependencia | 20 | Decodificar dado nao confiavel em codigo C amplia a superficie; o Pillow tem historico de avisos de seguranca |
| Privacidade (metadados) | 15 | Foto de celular pode levar GPS e modelo do aparelho para a listagem |
| Experiencia do usuario | 15 | Arquivo corrompido deveria voltar com mensagem na pagina, e nao aparecer como imagem quebrada |
| Custo de manutencao | 15 | Dependencia nova precisa ser travada, auditada e atualizada; mais testes |
| Recursos por upload | 10 | CPU e memoria para decodificar ate a dimensao maxima |

## Alternativas

- **A - Cabecalho (status quo):** manter a validacao por magic bytes e gravar os bytes originais.
- **B - Pillow so para validar:** abrir e decodificar a imagem inteira para recusar arquivo corrompido, mas gravar os bytes originais.
- **C - Pillow para decodificar e regravar:** decodificar, aplicar a orientacao do EXIF, descartar metadados e gravar o arquivo **gerado pela aplicacao** no mesmo formato.

| Criterio (peso) | A - Cabecalho | B - Pillow valida | C - Pillow regrava |
|---|---|---|---|
| Seguranca do arquivo (25) | 3 - `nosniff` + tipo fixo mitigam; poliglota e lixo continuam no volume | 3 - recusa lixo, mas imagem valida com dados anexados (poliglota) passa e e gravada como veio | 5 - o que e gravado sai do codificador; dados anexados e metadados nao sobrevivem |
| Risco da dependencia (20) | 5 - nenhuma dependencia nova | 2 - decodifica dado nao confiavel (mesma superficie de C) | 2 - idem; mitigavel com `formats=` restrito, limite de pixels, dependencia travada e container sem root |
| Privacidade (15) | 1 - EXIF/GPS servidos | 1 - idem | 5 - metadados descartados |
| Experiencia (15) | 2 - corrompido aparece quebrado | 4 - corrompido recusado com mensagem | 5 - recusado com mensagem; orientacao aplicada no arquivo |
| Manutencao (15) | 5 - nada novo | 3 - dependencia nova, testes com imagens reais | 3 - idem, mais regras de conversao de modo de cor |
| Recursos (10) | 5 - so le bytes | 3 - decodifica | 2 - decodifica e codifica |
| **Total ponderado** (soma peso x nota / 5) | **69** | **53** | **76** |

**Sensibilidade:** o resultado depende da privacidade e da experiencia. Com peso 0 para privacidade (os mesmos 15 pontos fora), A fica com 66 e C com 61 (em pontos de 85). B nao vence em nenhum cenario razoavel: paga o custo da dependencia sem tirar o conteudo original do volume.

## Fatos volateis consultados

| Fato | Valor | Fonte oficial | Data |
|---|---|---|---|
| Versao atual do Pillow | 12.3.0, `requires_python >=3.10` | https://pypi.org/pypi/pillow/json | 2026-09-30 |
| Wheel para a imagem do projeto (CPython 3.13, Linux x86_64) | existe (`...cp313-cp313-manylinux_2_28_x86_64.whl`, ~3,4 MB) | https://pypi.org/pypi/pillow/json | 2026-09-30 |
| Avisos de seguranca recentes | 16 avisos GHSA publicados em 20/07/2026 e 4 PYSEC em 23/07/2026, com correcao disponivel; ex.: GHSA-9hw9-ch79-4vh6 (escrita fora dos limites em `ImageCms`, CVSS 7.5), afeta ate 12.2.0, corrigido em 12.3.0 | https://osv.dev/list?q=pillow&ecosystem=PyPI e https://osv.dev/vulnerability/GHSA-9hw9-ch79-4vh6 | 2026-09-30 |
| Protecao contra bomba de descompressao | `MAX_IMAGE_PIXELS` padrao 89.478.485; acima dele, `DecompressionBombWarning`; acima do dobro, `DecompressionBombError` | https://github.com/python-pillow/Pillow/blob/main/docs/reference/Image.rst | 2026-09-30 |
| Suporte a WebP na wheel | **nao confirmado em fonte**; vira criterio de aceite (`PIL.features.check("webp")` na imagem) | - | - |

Conhecimento estavel usado sem fonte consultada nesta tarefa (conferir na implementacao): `Image.open` le so o cabecalho ate `load()`; `Image.open(..., formats=[...])` restringe os decodificadores tentados; `ImageOps.exif_transpose` aplica a orientacao do EXIF. A pagina `docs/reference/ImageOps.rst` foi aberta, mas nao descreve a funcao.

## Recomendacao

**C - decodificar e regravar com Pillow** (ADR-0002, `proposta`), com estas condicoes:

1. Entra **depois** do travamento de dependencias com hash (SEC-0003, T-0009): o Pillow ja nasce travado e auditado, o que responde ao historico de avisos.
2. Decodificadores restritos a JPEG, PNG e WebP (`formats=`), limite de pixels proprio bem abaixo do padrao e conferencia de dimensoes antes de `load()`.
3. De preferencia depois do container sem root (SEC-0004, T-0008): limita o dano de uma falha de decodificador.

**Riscos:** o Pillow passa a ser a dependencia com mais avisos do projeto e exige atualizacao rapida; regravar JPEG perde um pouco de qualidade; imagens animadas perdem a animacao (premissa: so o primeiro quadro).

**Custo da nova dependencia:** ~3,4 MB de wheel na imagem runtime; uma entrada a mais no arquivo travado e no `pip-audit`; testes com imagens reais geradas pelo proprio Pillow nos testes; decodificacao limitada a arquivos de ate 2 MB.

**O que faria mudar de ideia:** se o humano disser que os metadados das fotos nao importam e que imagem quebrada na listagem e aceitavel, **A com o risco aceito e defensavel** (69 contra 76, e vence sem o peso da privacidade). Se a aplicacao for exposta publicamente ou ganhar autenticacao, C fica ainda mais forte.
