---
tipo: design-entrega
tarefa: T-0013
base: docs/design/T-0011/05-entrega.md (merge ec69b02)
direcao: estrutura do conceito A + produtos em carrossel (T-0011, escolha do humano em 2026-09-30)
criado: 2026-10-03
---
# Entrega ao Dev - complemento da tela de cadastro (T-0013)

So o que muda em relacao a `docs/design/T-0011/05-entrega.md`. **O resto da entrega da T-0011 continua valendo** (secoes 2, 3, 5, 6, 7 e 8; a secao 1 e substituida pela secao 1 abaixo; a secao 4 ganha as linhas da secao 3 abaixo).

Texto entre aspas e texto literal da interface (com acentos; as mensagens do servidor exatamente como estao no codigo, inclusive "indisponivel" sem acento).

Fonte de verdade: `04-prototipo.html` + `static/cadastro.css` + `static/carrossel.js` desta pasta + `docs/design/sistema/tokens.css`. Abrir o prototipo: direto no navegador (arquivo local) ou servindo `docs/design/` com `python3 -m http.server`. A barra rosa, os rotulos rosa e a tabela "Referencia" sao do prototipo (`static/prototipo.css`) e **nao** vao para o app. Capturas de referencia em `capturas/desktop-1280.png` e `capturas/celular-360.png`.

## 1. Arquivos e CSP (substitui a secao 1 da T-0011)

| No prototipo | No app | Observacao |
|---|---|---|
| `../sistema/tokens.css` | `app/static/tokens.css` -> `/static/tokens.css` | copia identica de `docs/design/sistema/tokens.css` |
| `static/cadastro.css` | `app/static/cadastro.css` -> `/static/cadastro.css` | copia identica |
| `static/carrossel.js` | `app/static/carrossel.js` -> `<script src="/static/carrossel.js" defer>` | copia identica; melhoria opcional, a tela funciona sem JS |
| `static/prototipo.css` | nao vai | |
| `<svg class="sprite">` com os `<symbol>` | SVG inline no template, com a classe `.sprite` | sem `style=""` (VER-0016, O1); os atributos de apresentacao do SVG (`fill`, `stroke`, `transform`) **nao** sao estilo inline e passam pela CSP |
| fotos `f-*` (SVG) | `<img src="/uploads/{{ p.imagem_arquivo }}" alt="Imagem de {{ p.nome }}">` | so do prototipo |
| ids com sufixo (`nome-1`, `nome-3`...) | `nome`, `valor`, `fornecedor`, `imagem`, `carrossel` | varios estados na mesma pagina so no prototipo |

Ordem no `<head>`: `tokens.css`, `cadastro.css`, depois o `<script ... defer>`.

O HTML do prototipo **nao tem** `<style>`, `style=""`, `<script>` inline nem atributo `on*=` (conferido por busca no arquivo). Com o mesmo HTML no template, a CSP pode ficar `style-src 'self'; script-src 'self'` sem `'unsafe-inline'`. O atributo `hidden` e permitido.

Diferenca de CSS em relacao ao bloco TELA da T-0011 (todas marcadas "T-0013" no arquivo):
- `.sprite` (novo, substitui o `style="position:absolute"` do sprite).
- `.cabecalho__contagem`: `margin: 0 0 0 auto` (antes so `margin-left`; zera a margem padrao do `<p>`).
- `.aviso`, `.aviso__texto` (novo, secao 2).
- `.resumo-erros__msg` (novo, secao 2).
- `.indisponivel`, `.indisponivel__titulo`, `.indisponivel__texto` (novo, mesmas regras do `.vazio`).
- Celular: padding menor em `.vazio`/`.indisponivel`.

Nenhum token novo. `tokens.css` so teve o comentario do contraste do resumo corrigido para 5,7:1 (VER-0016, O5).

## 2. Componentes novos

| Componente | Classe | Regras |
|---|---|---|
| Aviso da pagina | `div.aviso[role=alert]` | primeiro filho de `main.pagina`, ocupa as duas colunas (`grid-column: 1 / -1`); icone `#i-erro` (aria-hidden) + `p.aviso__texto` com o texto literal do `aviso`; fundo `--cor-erro-suave`, borda esquerda 4 px `--cor-erro`, texto `--cor-texto` |
| Lista indisponivel | `div.indisponivel` | no lugar do carrossel/estado vazio quando ha `aviso`; icone `#i-banco-fora` + "Lista indisponível no momento." + "Os produtos voltam a aparecer aqui quando o banco de dados responder. Recarregue a página em instantes." |
| Resumo sem campo | `div.resumo-erros[role=alert]` com `h3` "Não foi possível cadastrar.", `p.resumo-erros__msg` (texto literal de `erros.banco`) e `p` "Os dados digitados foram mantidos." | sem lista e sem link (nao ha campo a corrigir) |
| Icone banco fora | `<symbol id="i-banco-fora">` | novo no sprite |

## 3. Estados novos (acrescentar a secao 4 da T-0011)

| Estado | Prototipo | Template |
|---|---|---|
| Banco fora ao abrir (`GET /` 503, `aviso`) | Estado 6 | `div.aviso` no topo de `main`; painel Produtos so com `h2` + `div.indisponivel` (sem "Mais recentes primeiro", sem carrossel e **sem** "Nenhum produto cadastrado."); **sem** contagem no cabecalho; formulario normal |
| Banco fora ao cadastrar (`POST` 503, `erros.banco`) | Estado 7 | resumo sem campo (secao 2); nenhum campo com `aria-invalid`; valores preservados; dica de reenvio da imagem (regra da T-0011: qualquer erro com a imagem sem erro). Se o `aviso` tambem vier (lista falhou junto, caso comum): painel com `div.indisponivel`, mas **sem** `div.aviso` no topo (um so `role="alert"`, a frase ja esta no resumo). Se a lista carregar: carrossel normal |
| Servidor ocupado (`POST` 503, `erros.imagem` = `ERRO_OCUPADO`) | Estado 5 | igual ao Estado 4 (`.campo-arquivo--erro`, `aria-invalid`, `msg-erro`, resumo com link `#imagem`), mas a dica e "Escolha a mesma imagem de novo e envie em instantes, ou cadastre sem imagem." (o arquivo nao tem problema). Comparar com `imagens.ERRO_OCUPADO` (passar a constante ao template ou um booleano), nunca com texto copiado |
| Imagem corrompida / pixels demais (422, T-0010) | Estado 4 (rotulo) e Referencia | igual ao Estado 4, com a dica "Escolha outro arquivo, ou cadastre sem imagem. JPEG, PNG ou WebP, até 2 MB." |
| Erro de campo **e** `aviso` (422 com a lista falhando) | (combinacao, nao desenhada a parte) | mostra os dois: `div.aviso` no topo e o resumo de erros do formulario; painel com `div.indisponivel` |

Logica resumida para o template (ordem):

```
mostrar_aviso_topo = aviso and not erros.banco
painel_produtos    = indisponivel se aviso; senao carrossel se produtos; senao vazio
contagem           = so se nao aviso e produtos
resumo             = "Nao foi possivel cadastrar." se erros.banco (sem lista)
                     senao "Corrija os campos marcados para cadastrar." + links, se erros
```

Textos novos de interface (so apresentacao, sem regra): "Não foi possível cadastrar.", "Os dados digitados foram mantidos.", "Lista indisponível no momento.", "Os produtos voltam a aparecer aqui quando o banco de dados responder. Recarregue a página em instantes.", "Escolha a mesma imagem de novo e envie em instantes, ou cadastre sem imagem.". As mensagens do servidor **nao mudam**.

## 4. Correcoes herdadas da revisao da T-0011

- **BUG-0009:** no Estado 3 o fornecedor de exemplo tem 131 caracteres ("Distribuidora Nacional de Eletrodomésticos, Eletroportáteis e Utilidades para o Lar do Sul e Sudeste Ltda. ME - Filial Porto Alegre"; conferido com `len()`), e provoca de fato "O fornecedor deve ter no máximo 120 caracteres.". Um teste que copie esse dado recebe 422.
- **O1:** sprite com `.sprite` (secao 1).
- **O2:** vale o prototipo (`li.cartao`, `section.painel.cartao-form`), nao a anotacao do esqueleto.
- **O3:** sem contagem no estado vazio (rotulo do Estado 2 corrigido).
- **O4:** todo `p.cartao__fornecedor` tem `title="{{ p.fornecedor }}"`, curto ou longo.
- **O5:** comentario do `tokens.css` corrigido (5,7:1).
- **O6:** "3 cartoes + borda do 4o" vale a 1280 px; entre 960 e 1100 px cabem ~2,6 cartoes (comportamento esperado, nao defeito).

## 5. Acessibilidade (acrescenta a secao 7 da T-0011)

- `div.aviso` e o resumo usam `role="alert"`; nunca dois alertas com a mesma frase na mesma resposta.
- O aviso e o resumo nunca dependem so da cor: icone + texto + borda.
- Contraste dos pares novos (WCAG 2.1, mesmos tokens ja conferidos): `--cor-texto` sobre `--cor-erro-suave` 13,7:1; `--cor-erro` sobre `--cor-erro-suave` 5,7:1; `--cor-texto-2` sobre `--cor-erro-suave` 6,6:1; `--cor-texto-2` sobre `--cor-fundo` 7,0:1 (texto do quadro indisponivel).
- No Estado 7 nenhum campo recebe `autofocus` (nao ha campo com erro): o foco fica no inicio da pagina e o `role="alert"` anuncia o resumo. No Estado 5 o `autofocus` vai para o campo imagem (primeiro campo com erro).

## 6. Conferido no prototipo (Designer, 2026-10-03)

- Chrome headless servindo `docs/design/` por HTTP: CSS e JS carregados dos arquivos, carrossel com botoes no desktop (JS rodou).
- 1280 px: duas colunas, aviso do Estado 6 na largura toda, 3 cartoes + borda do 4o.
- 360 px (iframe, ver `[[Chrome headless nao serve para medir celular nem carrossel com rolagem suave]]`): sem rolagem horizontal da pagina (`scrollWidth` 345 com barra de 15 px), cartao com 78%, botoes do carrossel escondidos, campos com 48 px.
- Busca no HTML: nenhum `<style>`, `style=""`, `<script>` inline ou `on*=`; nenhum id duplicado; todo `aria-describedby`/`aria-controls`/ancora aponta para um id existente.
- **Nao conferido:** a pagina com o cabecalho CSP real (o Designer nao pode escrever o servidor de teste fora de `docs/design/`): fica para o Dev e para a revisao visual (console sem violacao de CSP). Leitor de tela real: nao testado.
