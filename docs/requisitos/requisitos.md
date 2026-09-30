---
tipo: requisitos
status: rascunho
versao: 1
atualizado: 2026-09-28
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
| Imagem | Opcional; JPEG, PNG ou WebP; até 2 MB; tipo validado pelo conteúdo, não só pela extensão |

## Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF-01 | Tudo roda com `docker compose up` numa máquina com Docker, sem instalar dependências locais |
| RNF-02 | Configuração e segredos por variáveis de ambiente; `.env` fora do Git |
| RNF-03 | Testes automatizados rodam com um comando, contra um PostgreSQL real em contêiner |
| RNF-04 | Uploads salvos em volume, com nome gerado pela aplicação (nunca o nome enviado pelo usuário) |
| RNF-05 | Formulários protegidos contra envio malicioso (escape de HTML nas páginas, limite de tamanho no upload) |

## Notas de implementacao (T-0003)

- Tipo da imagem pelos bytes iniciais (JPEG `FFD8FF`, PNG, WebP `RIFF....WEBP`); SVG e recusado. A imagem nao e reprocessada.
- Limite de 2 MB: leitura limitada a 2 MB + 1 byte, com erro 422 na pagina (campos preservados). Teto anti-DoS separado: `Content-Length` acima de 10 MB recebe 413; POST sem `Content-Length` (chunked) recebe 411.

## Notas de implementacao (T-0007)

- RNF-08: toda resposta envia CSP (`default-src 'self'; img-src 'self'; style-src 'self' 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'`), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` e `Referrer-Policy: strict-origin-when-cross-origin`, por um middleware ASGI (`CabecalhosSeguranca` em `app/main.py`) que envolve o app inteiro (`AppComCabecalhos`), por fora do `ServerErrorMiddleware`, entao cobre tambem 411/413 e o 500 (SEC-0006).
- `'unsafe-inline'` so em `style-src`, porque o CSS esta num `<style>` do template; remover quando o CSS for para arquivo.

## Decisões

- **Fornecedor é texto livre** em cada produto (decidido por Igor em 2026-09-28). Um cadastro próprio de fornecedores pode vir depois, se necessário.

## Questões em aberto

- **Edição e exclusão** de produtos: fora do escopo inicial.
- **Autenticação:** fora do escopo inicial (uso local).
