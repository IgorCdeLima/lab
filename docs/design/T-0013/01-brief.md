---
tipo: design-brief
status: aprovado
tarefa: T-0013
criado: 2026-10-03
---
# Brief de design - Complemento da tela de cadastro (T-0013)

Complemento do design da T-0011 (`docs/design/T-0011/`). Nao e uma tela nova: a direcao visual ja foi escolhida pelo humano na T-0011 ("estrutura do conceito A + produtos em carrossel", 2026-09-30) e continua valendo. Esta tarefa acrescenta os estados que surgiram depois do merge `ec69b02` e prepara o prototipo para o Dev copiar sem adaptar (CSS e JS em arquivos, CSP sem `'unsafe-inline'`).

## Objetivo da tela

O mesmo da T-0011: cadastrar um produto (nome, valor, fornecedor e imagem opcional) em poucos segundos e conferir que ele entrou na lista. Novo nesta tarefa: quando o banco ou o servidor falham, a pessoa entende o que aconteceu, nao perde o que digitou e sabe que basta tentar de novo.

## Publico e contexto de uso

Igual a T-0011 (secao "Publico" do brief da T-0011): uso local, desktop principal, celular secundario, cadastro repetido. As falhas novas sao raras e passageiras (banco reiniciando, servidor ocupado com imagens grandes); a pessoa nao e tecnica e nao deve ver jargao alem do texto que o servidor ja usa.

## Conteudo real

Tudo da T-0011 continua. Estados novos (texto literal do servidor, **nao muda**):

| Situacao | Resposta | Texto literal | Origem |
|---|---|---|---|
| Banco fora ao abrir a pagina (`GET /`) | 503, `aviso` | "Banco de dados indisponivel no momento. Tente de novo em instantes." | `app/main.py`, `AVISO_BANCO` (sem acento no codigo; nao mudar) |
| Banco fora ao cadastrar (`POST /produtos`) | 503, `erros["banco"]` | mesmo texto | `app/main.py`, `cadastrar` |
| Servidor ocupado ao processar a imagem | 503, `erros["imagem"]` | "Servidor ocupado, tente de novo." | `app/imagens.py`, `ERRO_OCUPADO` |
| Imagem corrompida (T-0010) | 422, `erros["imagem"]` | "A imagem está corrompida ou não pôde ser lida." | `app/imagens.py`, `ERRO_CORROMPIDA` |
| Imagem grande demais em pixels (T-0010) | 422, `erros["imagem"]` | "A imagem deve ter no máximo 10.000 px de lado e 50 megapixels." | `app/imagens.py`, `ERRO_DIMENSAO` |

Observacao de comportamento: no `POST` com banco fora, `_pagina` tambem tenta listar os produtos; em geral a lista falha junto e o `aviso` tambem vem preenchido. O design trata as duas combinacoes.

Correcoes herdadas da revisao da T-0011:
- BUG-0009: no Estado 3, o fornecedor de exemplo passa a ter 131 caracteres (provoca de fato "O fornecedor deve ter no máximo 120 caracteres.").
- VER-0016, O1: o sprite de icones deixa de usar `style=""` (classe `.sprite` no CSS).
- VER-0016, O3: rotulo do Estado 2 alinhado com a entrega (sem contagem).
- VER-0016, O4: todo fornecedor ganha `title` com o texto completo (nao so os longos).
- VER-0016, O5: comentario do `tokens.css` corrigido para 5,7:1.

## Tom e personalidade

O mesmo da T-0011: sobrio, claro, confiavel. Nas falhas: calmo e objetivo (falha passageira, nada se perdeu, tente de novo), sem alarme visual alem do necessario.

## Restricoes

- Acessibilidade: contraste AA, foco visivel, rotulos nos campos, mensagens de erro claras; aviso de banco com `role="alert"`.
- Sistema de design existente: `docs/design/sistema/tokens.css` (T-0011). Nenhum token novo: os estados novos usam `--cor-erro`, `--cor-erro-suave`, `--cor-texto-*`.
- Tecnica: paginas geradas no servidor (Jinja2), sem framework JavaScript; a tela funciona sem JS. **CSP sem `'unsafe-inline'`:** nenhum `<style>`, `style=""`, `<script>` inline nem atributo `on*=` no HTML; CSS e JS em arquivos da propria origem.
- Nao mudar regra de negocio nem texto das mensagens do servidor. Nao alterar `docs/design/T-0011/`.

## Referencias

- `docs/design/T-0011/04-prototipo.html` e `05-entrega.md` (base).
- `[[CSP default-src self bloqueia o style inline dos templates]]` (por que o CSS sai do HTML).

## Perguntas ao humano

- Nenhuma antes de desenhar: direcao visual ja escolhida na T-0011. A unica decisao e aprovar (ou pedir ajuste) do prototipo completo no fim da fase 1.

## Direcoes exploradas

Sem conceitos novos nesta tarefa (etapa 1 do fluxo dispensada): o cartao pede o **complemento** do prototipo na direcao ja aprovada. Explorar outra direcao contrariaria a decisao da T-0011 e o objetivo do cartao ("o humano ve como a tela vai ficar"). O esqueleto da T-0011 (`03-esqueleto.svg`) continua valendo; os blocos novos (aviso, quadro indisponivel) estao anotados no prototipo e na entrega.

| Conceito | Ideia central | Arquivo |
|---|---|---|
| (T-0011) A + carrossel | form fixo a esquerda, produtos em carrossel de cartoes | `docs/design/T-0011/` |

**Escolha do humano:** direcao da T-0011 (2026-09-30). Aprovacao do prototipo da T-0013: <!-- preenchida pelo humano -->
