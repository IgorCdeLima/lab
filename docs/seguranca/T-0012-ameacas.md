---
tipo: analise-ameacas
tarefa: T-0012
alvo: T-0010 (ADR-0002, imagem decodificada e regravada com Pillow)
autor: seguranca
criado: 2026-10-01
commit_base: d9b37b1
pillow_avaliado: 12.3.0
tags: [seguranca, ameacas, upload, imagem, pillow, stride]
---
# T-0012 - Analise de ameacas da validacao de imagem com Pillow (T-0010)

## Escopo

Mudanca analisada: a T-0010 passa a **decodificar** a imagem enviada com o Pillow e a gravar no volume um arquivo **regravado pela aplicacao** (ADR-0002). A analise cobre o caminho `POST /produtos` (campo `imagem`) ate o arquivo servido em `/uploads/<32 hex>.<ext>`, a dependencia nova e a imagem Docker em que ela roda.

Base: `main` em `d9b37b1` (T-0008 e T-0009 ja integradas). Codigo atual relevante: `app/imagens.py` (magic bytes, `salvar`, `remover`) e `app/main.py` (`cadastrar`, middleware de teto 411/413, cabecalhos de seguranca).

Premissas aceitas pelo humano e **nao** revistas aqui (T-0006): uso local sem exposicao publica; lado ate 10.000 px e area ate 50 MP; JPEG/WebP com qualidade 90; ICC mantido; imagens antigas nao reprocessadas. Onde a analise mostrou risco numa premissa, ele vai como duvida para o humano (secao "Duvidas para o humano").

## Ativos

| Ativo | Por que importa |
|---|---|
| Disponibilidade do processo `app` (memoria, CPU, threads) | Um upload pequeno pode custar centenas de MB e dezenas de segundos de CPU (medido, E4). Sem limite no container, a pressao chega ao host e ao PostgreSQL |
| Integridade do processo `app` (uid 10001) | O Pillow decodifica dado nao confiavel em C; falha de memoria vira execucao de codigo como `app` |
| Arquivos do volume `uploads` | Sao servidos a quem abre a listagem; devem ser so o que a aplicacao gerou |
| Privacidade de quem envia a foto | EXIF com GPS, modelo do aparelho, comentarios e XMP |
| Coerencia banco x volume | Produto sem arquivo, ou arquivo sem produto, apos falha |
| Cadeia de dependencias | Pillow e as 18 bibliotecas nativas embutidas na wheel (E7) |

## Fronteiras de confianca e fluxo do arquivo

```mermaid
flowchart LR
    U([Navegador / cliente HTTP<br/>NAO confiavel]) -- multipart ate 10 MB --> MW
    subgraph C[Container app - uid 10001, sem limite de memoria/CPU hoje]
        MW[Middleware: 411 sem Content-Length,<br/>413 acima de 10 MB] --> H[Handler cadastrar<br/>le ate 2 MB + 1 byte]
        H --> MB[Magic bytes<br/>JPEG / PNG / WebP]
        MB --> OP[Pillow Image.open<br/>formats JPEG, PNG, WEBP<br/>so cabecalho]
        OP --> DIM{lado e area<br/>antes de load}
        DIM --> LD[load: decodifica pixels<br/>codigo C + libs nativas]
        LD --> RG[exif_transpose, 1o quadro,<br/>save sem metadados]
        RG --> W[Grava nome gerado<br/>32 hex + ext]
        W --> DB[(commit no PostgreSQL)]
    end
    W --> V[(Volume uploads)]
    V --> S[GET /uploads/nome<br/>Content-Type fixo, nosniff, CSP]
    S --> U2([Quem abre a listagem])
    classDef perigo fill:#fde2e2,stroke:#c0392b
    class LD,OP perigo
```

Fronteiras: (1) rede -> middleware; (2) bytes do usuario -> **parser em C do Pillow** (a fronteira mais critica: `OP` e `LD`); (3) processo -> volume e banco; (4) volume -> navegador de terceiros.

## Pontos de entrada

| Ponto | Dado controlado pelo atacante |
|---|---|
| `POST /produtos`, campo `imagem` | Ate 2 MB de bytes arbitrarios que passam pelos magic bytes; o nome e o `Content-Type` da parte sao ignorados (e devem continuar ignorados) |
| Metadados dentro do arquivo | EXIF, XMP, COM (JPEG), tEXt/iTXt/zTXt (PNG), ICC, MPF (JPEG multi-imagem), quadros extras (APNG, WebP animado) |
| Dimensao declarada | Lado e area declarados no cabecalho, independentes do tamanho em bytes |
| Requisicoes simultaneas | Sem autenticacao nem rate limit (uso local) |

## Evidencias medidas nesta analise

Todas em container `python:3.13.15-slim` (a base do `Dockerfile`) com `pip install pillow==12.3.0`, em 2026-10-01. Bibliotecas na wheel: libjpeg-turbo 3.1.4.1, libwebp 1.6.0, zlib 1.3.1, lcms2 2.19 (`PIL.features.version`).

| # | Experimento | Resultado |
|---|---|---|
| E1 | JPEG/PNG/WebP com EXIF (Orientation=6, Make, GPS), XMP, ICC, COM (JPEG) e tEXt/iTXt (PNG); `Image.open(formats=...)`, `load()`, `ImageOps.exif_transpose`, `save(formato)` **sem argumentos** | EXIF, XMP e tEXt/iTXt **somem** nos 3 formatos; rotacao aplicada (40x20 -> 20x40). **O comentario COM do JPEG sobrevive.** **O ICC sobrevive no PNG** (inclusive um ICC invalido de lixo) e **some** no JPEG e no WebP |
| E2 | ICC valido + `<script>` + 200 KB anexados, repassado com `save(icc_profile=im.info["icc_profile"])` | O `<script>` e os 200 KB chegam ao arquivo gravado. Reserializado com `ImageCms.ImageCmsProfile(...).tobytes()`, sai so o perfil (588 bytes), sem o anexo |
| E3 | `<script>` anexado depois do fim do JPEG/PNG/WebP | Abre normalmente; o arquivo regravado **nao** contem a string nos 3 formatos |
| E4 | Pior caso de 50 MP (7071 x 7071), cada um em processo novo | WebP RGBA de **89 KB**: pico **879 MB**, **26,4 s**. JPEG RGB de 764 KB: 400 MB, 1,7 s. PNG RGBA de 190 KB: 399 MB, 6,8 s. PNG 1 bit de 6 KB: 113 MB. PNG 8000 x 8000 (64 MP) recusado antes de `load()`: 52 ms e 17 MB |
| E5 | 1.800 arquivos mutados (troca de bytes, truncamento, insercao; 600 por formato) passando por open/load/transpose/save | Excecoes vistas: `OSError` (inclui `UnidentifiedImageError`) e **`SyntaxError`** (PNG). Varios JPEG/WebP mutados decodificam sem erro. Nenhuma outra classe nesta amostra |
| E6 | Hierarquia de excecoes | `UnidentifiedImageError` herda de `OSError`; **`DecompressionBombError` herda direto de `Exception`, nao de `OSError`** (um `except OSError` deixa passar e vira 500) |
| E7 | JPEG com varias imagens (MPF) gerado com `save("MPO", save_all=True)` | Magic bytes `FFD8FF` (passa como JPEG), mas `Image.open(..., formats=["JPEG"])` devolve `format == "MPO"`. Comparar `im.format == "JPEG"` recusa o arquivo. Salvo como `JPEG`, sai 1 quadro so |
| E8 | GIF, BMP, TIFF, ICO, PPM com `formats=["JPEG","PNG","WEBP"]` | `UnidentifiedImageError` em todos |
| E9 | APNG de 4 quadros e WebP animado de 2 quadros, regravados | Saem com 1 quadro |
| E10 | Amplificacao no disco | JPEG 48 MP q5 de 1,56 MB -> 3,36 MB em q90 (x2,2); WebP q1 de 1,92 MB -> 4,43 MB em q90 (x2,3) |
| E11 | `osv-scanner scan image --all-packages` (2.6.0) numa imagem com `pillow==12.3.0` | Ve `pillow 12.3.0` (PyPI) e os pacotes Debian, mas **nenhuma** das 18 bibliotecas de `site-packages/pillow.libs/` (libwebp, libjpeg, libpng16, liblcms2, libtiff, libopenjp2, libfreetype, libharfbuzz, libavif...) |

Fato volatil: Pillow 12.3.0 e a versao mais nova no PyPI em 2026-10-01 (`https://pypi.org/pypi/pillow/json`). A API do OSV (`https://api.osv.dev/v1/query`, PyPI/pillow) devolve **0 avisos** para 12.3.0 e 13 GHSA (+13 PYSEC) para 12.2.0, todos de 2026-07, corrigidos na 12.3.0. Desses, os que tocam o caminho da T-0010 sao GHSA-9hw9-ch79-4vh6 (escrita fora dos limites em `ImageCmsTransform.apply`) e GHSA-6r8x-57c9-28j4 (escrita fora dos limites em `paste`/`crop`); os demais estao em plugins que o `formats=` nao alcanca (fontes BDF/PCF, McIdas, EPS, PDF, GD, JPEG 2000, TGA) ou no visualizador do Windows.

## Ameacas, controles e como testar

Risco = probabilidade x impacto no cenario atual (uso local, sem autenticacao). "Exposicao publica" sobe todos os de disponibilidade.

| ID | STRIDE | CWE | Abuso concreto | Risco | Controle esperado | Como testar |
|---|---|---|---|---|---|---|
| A01 | D | CWE-409, CWE-400 | PNG 1 bit de 48 KB declarando 20.000 x 20.000 px (bomba de descompressao). Entre ~89 MP e ~179 MP o `open` so avisa; acima disso levanta `DecompressionBombError` no proprio `open` (BUG-0008) | Alto se faltar | Lado (10.000) e area (50 MP) checados logo apos `Image.open` e **antes** de `load()`/`exif_transpose`; `DecompressionBombError` tratado como dimensao acima do limite; `Image.MAX_IMAGE_PIXELS` nunca `None` | CS-01 |
| A02 | D | CWE-770, CWE-400 | 10 requisicoes simultaneas com o WebP RGBA 50 MP de 89 KB: ~8,8 GB e ~26 s de CPU cada (E4). O handler e `def` sincrono e roda no threadpool (ate 40 threads), sem limite de memoria no container | **Medio** (local); alto se exposto | Limite de decodificacoes simultaneas no processo (semaforo, constante nomeada); limite de memoria/CPU/pids no servico `app` (fora da T-0010: SEC-T0012-01) | CS-08; SEC-T0012-01 |
| A03 | T, E | CWE-434 | Arquivo com magic bytes aceitos mas que o Pillow abriria por outro plugin (TIFF, EPS, PDF, GD...), ampliando a superficie com plugins de historico ruim | Medio se faltar | `formats=["JPEG","PNG","WEBP"]` em **todo** `Image.open` (E8) | CS-03 |
| A04 | T | CWE-20 | `RIFF....WEBP` com corpo de PNG; JPEG multi-imagem (MPF) que abre como `MPO` (E7) | Baixo | Formato decodificado igual ao dos magic bytes, com `MPO` tratado como JPEG e regravado como JPEG de 1 quadro | CS-03, CS-04 |
| A05 | D, I | CWE-755, CWE-20 | Arquivo mutado/truncado levanta `SyntaxError` (PNG) ou `DecompressionBombError`, que nao herdam de `OSError` (E5, E6), e vira 500 | Medio | Toda chamada ao Pillow (open, load, transpose, save) dentro de um bloco que mapeia `DecompressionBombError` -> mensagem de dimensao e **qualquer outra `Exception`** -> "corrompida"; mensagem fixa, sem texto da excecao | CS-02 |
| A06 | I | CWE-212 | Foto de celular com GPS no EXIF, autor no XMP, texto no COM/tEXt servida na listagem | Medio | Gravar sem EXIF, XMP, COM e chunks de texto. Atencao: o `save` padrao **mantem o COM do JPEG** e **mantem o ICC no PNG** (E1) | CS-05 |
| A07 | T, I | CWE-434 | Poliglota: (a) conteudo anexado depois do fim; (b) conteudo dentro do COM ou do ICC (E1, E2); (c) PNG/WebP sem perda com pixels escolhidos para que o IDAT regravado contenha HTML | Baixo (mitigado por `nosniff`, tipo fixo e CSP da T-0007) | (a) regravacao (E3); (b) COM descartado e ICC reserializado ou descartado (duvida D1); (c) residual: manter `Content-Type` fixo, `nosniff` e CSP em `/uploads` | CS-05, CS-06, CS-07 |
| A08 | E | CWE-1395 | Versao do Pillow com aviso conhecido (13 GHSA na 12.2.0) | Medio se desatualizar | Versao mais nova no dia, travada com hash (T-0009), `pip-audit` limpo e consulta ao OSV registrada | CS-10 |
| A09 | E | CWE-1395 | CVE em libwebp/libjpeg/libpng/lcms2 embutida na wheel: nem o `pip-audit` nem o `osv-scanner` de imagem a enxergam (E11) | Baixo (hoje) | Registrar as versoes das libs na entrega; processo de acompanhamento (fora da T-0010: SEC-T0012-02) | CS-10; SEC-T0012-02 |
| A10 | E | CWE-787, CWE-250 | Falha de memoria ainda desconhecida num decodificador -> codigo executando como `app` | Baixo | Defesa em profundidade: usuario sem privilegio (T-0008, feito), `formats=` restrito, nada de `ImageCms` em transformacao (GHSA-9hw9), `no-new-privileges`/`cap_drop` (SEC-T0008-01, aberto) | CS-03, CS-06 (revisao) |
| A11 | T, D | CWE-459 | Erro entre gravar o arquivo e o commit deixa arquivo orfao; arquivo parcial se a escrita falhar no meio | Baixo | Gravar so depois de regravar tudo em memoria; escrita em arquivo temporario na mesma pasta + `os.replace`; falha no commit remove o arquivo (ja existe). Morte do processo (OOM) entre gravar e o commit deixa orfao: residual aceito | CS-09 |
| A12 | I | CWE-200 | Mensagem de erro com texto da excecao do Pillow (versao, caminho interno) | Baixo | Mensagens fixas do `requisitos.md` | CS-02 |
| A13 | D | CWE-400 | Uploads repetidos que regravados crescem ~2,3x (E10) enchem o volume | Baixo (local) | Residual: sem rate limit (uso local). Reavaliar se exposto | - |
| A14 | T | CWE-22 | Passar ao Pillow o nome enviado ou um caminho (`Image.open(caminho)`) | Baixo | Pillow so recebe `io.BytesIO(conteudo)`; o nome do cliente nunca e usado | CS-11 |
| A15 | D | CWE-400 | WebP/APNG animado com muitos quadros, se o codigo iterar ou chamar `seek` em todos | Baixo | So o quadro 0; nada de laco sobre quadros nem `save_all` | CS-04 (revisao) + E9 |

STRIDE sem ameaca nova nesta mudanca: **Spoofing** e **Repudiation** (nao ha autenticacao nem trilha de auditoria no projeto; questao em aberto do `requisitos.md`).

## T-0008 e T-0009 sao pre-requisito?

- **T-0009 (dependencias com hash): pre-requisito de seguranca.** O Pillow decodifica dado nao confiavel; entrar sem versao exata e hash repetiria o SEC-0003 com a dependencia de maior superficie do projeto. Ja concluida (merge `d362236`).
- **T-0008 (sem root): recomendacao forte, nao bloqueio.** Nao impede a falha do decodificador (A10), so limita o dano. Ja concluida (merge `d9b37b1`). O complemento `no-new-privileges` e `cap_drop: [ALL]` (SEC-T0008-01) continua recomendado e passa a **pre-requisito** se a aplicacao for exposta.

Nada bloqueia a T-0010 por esse lado.

## Criterios de aceite de seguranca propostos para a T-0010

Os testes geram as imagens com o proprio Pillow dentro do teste (nada de binario versionado), como ja pede a T-0010. "Via HTTP" = pelo `TestClient`, no `POST /produtos`.

- [ ] **CS-01 Dimensao antes de decodificar.** Constantes nomeadas em `app/imagens.py` (ex.: `LADO_MAXIMO = 10_000`, `AREA_MAXIMA = 50_000_000`); a checagem vem logo depois de `Image.open` e antes de `load()`/`exif_transpose`; `DecompressionBombError` vira a mensagem de dimensao; nenhum `Image.MAX_IMAGE_PIXELS = None` no codigo. **Teste:** via HTTP, PNG modo "1" de 20.000 x 20.000 px (~48 KB) -> 422 "no máximo 10.000 px de lado e 50 megapixels"; PNG 8.000 x 8.000 -> mesma mensagem; PNG 10.001 x 10 -> mesma mensagem; PNG 10.000 x 5.000 -> 303. Em teste unitario, um espiao em `ImageFile.ImageFile.load` (ou `monkeypatch`) prova que `load` **nao** e chamado nos tres casos recusados.
- [ ] **CS-02 Nenhuma excecao do Pillow vira 500 nem vaza texto.** As chamadas ao Pillow (open, load, transpose, save) ficam num bloco que trata `DecompressionBombError` como dimensao e **qualquer outra `Exception`** como "A imagem está corrompida ou não pôde ser lida." (nao basta `except OSError`: E5 e E6). **Teste:** teste parametrizado via HTTP com pelo menos 300 arquivos mutados com semente fixa (troca de bytes, truncamento e insercao, sobre JPEG, PNG e WebP validos) -> status sempre 303 ou 422; um caso explicito que levante `SyntaxError` (PNG com CRC de chunk quebrado ou equivalente) -> 422 "corrompida"; a pagina de erro nao contem `Error`, `Traceback` nem `PIL`.
- [ ] **CS-03 Decodificadores restritos e formato coerente.** Todo `Image.open` usa `formats=["JPEG", "PNG", "WEBP"]` (conferir com `grep` na revisao); o formato aberto tem de bater com o dos magic bytes (`MPO` conta como JPEG); nenhum uso de `ImageCms.buildTransform`, `profileToProfile` ou `applyTransform`. **Teste:** `RIFF....WEBP` + corpo de PNG -> 422; teste unitario da funcao de validacao com bytes de TIFF, GIF e BMP -> recusados sem chamar `load`.
- [ ] **CS-04 JPEG multi-imagem e animados.** JPEG com MPF vira JPEG de 1 quadro; APNG e WebP animado viram 1 quadro; o codigo nao itera quadros. **Teste:** via HTTP, arquivo gerado com `save(..., "MPO", save_all=True, append_images=[...])` -> 303, arquivo gravado reabre com `format == "JPEG"` e sem `n_frames > 1`; APNG de 4 quadros e WebP animado de 2 quadros -> gravados com 1 quadro.
- [ ] **CS-05 Sem metadados no arquivo gravado.** Sem EXIF, XMP, comentario JPEG (COM) e chunks de texto PNG. Como o `save` padrao mantem o COM (E1), o codigo tem de remove-lo explicitamente (`comment=b""` ou retirar `comment` de `im.info`). **Teste:** para cada formato, gerar no teste um arquivo com EXIF (com GPS e `Make`), XMP, COM (JPEG) e tEXt/iTXt (PNG), cada um com um marcador unico (ex.: `MARCADOR-GPS-T0010`); apos o upload, os bytes do arquivo gravado **nao** contem nenhum marcador, `getexif()` vem vazio e `info` nao tem `exif`, `xmp`, `comment`.
- [ ] **CS-06 Perfil ICC tratado igual nos tres formatos (D1).** O ICC so e mantido se `ImageCms.ImageCmsProfile(io.BytesIO(icc))` o ler, e entao e gravado o resultado de `.tobytes()` (sem bytes anexados, E2); ICC invalido e descartado; nos tres formatos (o PNG mantem o ICC por padrao e o JPEG/WebP o descartam por padrao, E1). **Teste:** ICC sRGB valido -> mantido (`info["icc_profile"]` presente) em JPEG, PNG e WebP; ICC sRGB + `<script>` anexado -> arquivo gravado sem `<script>`; ICC de bytes aleatorios -> gravado sem ICC e com 303.
- [ ] **CS-07 Poliglota e servico do arquivo.** **Teste:** JPEG, PNG e WebP validos com `<script>alert(1)</script>` anexado -> 303 e o arquivo gravado nao contem `<script>` (a T-0010 pede so o JPEG; estender aos tres). `GET /uploads/<nome>` do arquivo gravado continua com `Content-Type` da extensao gerada, `X-Content-Type-Options: nosniff` e a CSP do RNF-08 (teste de regressao).
- [ ] **CS-08 Concorrencia limitada.** No maximo N decodificacoes simultaneas por processo (constante nomeada, sugestao `DECODIFICACOES_SIMULTANEAS = 2`), com espera limitada (ex.: 30 s); estourada a espera, 503 com a mensagem "Servidor ocupado, tente de novo." na pagina e campos preservados (D4). **Teste:** teste unitario com o semaforo ocupado e espera curta -> a requisicao nao chama o Pillow e recebe 503 com essa mensagem e os campos preservados. **Teste manual registrado no VER:** 10 requisicoes simultaneas (`curl` em paralelo) com o WebP RGBA 7071 x 7071 (~89 KB) -> nenhum 500 e pico de memoria do container `app` (`docker stats --no-stream` em laco) abaixo de 2 GB.
- [ ] **CS-09 Gravacao segura.** O arquivo so e escrito depois de regravado por completo em memoria; escrita em arquivo temporario na pasta de uploads seguida de `os.replace` para o nome final; falha no commit remove o arquivo (ja existe). **Teste:** com `monkeypatch` fazendo a escrita levantar `OSError` -> nenhum arquivo (nem temporario) sobra no volume; com o commit falhando -> o arquivo regravado e removido; com imagem recusada (422) -> nenhum arquivo novo no volume.
- [ ] **CS-10 Dependencia conferida no dia.** `pillow` na versao mais nova do PyPI no dia, com hash; `pip-audit` limpo; a Entrega registra a consulta ao OSV da versao instalada (data e numero de avisos) e as versoes de `PIL.features.version("libjpeg_turbo")`, `"webp"`, `"zlib"` e `"littlecms2"` na imagem runtime (insumo do SEC-T0012-02).
- [ ] **CS-11 Pillow so recebe bytes.** `Image.open` so com `io.BytesIO(conteudo)`; o nome e o `content_type` enviados pelo cliente nunca chegam ao Pillow nem ao nome gravado (conferir com `grep` na revisao); o nome gravado continua `[0-9a-f]{32}\.(jpg|png|webp)`.

## Duvidas para o humano (premissas aceitas, risco encontrado)

**Decisao do humano (2026-10-01): D1 a D4 aprovadas na opcao recomendada** (ICC reserializado com `ImageCms` e descartado se invalido; 50 MP mantidos com o semaforo; MPO aceito como JPEG de 1 quadro; 503 com mensagem e campos preservados quando a fila estoura).

- **D1 - ICC mantido.** O ICC e um bloco de bytes do usuario: repassado como veio, leva conteudo anexado ate o arquivo servido (E2). Opcoes: (a) **reserializar com `ImageCms` e descartar se invalido** (recomendado; o parse usa a lcms2 da wheel, mas sem transformacao de cor, fora do GHSA-9hw9); (b) manter os bytes crus com limite de tamanho (risco aceito: poliglota no ICC, mitigado por `nosniff`); (c) descartar o ICC (cores de fotos Display P3 mudam um pouco).
- **D2 - 50 MP em WebP.** Um WebP de 89 KB com 50 MP custa 879 MB e 26 s de CPU (E4). Com o CS-08 o pico fica limitado, mas cada upload desses ocupa uma vaga do semaforo por ~26 s. Manter os 50 MP (recomendado no uso local) ou reduzir so para WebP?
- **D3 - JPEG multi-imagem (MPF/MPO).** Fotos de celular com HDR embutido costumam levar MPF (nao conferido com foto real). Recomendado: aceitar como JPEG e gravar so a imagem principal. A alternativa e recusar com a mensagem de corrompida, o que confundiria o usuario.
- **D4 - Fila cheia.** Estourada a espera do CS-08: (a) 503 com mensagem na pagina "Servidor ocupado, tente de novo." e campos preservados (recomendado; texto novo de interface); ou (b) so esperar, sem tempo maximo (mais simples, prende threads do servidor).

## Achados fora da T-0010

- **SEC-T0012-01** (baixa): servico `app` sem limite de memoria, CPU e pids no `docker-compose.yml`; com a T-0010, um upload de 89 KB custa 879 MB.
- **SEC-T0012-02** (baixa): as 18 bibliotecas nativas embutidas na wheel do Pillow ficam fora do `pip-audit` e do `osv-scanner` de imagem.
- Ja registrado e ainda aberto: SEC-T0008-01 (`no-new-privileges`, `cap_drop`), relevante para A10.

## Riscos residuais aceitos nesta analise

- Poliglota construido nos pixels de PNG/WebP sem perda (A07c): mitigado por `Content-Type` fixo, `nosniff` e CSP, nao eliminado.
- Arquivo orfao se o processo morrer entre gravar e o commit (A11).
- Volume crescendo ~2,3x por upload regravado e sem rate limit (A13), no uso local.
- Falha de memoria desconhecida no decodificador (A10): limitada por usuario sem privilegio e `formats=`.

## NAO verificado

- Comportamento com fotos reais de celular (MPF/Ultra HDR, CMYK de camera, HEIC renomeado): so arquivos gerados pelo Pillow.
- JPEG progressivo com muitas varreduras (custo de CPU do libjpeg-turbo) e PNG com milhares de chunks: nao medidos.
- Avisos de seguranca das bibliotecas nativas nas versoes embutidas (libwebp 1.6.0, libjpeg-turbo 3.1.4.1, lcms2 2.19 etc.): sem fonte que mapeie wheel -> CVE (pedido ao Pesquisador no SEARCH-0003).
- `pip-audit` no arquivo travado com Pillow: o Pillow ainda nao esta no `requirements.txt`; a consulta foi feita direto na API do OSV.
- Fuzz amplo (o E5 e uma amostra de 1.800 mutacoes, nao prova ausencia de outras classes de excecao).

## Fontes

- OSV.dev, API `v1/query` PyPI/pillow 12.2.0 e 12.3.0, consultada em 2026-10-01; pagina do aviso: https://osv.dev/vulnerability/GHSA-9hw9-ch79-4vh6
- PyPI, https://pypi.org/pypi/pillow/json, consultado em 2026-10-01 (12.3.0, wheel cp313 manylinux x86_64 de 2026-07-01).
- MITRE CWE, consultadas em 2026-10-01: CWE-409 (https://cwe.mitre.org/data/definitions/409.html), CWE-400, CWE-212, CWE-459, CWE-755, CWE-1395.
- Brain: [[Fontes de referencia para analise de seguranca por CWE e dependencias]], [[CWE-434 upload sem restricao exige validar o tipo pelo conteudo e servir por nome gerado]] (OWASP File Upload Cheat Sheet), [[CWE-770 recursos sem limite se evitam com limite de corpo, timeout e rate limit]] (OWASP Denial of Service Cheat Sheet), [[Pillow Image.open ja recusa imagem acima do dobro de MAX_IMAGE_PIXELS antes da checagem de dimensao do projeto]], [[Checklist de entradas extremas precisa de itens proprios para upload]], pista do Inbox [[Regravar imagem sem EXIF exige aplicar a orientacao antes]] (a rotacao com `exif_transpose` foi confirmada no E1).
- Projeto: ADR-0002, `docs/avaliacoes/validacao-da-imagem.md`, `docs/requisitos/requisitos.md`, `docs/modelos/modelos.md`, BUG-0008, SEC-0003, SEC-0004, SEC-T0008-01.
- Experimentos E1 a E11: executados pela Seguranca em 2026-10-01 (secao "Evidencias medidas").
