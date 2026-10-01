---
tipo: requisitos
status: rascunho
versao: 2
atualizado: 2026-09-30
---
# Requisitos — cadastro de produtos

## Visão

Uma página única onde o usuário cadastra produtos e vê os produtos já cadastrados, cada um com imagem.

## Requisitos funcionais

| ID | Requisito | Tarefa |
|---|---|---|
| RF-01 | A aplicação expõe uma verificação de saúde que confirma que a aplicação e o banco estão funcionando | T-0001 |
| RF-02 | Cadastrar produto com **nome**, **valor** e **fornecedor** | T-0002 |
| RF-03 | Listar os produtos cadastrados na mesma página, do mais recente para o mais antigo | T-0002 |
| RF-04 | Anexar uma **imagem** ao produto e exibi-la na listagem | T-0003 |

## Regras de validação

| Campo | Regra |
|---|---|
| Nome | Obrigatório, 1 a 120 caracteres, sem espaços nas pontas |
| Valor | Obrigatório, maior que zero, duas casas decimais, até 99.999.999,99. Formato pt-BR: vírgula decimal, ponto de milhar (`1.234` = 1234,00); ponto decimal só sem vírgula e com 1-2 casas (`12.5`); mais de duas casas é erro, sem arredondar |
| Fornecedor | Obrigatório, 1 a 120 caracteres |
| Imagem | Opcional; JPEG, PNG ou WebP; até 2 MB enviados; tipo pelos magic bytes **e** pela decodificação completa (o formato decodificado tem de ser o mesmo); lado até 10.000 px e área até 50 megapixels; a aplicação grava a imagem **regravada** (T-0010), no mesmo formato, com a orientação do EXIF aplicada e sem metadados; imagem animada ou multi-imagem vira o primeiro quadro |

## Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | Tudo roda com `docker compose up` numa máquina com Docker, sem instalar dependências locais |
| RNF-02 | Configuração e segredos por variáveis de ambiente; `.env` fora do Git |
| RNF-03 | Testes automatizados rodam com um comando, contra um PostgreSQL real em contêiner |
| RNF-04 | Uploads salvos em volume, com nome gerado pela aplicação (nunca o nome enviado pelo usuário) |
| RNF-05 | Formulários protegidos contra envio malicioso (escape de HTML nas páginas, limite de tamanho no upload) |

## Notas de implementacao (T-0003)

- Tipo da imagem pelos bytes iniciais (JPEG `FFD8FF`, PNG, WebP `RIFF....WEBP`); SVG e recusado. ~~A imagem nao e reprocessada.~~ Desde a T-0010 a imagem e decodificada e regravada (ver "Regra da imagem" e "Notas de implementacao (T-0010)"); imagens gravadas antes dela nao foram reprocessadas.
- Limite de 2 MB: leitura limitada a 2 MB + 1 byte, com erro 422 na pagina (campos preservados). Teto anti-DoS separado: `Content-Length` acima de 10 MB recebe 413; POST sem `Content-Length` (chunked) recebe 411.

## Definido pela T-0006 (ADR-0002 e ADR-0003 aceitos em 2026-09-30)

Origem: SEC-0002 a SEC-0005, observacoes do VER-0006/VER-0007 e ADR-0002/ADR-0003 (aceitos pelo humano em 2026-09-30).

### Requisitos nao funcionais novos

| ID | Requisito (verificavel) | Origem | Cartao |
|---|---|---|---|
| RNF-06 | Toda dependencia Python (direta e indireta, runtime e dev) instalada com versao exata e hash sha256 (`pip install --require-hashes`); arquivos travados gerados por comando documentado | SEC-0003, ADR-0003 | T-0009 |
| RNF-07 | O processo da aplicacao (imagem runtime) roda com usuario sem privilegio: `id -u` diferente de 0 no container `app` | SEC-0004 | T-0008 |
| RNF-08 | Toda resposta HTTP da aplicacao (HTML, JSON, erro 4xx, arquivo de `/uploads`) leva `Content-Security-Policy` com `frame-ancestors 'none'`, `X-Frame-Options: DENY` e `X-Content-Type-Options: nosniff` | SEC-0005 | T-0007 |
| RNF-09 | A imagem runtime nao tem pacote do sistema com correcao de seguranca disponivel na data do build (`apt list --upgradable` sem pacote de seguranca), e a varredura da imagem (alem do `pip-audit`) tem comando documentado; CVE sem correcao fica registrada com triagem | SEC-0002 | T-0008 |
| RNF-10 | Os comandos documentados de `test`, `lint` e `audit` reconstroem a imagem antes de rodar (`run --build`), para nunca verificar codigo ou dependencias antigos | O1 (VER-0009/VER-0010) | T-0009 |

### Regra da imagem (ADR-0002, implementada na T-0010)

| Campo | Regra |
|---|---|
| Imagem | Opcional; JPEG, PNG ou WebP; ate 2 MB **enviados**; tipo pelos magic bytes **e** pela decodificacao completa (o formato decodificado tem de ser o mesmo); lado ate 10.000 px e area ate 50 megapixels; a aplicacao grava a imagem **regravada**, no mesmo formato, com a orientacao do EXIF aplicada e sem metadados; imagem animada vira o primeiro quadro |

Mensagens (422, na pagina, campos preservados), alem das atuais de tamanho e tipo. Entre aspas esta o texto literal da interface, com acentos, como as mensagens que ja existem em `app/imagens.py`:

- corrompida ou truncada: "A imagem está corrompida ou não pôde ser lida."
- dimensoes acima do limite: "A imagem deve ter no máximo 10.000 px de lado e 50 megapixels."

### Exemplos de entrada - imagem

O Revisor testa estes casos. Nenhum pode gerar erro 500.

| Entrada | Valido? | Resultado esperado |
|---|---|---|
| JPEG real 1200x800, ~300 KB | sim | 303; arquivo gravado abre como JPEG 1200x800 |
| PNG real 8x8 com transparencia | sim | 303; gravado como PNG com canal alfa |
| WebP real 64x64 | sim | 303; gravado como WebP |
| JPEG com EXIF `Orientation=6` e GPS | sim | 303; gravado ja girado (altura > largura se o original era retrato) e **sem** EXIF |
| PNG real com extensao `.jpg` no nome | sim | 303; gravado como `.png` (tipo pelo conteudo) |
| JPEG valido com `<script>...</script>` anexado depois do fim | sim | 303; o arquivo gravado **nao** contem a string `<script>` |
| Arquivo com exatamente 2 MB (imagem real) | sim | 303 |
| Campo vazio ou arquivo de 0 byte | sim (sem imagem) | 303 sem imagem, como hoje |
| `FFD8FF` + 1 KB de bytes aleatorios | nao | 422 "corrompida ou não pôde ser lida" |
| PNG real cortado pela metade | nao | 422 "corrompida ou não pôde ser lida" |
| PNG valido declarando 20.000 x 20.000 px (arquivo pequeno) | nao | 422 "no máximo 10.000 px...", sem decodificar os pixels (resposta rapida, memoria estavel) |
| Cabecalho `RIFF....WEBP` com corpo de PNG | nao | 422 (formato decodificado diferente do detectado) |
| GIF, SVG, PDF renomeado para `.jpg` | nao | 422 "A imagem deve ser JPEG, PNG ou WebP." (como hoje) |
| Imagem real de 3 MB | nao | 422 "no máximo 2 MB" com os campos preservados (como hoje) |
| Corpo acima de 10 MB / sem `Content-Length` | nao | 413 / 411 (teto anti-DoS, como hoje) |

### Decisoes do humano (T-0006, aceitas em 2026-09-30)

- Uso local, sem exposicao publica (como nas questoes em aberto). Exposicao publica mudaria a avaliacao do ADR-0002.
- Limite de dimensao: 10.000 px de lado e 50 megapixels (cobre camera de celular de 48 MP). Revisavel.
- Qualidade da regravacao: JPEG e WebP com qualidade 90; PNG sem perda. Revisavel.
- Perfil de cor ICC: mantido (nao identifica a pessoa e evita mudar as cores); reserializado com `ImageCms` (D1, 2026-10-01). Revisavel.
- Imagens gravadas antes da mudanca nao sao reprocessadas.
- A imagem `dev` (servicos `test`, `lint`, `audit`) continua como root: nao publica porta e so roda localmente (RNF-07 vale para a runtime).
- A CSP permite `style-src 'unsafe-inline'` enquanto o CSS estiver dentro de `index.html`; tirar o CSS para arquivo fica para uma tarefa de interface.
- Analise de ameacas da T-0012 (2026-10-01): 50 MP mantidos tambem para WebP, com semaforo (D2); JPEG MPF/MPO aceito como JPEG de 1 quadro (D3); fila cheia -> 503 "Servidor ocupado, tente de novo." (D4).

## Notas de implementacao (T-0010)

- `app/imagens.py`: `processar_imagem` valida tamanho e magic bytes, abre com `Image.open(io.BytesIO, formats=[JPEG, PNG, WEBP])`, confere o formato (MPO conta como JPEG) e as dimensoes (`LADO_MAXIMO`, `AREA_MAXIMA`) **antes** de `load()`, aplica `exif_transpose`, regrava sem metadados (comentario COM e texto PNG incluidos) e reserializa o ICC com `ImageCms` (descartado se invalido). Qualquer excecao do Pillow vira "corrompida"; `DecompressionBombError` vira a mensagem de dimensao (nunca 500).
- Concorrencia: no maximo `DECODIFICACOES_SIMULTANEAS` (2) por processo, espera de 30 s; estourada, 503 "Servidor ocupado, tente de novo." na pagina, campos preservados.
- Gravacao: temporario na pasta de uploads + `os.replace`; falha no commit remove o arquivo.

## Notas de implementacao (T-0007)

- RNF-08 (definicao na tabela "Definido pela T-0006"; valores exatos): toda resposta envia CSP (`default-src 'self'; img-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'`), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` e `Referrer-Policy: strict-origin-when-cross-origin`, por um middleware ASGI (`CabecalhosSeguranca` em `app/main.py`) que envolve o app inteiro (`AppComCabecalhos`), por fora do `ServerErrorMiddleware`, entao cobre tambem 411/413 e o 500 (SEC-0006).
- `'unsafe-inline'` so em `style-src`, porque o CSS esta num `<style>` do template; remover quando o CSS for para arquivo.

## Decisões

- **Fornecedor é texto livre** em cada produto (decidido por Igor em 2026-09-28). Um cadastro próprio de fornecedores pode vir depois, se necessário.

## Questões em aberto

- **Edição e exclusão** de produtos: fora do escopo inicial.
- **Autenticação:** fora do escopo inicial (uso local).
- (T-0006) **Acima de 10 MB** a resposta continua JSON 413 (VER-0007). Quer uma pagina amigavel nesse caso? Nao bloqueia.
- (T-0006) **Varredura da imagem automatizada** (servico do Compose) ou so comando documentado com o `osv-scanner` da maquina? A T-0008 assume o comando documentado. Nao bloqueia.
