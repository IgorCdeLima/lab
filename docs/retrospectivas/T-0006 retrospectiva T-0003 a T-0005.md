---
tipo: retrospectiva
status: proposta
tarefa: T-0006
atualizado: 2026-09-30
---
# Retrospectiva das tarefas T-0003 a T-0005 (defeitos, achados de seguranca e processo)

Escrita pelo Engenheiro na T-0006. Base: cartoes T-0003, T-0004 e T-0005, `qualidade/` (VER-0006 a VER-0010, BUG-0006, BUG-0007, SEC-0001 a SEC-0005) e o historico do Git do Brain (quando cada regra entrou). As melhorias de processo estao propostas como candidatos no `BRAIN/00_Inbox`, porque regras de `60_Agentes` e `70_Workflows` so o humano altera.

## Linha do tempo que importa

| Quando (2026-09-30) | Evento | Fonte |
|---|---|---|
| 07:56 | Regra nova: "funcionalidade com entrada de usuario passa antes pelo Engenheiro" e checklist de entradas extremas na matriz | Brain `41a6ef2` |
| 08:02 | Papel Designer e marca `interface:` | Brain `b87e716` |
| 09:56 | T-0003 vai para `pronta` **sem cartao do Engenheiro, sem triagem e sem as marcas** `interface:`/`seguranca:` (cartao criado em 2026-09-28, antes delas) | Brain `3a77a48` |
| 10:38 | T-0003 concluida depois de 2 rodadas (VER-0006 reprovado, VER-0007 aprovado) | Brain `1dcaf87` |
| 11:09 | Papeis Coordenador e Seguranca (triagem e analise de ameacas passam a existir) | Brain `ab6db60` |
| tarde | T-0004 (1 rodada) e T-0005 (VER-0009 parcial, VER-0010 aprovado) | cartoes |

Conclusao da linha do tempo: a regra que teria mudado a T-0003 **ja existia** duas horas antes de a tarefa ir para `pronta`, mas nada no caminho a conferia. O lancador `papel` confere pasta, papel e status, nao os pre-requisitos da triagem.

## Causa raiz de cada registro

| Registro | Sev. | Causa raiz | Onde poderia ter sido pego | Papel | Foi pego por |
|---|---|---|---|---|---|
| BUG-0006 (413 em JSON cru acima de ~2,06 MB) | media | Teto anti-DoS (`Content-Length`) quase igual ao limite de negocio (2 MB + 64 KB); o teste de "tamanho excedido" usava 2 MB + 58 bytes | 1) Requisito: a regra "ate 2 MB" nao dizia o que o usuario ve com uma foto tipica de 3 a 5 MB nem separava teto de limite. 2) Teste do Dev com o caso tipico, nao so limite + 1 | Engenheiro (regra com exemplos, incluindo "arquivo tipico grande demais"); Dev (teste) | Revisor, rodada 1 (custou 1 rodada) |
| SEC-0001 (POST chunked sem limite) | baixa | O limite so olhava `Content-Length`; RNF-05 ("limite de tamanho no upload") nao era verificavel (sem numero, sem dizer "com e sem `Content-Length`") | 1) RNF verificavel. 2) Analise de ameacas de upload (CWE-770/CWE-434 citam chunked). 3) O proprio Dev listou "chunked" como NAO verificado e mesmo assim entregou | Engenheiro; Seguranca (ameacas); Dev | Revisor, rodada 1 |
| BUG-0007 (comentario do Dockerfile no estagio errado) | baixa | Frase sobre o estagio `runtime` escrita no bloco do `dev` | Autorrevisao do diff pelo Dev | Dev | Revisor, na mesma rodada. **Sem mudanca de processo**: custo de prevenir > dano |
| SEC-0002 (openssl da imagem base; `pip-audit` nao ve a camada do sistema) | baixa | 1) Nenhum requisito sobre a imagem base (ADR-0001 so diz "versoes estaveis atuais"). 2) O escopo do `pip-audit` (so Python) nao foi escrito; "No known vulnerabilities" foi lido como "imagem limpa" | Requisito da T-0005 ("varredura cobre pacotes Python **e** do sistema"); analise de ameacas da T-0005, que foi dispensada | Engenheiro; Seguranca | Seguranca, revisao da T-0005 (pre-existente) |
| SEC-0003 (29 dependencias indiretas sem versao nem hash) | baixa | ADR-0001: "o Dev fixa as versoes" sem dizer "inclusive indiretas" e sem hash; a T-0005 trouxe 29 indiretas novas | RNF verificavel desde a T-0001; analise de ameacas da T-0005 (dependencias novas), dispensada | Engenheiro; Seguranca | Seguranca, revisao da T-0005 |
| SEC-0004 (container como root) | baixa | Dockerfile da T-0001 sem `USER`; nenhum checklist de endurecimento da imagem | Linha de base de seguranca do projeto (nao existia; o papel Seguranca nasceu depois da T-0003) | Seguranca (linha de base) | Seguranca, revisao da T-0005 (pre-existente) |
| SEC-0005 (sem CSP/`X-Frame-Options`/`nosniff` na pagina) | baixa | Pagina criada na T-0002 sem requisito de cabecalhos; a revisao de seguranca da T-0003 (Revisor) olhou o upload, nao a pagina | Linha de base; checklist de revisao de seguranca com "cabecalhos HTTP" | Seguranca | Seguranca, revisao da T-0005 (pre-existente) |
| VER-0009 parcial (Revisor antes da Seguranca) | - | O fluxo diz a ordem, mas o lancador aceita `papel revisor` com `seguranca: sim` e sem a secao "Revisao de seguranca" | Lancador ou Coordenador, antes de abrir o Revisor | Coordenador / lancador | Revisor (registrou `parcial`; custou 1 VER extra) |
| O1 (`audit` sem `--build` pode ler imagem velha) | - | `docker compose run` nao reconstroi imagem existente. A nota [[Imagem Docker que embute o codigo exige build antes de rodar pytest]] ja descrevia o mesmo problema, mas nao foi aplicada aos servicos novos (`test`, `lint`, `audit`) | Dev da T-0004/T-0005 ao criar os servicos (consultar o Brain) | Dev | Revisor (nao reproduziu: sem permissao para alterar uma copia) |

## Respostas as pistas do cartao

1. **Um cartao do Engenheiro antes da T-0003 teria evitado o BUG-0006?** Provavelmente sim, mas so se os exemplos de upload incluissem o "arquivo tipico grande demais" (3 a 5 MB) e o envio sem `Content-Length`. O guia atual pede "muito longo (limite + 1 e algo absurdo)", o que, para upload, levaria a 2 MB + 1 e talvez 1 GB, e este ultimo cai no teto e poderia ser aceito como 413 correto. **Falta o item especifico de upload** na matriz e no guia. A retrospectiva da T-0002 ja propos esse item ([[T-0002 mostrou que regra de entrada ambigua vira bug e que o Revisor precisa testar extremos]]); ele nao entrou na matriz.
2. **A T-0003 mudou a tela sem `interface: sim` nem Designer.** O cartao era de 2026-09-28, anterior a marca. Nenhum defeito visual foi registrado, mas nas duas rodadas o navegador real ficou sem verificacao (extensao do Chrome indisponivel), e ate hoje nao se sabe o que o navegador mostra no 413 acima de 10 MB. Causa: **cartao antigo nao foi retriado quando a regra mudou**.
3. **Lacunas na Entrega deveriam bloquear a ida para revisao?** Bloquear tudo incentivaria esconder lacunas. Proposta: lacuna que toca um **criterio de aceite** ou uma **verificacao obrigatoria** (ex.: "chunked nao verificado" numa tarefa de upload com `seguranca`) nao pode ir para `revisao` sem uma de duas saidas: fechar a lacuna ou registrar a pergunta em "Passos do humano" com o motivo. As demais lacunas seguem so declaradas (como hoje).
4. **O papel Seguranca teria pego o SEC-0001?** Provavel: a analise de ameacas de upload cobre CWE-770 e CWE-434, e as notas atuais citam chunked explicitamente ([[CWE-434 upload sem restricao exige validar o tipo pelo conteudo e servir por nome gerado]], [[CWE-770 recursos sem limite se evitam com limite de corpo, timeout e rate limit]]). Nao e comprovavel: essas notas sao do mesmo dia. O ganho seria evitar uma rodada, porque o Revisor pegou na rodada 1.

## Padroes que aparecem

- **Regra sem portao nao e seguida.** A regra do Engenheiro (T-0003) e a ordem Seguranca -> Revisor (T-0005) existiam por escrito. O que falhou foi a conferencia no momento da transicao.
- **Requisito nao verificavel deixa a lacuna para o Revisor.** RNF-05 e o "fixa as versoes" do ADR-0001 eram vagos; os achados vieram exatamente dessas lacunas.
- **Achados pre-existentes chegam tarde.** Tres dos quatro SEC da T-0005 existiam desde a T-0001/T-0002. Nao houve linha de base quando o papel Seguranca foi criado.
- **O processo pegou tudo antes da `main`**, com custo de 2 rodadas extras (T-0003 e T-0005). Nenhum defeito chegou ao humano depois do merge.
- **Edicoes em `CLAUDE.md` do projeto (N4) viram escalacao.** Cada comando novo (T-0004, T-0005) passou por Coordenador -> Administrador. Os comandos poderiam ter fonte unica no README.

## Melhorias propostas (candidatos no Inbox)

| # | Melhoria | Onde mudaria | Candidato |
|---|---|---|---|
| M1 | Portao no lancador: `papel revisor` com `seguranca: sim` exige a secao "Revisao de seguranca" preenchida; com `interface: sim`, a "Revisao visual" | `ferramentas/papel`, Fluxo de tarefa | Regra de fluxo sem portao no lancador nao e seguida |
| M2 | Triagem registrada no cartao (`triagem:` com data) e o lancador `papel dev` recusa cartao `normal`/`grande` sem triagem; ao mudar uma regra de fluxo, os cartoes em `backlog`/`pronta` voltam para triagem | Fluxo de tarefa, template Tarefa, lancador | Regra de fluxo sem portao no lancador nao e seguida |
| M3 | Lacuna da Entrega que toca criterio de aceite ou verificacao obrigatoria: fechar ou levar ao humano antes de `revisao` | 60_Agentes/Dev, Fluxo de tarefa | Lacuna declarada pelo Dev em criterio de aceite precisa de destino antes da revisao |
| M4 | Checklist de entradas extremas para **upload**: limite + 1, arquivo tipico grande demais, acima do teto, sem `Content-Length`, cabecalho valido com corpo invalido | Matriz de verificacao, Padroes de modelagem | Checklist de entradas extremas precisa de itens proprios para upload |
| M5 | Linha de base de seguranca do projeto (container sem root, cabecalhos HTTP, dependencias travadas com hash, varredura da imagem) no ADR de stack de todo projeto novo e uma vez em cada projeto existente quando o papel/regra nasce | Fluxo de tarefa, 60_Agentes/Seguranca e Engenheiro | Projeto novo precisa de linha de base de seguranca no ADR de stack |
| M6 | Servicos Compose que embutem codigo ou dependencias (`test`, `lint`, `audit`) usam `run --build` nos comandos documentados; Revisor pode fazer experimento em copia descartavel no scratchpad | README do projeto, perfil do Revisor | docker compose run nao reconstroi e faz testes e auditoria olharem imagem velha |
| M7 | Comandos do projeto com fonte unica no README; o `CLAUDE.md` do projeto aponta para ele (menos escalacoes N4) | CLAUDE.md dos projetos (N4) | Regra de fluxo sem portao no lancador nao e seguida |

Armadilhas de modelagem encontradas ao especificar os cartoes (tambem no Inbox): "CSP default-src self bloqueia o style inline dos templates" e "Regravar imagem sem EXIF exige aplicar a orientacao antes".

## Plano para os SEC-0002 a SEC-0005 e a O1

| Registro | Solucao escolhida | Como testar | Cartao |
|---|---|---|---|
| SEC-0002 | Tag de patch mais nova de `python:3.13-slim` (ou `apt-get upgrade` no estagio base, se a tag nao trouxer a correcao) + varredura da imagem documentada, com triagem das CVE sem correcao (RNF-09) | `apt list --upgradable` na runtime sem openssl/libssl3t64/libpcre2; `osv-scanner scan image` registrado | T-0008 |
| SEC-0003 | Arquivos travados com hash gerados por pip-tools e `pip install --require-hashes` (RNF-06, ADR-0003) | Linhas com `==` e hash; build falha sem hash; `pip freeze` bate com o travado | T-0009 |
| SEC-0004 | `USER` sem privilegio na runtime, `/uploads` com posse do usuario, ajuste unico de posse dos volumes antigos (RNF-07). Imagem dev continua root (risco aceito, premissa) | `id -u` != 0; upload com volume novo e antigo | T-0008 |
| SEC-0005 | Middleware ASGI com CSP (`frame-ancestors 'none'`, `style-src 'unsafe-inline'` por causa do CSS inline), `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy` em toda resposta (RNF-08) | Testes nos 8 tipos de resposta; navegador sem violacao de CSP | T-0007 |
| O1 | Confirmar em copia descartavel (`audit` e tambem `test`) e documentar `run --build` (RNF-10) | Roteiro na Parte 1 do cartao | T-0009 |
| Pillow (VER-0006) | Decodificar e regravar (ADR-0002, proposta) | Tabela "Exemplos de entrada - imagem" do `requisitos.md` | T-0010 |

Ordem sugerida: **T-0007** (independente, pode ir ja) e **T-0009** -> **T-0008** (mesmo Dockerfile, em sequencia) -> **T-0010** (depende do ADR-0002 aceito e da T-0009; recomendado depois da T-0008). Diagrama em `docs/modelos/modelos.md`.

## O que NAO foi avaliado

- Tempo e custo (tokens) de cada rodada: nao ha medida nos cartoes.
- As tarefas T-0001 e T-0002 (ja cobertas pelas retrospectivas anteriores), exceto como origem dos SEC pre-existentes.
- Se o Chrome/Firefox mostra JSON ou erro de conexao no 413: continua sem verificacao (VER-0007).
