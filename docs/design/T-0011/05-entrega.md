---
tipo: design-entrega
tarefa: T-0011
direcao: estrutura do conceito A + produtos em carrossel (escolha do humano, 2026-09-30)
criado: 2026-09-30
---
# Entrega ao Dev - tela de cadastro de produtos

Texto entre aspas e texto literal da interface (com acentos, como em `requisitos.md`).

A fonte de verdade da interface e o **prototipo** `04-prototipo.html` + os **tokens** `docs/design/sistema/tokens.css`. Os conceitos (`02-*.svg`) sao so inspiracao; o esqueleto (`03-esqueleto.svg`) mostra grade e medidas.

Abrir o prototipo: direto no navegador (arquivo local, sem servidor e sem rede). A barra rosa no topo navega entre os estados; ela e os rotulos rosa **nao** vao para o app.

## 1. Arquivos e CSP

| No prototipo | No app | Observacao |
|---|---|---|
| bloco `TOKENS` do `<style>` | `/static/tokens.css` (copia de `docs/design/sistema/tokens.css`) | mudanca de token: primeiro no `docs/design/sistema/`, depois no app |
| bloco `TELA` do `<style>` | `/static/cadastro.css` | |
| bloco `PROTOTIPO` do `<style>` | nao vai | |
| `<script>` no fim | `/static/carrossel.js` com `defer` | melhoria opcional; a tela funciona sem ele |
| `<symbol>` de icones | SVG inline no template (ou `/static/icones.svg` com `<use href="/static/icones.svg#i-erro">`) | sem fonte de icones, sem CDN |
| fotos ficticias `f-*` | `<img src="/uploads/{{ p.imagem_arquivo }}">` | nao usar `data:` (barrado por `img-src 'self'`) |

- O app ainda nao serve `/static`: montar `StaticFiles` (FastAPI) numa pasta `app/static/`. Os cabecalhos de seguranca da T-0007 ja cobrem toda resposta.
- Com CSS e JS em arquivo, o template fica **sem `<style>` e sem `style=""`**, o que permite tirar `'unsafe-inline'` de `style-src` (decisao da Seguranca/Dev; nao e escopo do design). Atencao: o atributo `hidden` e permitido (nao e estilo inline).
- Fontes: so do sistema (`--fonte-base`). Nenhuma fonte baixada.

## 2. Estrutura da pagina (ordem do DOM = ordem visual)

```
header.cabecalho
  .cabecalho__conteudo: svg.cabecalho__marca (aria-hidden) | h1 "Cadastro de produtos" | p.cabecalho__contagem
main.pagina  (grid: 340px | 1fr no desktop; pilha abaixo de 960px)
  section.painel.cartao-form (aria-labelledby -> h2 "Novo produto")
    p.painel__sub "Todos os campos são obrigatórios, exceto a imagem."
    form (method post, action /produtos, multipart, novalidate)
      [div.resumo-erros role=alert]            so com erro
      div.campo  Nome
      div.campo  Valor (campo-prefixo "R$")
      div.campo  Fornecedor
      div.campo  Imagem (div.campo-arquivo)
      button.botao-primario "Cadastrar"
  section.painel.produtos (aria-labelledby -> h2 "Produtos", data-carrossel)
    .produtos__topo: h2 + p.painel__sub "Mais recentes primeiro" | div.carrossel-nav[hidden]
    div.carrossel#carrossel (role=region, aria-label, tabindex=0)
      ul.carrossel__lista > li.cartao ...
    -- ou, sem produtos: div.vazio
```

## 3. Componentes

| Componente | Classe | Regras |
|---|---|---|
| Cabecalho | `.cabecalho` | fundo `--cor-superficie`, borda inferior; contagem: "N produtos" / "1 produto"; sem produtos, nao mostrar a contagem |
| Painel | `.painel` | superficie, borda `--cor-borda`, raio `--raio-md`, padding `--esp-5` (`--esp-4` no celular) |
| Campo de texto | `.campo` + `label` + `input` | rotulo visivel sempre acima (nunca placeholder como rotulo); altura 44 px (48 no celular); fonte 16 px; borda `--cor-borda-campo` |
| Campo com prefixo | `.campo-prefixo` | "R$" visual com `aria-hidden`; o rotulo ganha `<span class="sr-only"> em reais</span>`; `inputmode="decimal"`; dica "Ex.: 1234,56" ligada por `aria-describedby` |
| Campo de arquivo | `.campo-arquivo` | `input type=file` nativo, botao estilizado por `::file-selector-button`; `accept="image/jpeg,image/png,image/webp"`; dica de formatos por `aria-describedby` |
| Mensagem de erro | `.msg-erro` | icone (aria-hidden) + texto; cor `--cor-erro`; logo abaixo do campo; **texto literal** do servidor |
| Resumo de erros | `.resumo-erros` | topo do form, `role="alert"`; titulo "Corrija os campos marcados para cadastrar." e um link por erro: `<a href="#{campo}">{Rotulo}: {mensagem}</a>` |
| Botao primario | `.botao-primario` | largura total da coluna; hover `--cor-acento-forte`; texto "Cadastrar" |
| Carrossel | `.carrossel` + `.carrossel__lista` | rolagem horizontal nativa com `scroll-snap-type: x mandatory`; cartoes de 196 a 240 px (3 visiveis + borda do 4o) no desktop, 45% no tablet, 78% no celular; **sem rotacao automatica**; barra de rolagem visivel |
| Navegacao do carrossel | `.carrossel-nav` + `.botao-circulo` | renderizada com `hidden`; o `carrossel.js` mostra quando ha mais cartoes do que cabem; botoes desativados nas pontas; escondida no celular (arrasta com o dedo); `aria-label` "Produtos anteriores" / "Próximos produtos", `aria-controls` |
| Cartao de produto | `li.cartao` | foto 1:1 (`object-fit: cover`), `h3.cartao__nome` (2 linhas, `line-clamp`; texto completo no DOM), fornecedor (1 linha com reticencias + `title` com o texto todo), valor (`tabular-nums`, nunca quebra, cor acento) |
| Sem imagem | `.cartao__foto--vazia` | mesmo quadro 1:1, borda tracejada, icone + "sem imagem" |
| Estado vazio | `.vazio` | icone + "Nenhum produto cadastrado." (texto atual) + "Preencha o formulário para cadastrar o primeiro." |

## 4. Estados e o que o template faz em cada um

| Estado | Prototipo | Template |
|---|---|---|
| Lista com produtos | Estado 1 | carrossel com um `li.cartao` por produto, mais recente primeiro (como hoje) |
| Lista vazia | Estado 2 | `div.vazio` no lugar do carrossel; sem contagem |
| Erro em campo de texto (422) | Estado 3 | por campo com erro: `aria-invalid="true"`, `aria-describedby="{campo}-erro ..."`, `p.msg-erro#{campo}-erro`; resumo no topo; valores preservados (`value="{{ valores.x }}"`, como hoje); `autofocus` **so no primeiro** campo com erro (ordem: nome, valor, fornecedor, imagem) |
| Qualquer erro com o campo de imagem sem erro | Estado 3 | no `.campo-arquivo`, dica extra "Se você tinha escolhido uma imagem, escolha de novo." (o navegador nao devolve o arquivo apos o 422) |
| Erro de imagem | Estado 4 | `.campo-arquivo--erro`, `aria-invalid` no input, `msg-erro` + dica "Escolha outro arquivo, ou cadastre sem imagem. JPEG, PNG ou WebP, até 2 MB." |
| Todas as mensagens | "Todas as mensagens" | texto literal de `app/validacao.py` e `app/imagens.py` (+ 2 da T-0010); **nao mudar** |
| Sucesso | Estado 1 | redirect 303 para `/` (como hoje); o produto novo entra como **primeiro cartao** do carrossel, **sem destaque** nem mensagem (decisao do humano, secao 5) |

Textos novos de interface (so apresentacao, sem regra): "Novo produto", "Todos os campos são obrigatórios, exceto a imagem.", "Ex.: 1234,56", "Mais recentes primeiro", "Corrija os campos marcados para cadastrar.", "Se você tinha escolhido uma imagem, escolha de novo.", "Escolha outro arquivo, ou cadastre sem imagem.", "Preencha o formulário para cadastrar o primeiro.", "sem imagem", contagem "N produtos".

## 5. Produto recem-cadastrado: sem destaque

Decisao do humano (2026-09-30): nao destacar o produto novo. Ele so entra no carrossel como primeiro cartao (lista do mais recente para o mais antigo, como hoje). Nada muda no servidor: o redirect 303 continua para `/`. Nao usar selo, `:target`, ancora nem mensagem de sucesso.

## 6. Responsivo

| Largura | Layout |
|---|---|
| >= 960 px | duas colunas (form 340 px fixo e `sticky` com `top: 24px`; produtos `1fr`), largura maxima 1200 px, margens 32 px |
| 720 a 959 px | pilha (form, depois produtos), largura maxima 640 px centrada; form sem `sticky`; cartao 45% |
| < 720 px | pilha, margens 16 px; campos e botao com 48 px; cartao 78%; sem botoes anterior/proximo |

Sem rolagem horizontal da pagina em 320 px (so o carrossel rola na horizontal).

## 7. Acessibilidade (requisitos verificaveis)

- Contraste AA conferido (WCAG 2.1, calculado):

| Par | Razao | Minimo |
|---|---|---|
| `--cor-texto` / superficie | 15,7:1 | 4,5 |
| `--cor-texto-2` / superficie e fundo | 7,6 / 7,0:1 | 4,5 |
| `--cor-texto-3` / superficie e fundo | 5,8 / 5,4:1 | 4,5 |
| branco / `--cor-acento` (botao) | 7,2:1 | 4,5 |
| `--cor-erro` / superficie | 6,5:1 | 4,5 |
| `--cor-erro` / `--cor-erro-suave` (resumo) | 5,7:1 | 4,5 |
| `--cor-texto-3` / `--cor-superficie-2` ("sem imagem") | 5,1:1 | 4,5 |
| `--cor-borda-campo` / superficie (borda de campo) | 4,3:1 | 3 |

- Foco visivel em todo elemento interativo: contorno 3 px `--foco-cor`, afastamento 2 px (`:focus-visible`); em campo com erro o contorno fica `--cor-erro`. Nunca `outline: none` sem substituto.
- Todo campo com `<label for>` visivel; "(opcional)" faz parte do rotulo da imagem.
- Erro ligado ao campo: `aria-invalid="true"` + `aria-describedby` apontando para a `msg-erro`; erro nunca so por cor (icone + texto + borda grossa).
- Resumo de erros com `role="alert"` e links para os campos.
- Carrossel: `role="region"`, `aria-label="Lista de produtos, role para o lado"`, `tabindex="0"` (rola com as setas do teclado); a lista e `<ul>`/`<li>`; cada produto tem `<h3>`; nada some ou gira sozinho; `prefers-reduced-motion` desliga a rolagem suave.
- Imagem do produto: `alt="Imagem de {{ p.nome }}"` (como hoje). Icones decorativos com `aria-hidden="true"`.
- Alvos de toque >= 44 px (48 no celular). Fonte 16 px nos campos (sem zoom automatico no iOS).
- `lang="pt-BR"` mantido; um unico `h1`.

## 8. Limites conhecidos

- Com dezenas de produtos o carrossel fica longo para percorrer; "ver todos", busca ou paginacao ficam para outra tarefa.
- O texto "Nenhum arquivo escolhido" do input de arquivo e do navegador (pode aparecer cortado em coluna estreita); nao e estilizavel sem JavaScript.
- Pagina amigavel para 413/411 (corpo acima de 10 MB) esta fora deste design (questao em aberto da T-0006).

## 9. Proposta de cartao de implementacao (o Coordenador cria)

**Titulo:** Implementar a tela de cadastro com o design da T-0011. `papel: dev`, `interface: sim`, `seguranca: sim` (CSS/JS em arquivo, rota `/static`). Depois da T-0007 (ja na `main`) e, de preferencia, depois da T-0010 (mesmo template, mensagens novas).

Criterios de aceite verificaveis:

- [ ] `app/templates/index.html` reproduz a estrutura da secao 2 e os estados da secao 4; sem `<style>` nem `style=""` no template.
- [ ] `/static/tokens.css` identico a `docs/design/sistema/tokens.css`; `/static/cadastro.css` com o bloco TELA do prototipo; `/static/carrossel.js` com `defer`.
- [ ] Nenhum recurso de outra origem (conferir a aba Rede: todas as requisicoes para a propria origem) e nenhum erro de CSP no console.
- [ ] Sem JavaScript (desativado no navegador): cadastro, erros e carrossel funcionam (carrossel rola com mouse/teclado/toque; botoes anterior/proximo nao aparecem).
- [ ] Desktop 1280 px: duas colunas, form `sticky`, 3 cartoes visiveis + borda do 4o; celular 360 px: pilha, sem rolagem horizontal da pagina, cartao com borda do proximo.
- [ ] Erro em cada campo: `aria-invalid`, `aria-describedby`, `msg-erro` com o texto literal, resumo no topo com links, valores preservados, `autofocus` no primeiro campo com erro, dica de reenvio da imagem.
- [ ] Produto sem imagem, nome com 120 caracteres, fornecedor com 120 caracteres e valor `R$ 99.999.999,99` nao quebram o cartao.
- [ ] Estado vazio com "Nenhum produto cadastrado." (teste atual continua passando).
- [ ] Contagem "1 produto" / "N produtos" no cabecalho.
- [ ] Apos cadastrar, o produto novo e o primeiro cartao do carrossel, sem destaque; redirect continua 303 para `/`.
- [ ] Testes automatizados para: elementos de acessibilidade do erro (`aria-invalid`, `aria-describedby`), dica de reenvio, contagem, ordem do carrossel (mais recente primeiro), ausencia de `<style>` no HTML, `/static/*.css` servido com os cabecalhos de seguranca.
- [ ] Revisao visual do Designer (porta 8200 + N) antes do Revisor fechar.
