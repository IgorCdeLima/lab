---
tipo: modelos
status: rascunho
atualizado: 2026-09-30
---
# Modelos

## Contexto (C4 nível 1)

```mermaid
flowchart LR
    U([Usuário]) -->|navegador| APP[Aplicação lab<br/>FastAPI]
    APP -->|SQL| DB[(PostgreSQL)]
    APP -->|arquivos| VOL[/Volume de uploads/]
```

## Containers (Docker Compose)

```mermaid
flowchart LR
    subgraph compose[docker compose]
        app[app<br/>Python + FastAPI] --> db[(db<br/>PostgreSQL)]
        app --> up[/volume uploads/]
        db --> dados[/volume dados/]
    end
    navegador([Navegador]) -->|HTTP| app
```

## Dados (ER)

Fornecedor como texto livre (decisão registrada nos requisitos). Tabela `produto` criada por `Base.metadata.create_all` na inicialização (T-0002); a coluna `imagem_arquivo` (T-0003) e adicionada na inicializacao com `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, pois `create_all` nao altera tabela existente. Imagens ficam no volume `uploads` (`UPLOADS_DIR=/uploads`) e sao servidas em `/uploads/<nome>` so para nomes no formato gerado (32 hex + jpg/png/webp). Testes usam o banco separado `<POSTGRES_DB>_test`, com rollback por teste.

```mermaid
erDiagram
    PRODUTO {
        int id PK
        varchar nome "1-120"
        numeric valor "NUMERIC(10,2) > 0"
        varchar fornecedor "1-120"
        varchar imagem_arquivo "nome gerado, opcional"
        timestamptz criado_em
    }
```

## Fluxo de cadastro

```mermaid
sequenceDiagram
    actor U as Usuário
    participant A as App
    participant D as PostgreSQL
    participant V as Volume
    U->>A: envia formulário (nome, valor, fornecedor, imagem)
    A->>A: valida campos e tipo real da imagem
    alt inválido
        A-->>U: página com erros de validação
    else válido
        A->>V: salva imagem com nome gerado
        A->>D: INSERT produto
        A-->>U: redireciona para a listagem
    end
```

## Em que ordem a imagem e validada e o que chega ao volume? (proposta ADR-0002, T-0010)

So vale se o ADR-0002 for aceito. Responde: qual verificacao recusa cada caso dos "Exemplos de entrada - imagem" (requisitos) e em que ponto os pixels sao decodificados. O teto anti-DoS (411/413) continua antes de tudo, no middleware.

```mermaid
sequenceDiagram
    actor U as Usuario
    participant A as App (handler)
    participant P as Pillow
    participant V as Volume uploads
    U->>A: POST /produtos (multipart, imagem)
    A->>A: le ate 2 MB + 1 byte
    alt mais de 2 MB
        A-->>U: 422 "no máximo 2 MB" (campos preservados)
    else magic bytes nao sao JPEG/PNG/WebP
        A-->>U: 422 "deve ser JPEG, PNG ou WebP"
    else cabecalho aceito
        A->>P: abrir so o cabecalho (formats JPEG, PNG, WEBP)
        alt formato decodificado diferente do detectado, ou nao abre
            P-->>A: erro
            A-->>U: 422 "corrompida ou não pôde ser lida"
        else dimensoes acima do limite (antes de decodificar pixels)
            A-->>U: 422 "no máximo 10.000 px ... 50 megapixels"
        else dimensoes ok
            A->>P: decodificar todos os pixels
            alt truncada ou corrompida
                P-->>A: erro
                A-->>U: 422 "corrompida ou não pôde ser lida"
            else decodificou
                A->>P: aplicar orientacao EXIF, 1o quadro, regravar sem metadados
                P-->>A: bytes regravados
                A->>V: grava bytes regravados com nome gerado
                A-->>U: 303 para a listagem
            end
        end
    end
```

## Em que ordem executar os cartoes da T-0006?

Responde: o que depende de que. Setas = "deve vir antes". Os cartoes sem seta entre si podem rodar em paralelo (worktrees separados).

```mermaid
flowchart LR
    ADR3{{ADR-0003 aceito}} --> T9[T-0009<br/>dependencias travadas<br/>+ roteiro O1]
    ADR2{{ADR-0002 aceito}} --> T10[T-0010<br/>imagem com Pillow]
    T9 --> T10
    T8[T-0008<br/>imagem sem root<br/>+ openssl + varredura] -.recomendado.-> T10
    T9 -. mesmo Dockerfile, fazer em sequencia .- T8
    T7[T-0007<br/>cabecalhos HTTP]
```
