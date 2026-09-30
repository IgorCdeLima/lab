---
tipo: modelos
status: rascunho
atualizado: 2026-09-28
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
