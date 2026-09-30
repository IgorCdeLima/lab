# lab — cadastro de produtos

Landing page simples para cadastrar produtos com nome, valor, fornecedor e imagem.

Projeto laboratório da equipe de agentes 01_IA. Padrões em [CLAUDE.md](CLAUDE.md); requisitos em [docs/requisitos](docs/requisitos/requisitos.md).

## Como rodar

Requer apenas Docker com Compose.

```
docker compose up -d --build     # sobe app e db (o app espera o banco ficar saudável)
docker compose run --rm test      # testes (imagem propria com pytest, contra o PostgreSQL do Compose)
docker compose down              # para (NUNCA use down -v: apaga o banco)
```

- Aplicação: <http://localhost:8000> — saúde: <http://localhost:8000/health>
- Funciona sem `.env`, com valores padrão **somente para desenvolvimento local**. Para alterar, copie `.env.example` para `.env` (fora do Git).
