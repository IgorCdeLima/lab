---
tipo: design-brief
status: rascunho
tarefa: T-0011
criado: 2026-09-30
---
# Brief de design - Cadastro de produtos (lab)

## Objetivo da tela

Cadastrar um produto (nome, valor, fornecedor e imagem opcional) em poucos segundos, sem erro de formato, e conferir logo abaixo/ao lado que ele entrou na lista.

## Publico e contexto de uso

- Quem cadastra produtos no proprio computador (uso local, sem login). Pessoa de operacao/comercio, nao necessariamente tecnica.
- Uso principal no desktop (teclado + mouse, cadastro em sequencia de varios itens). Uso secundario no celular (cadastrar com foto tirada na hora, consultar a lista).
- Familiaridade: repete a tarefa muitas vezes; quer velocidade, previsibilidade e erro facil de corrigir. Nao quer ler instrucao.

## Conteudo real

Tela unica, renderizada no servidor (Jinja2), titulo "Cadastro de produtos".

Formulario (POST `/produtos`, `multipart/form-data`, `novalidate`):

| Campo | Rotulo atual | Regra | Dica a mostrar |
|---|---|---|---|
| Nome | Nome | obrigatorio, 1 a 120 caracteres | - |
| Valor | Valor (R$) | obrigatorio, > 0, 2 casas, ate 99.999.999,99, formato pt-BR | exemplo `1234,56` |
| Fornecedor | Fornecedor | obrigatorio, 1 a 120 caracteres, texto livre | - |
| Imagem | Imagem (opcional) | JPEG, PNG ou WebP, ate 2 MB | "JPEG, PNG ou WebP, ate 2 MB" |

Botao: "Cadastrar".

Mensagens de erro (texto literal da interface; o design so muda a apresentacao):

- Nome: "Informe o nome." / "O nome deve ter no máximo 120 caracteres." / "O nome contém caracteres inválidos."
- Valor: "Informe o valor." / "Valor inválido. Use o formato 1234,56 (até duas casas decimais)." / "O valor deve ser maior que zero." / "O valor máximo é R$ 99.999.999,99."
- Fornecedor: "Informe o fornecedor." / "O fornecedor deve ter no máximo 120 caracteres." / "O fornecedor contém caracteres inválidos."
- Imagem: "A imagem deve ter no máximo 2 MB." / "A imagem deve ser JPEG, PNG ou WebP." e, com a T-0010, "A imagem está corrompida ou não pôde ser lida." / "A imagem deve ter no máximo 10.000 px de lado e 50 megapixels."
- Apos erro (422) os campos de texto voltam preenchidos; o arquivo **nao** volta (limitacao do navegador): o design precisa avisar que a imagem tem de ser escolhida de novo.

Listagem (mais recente primeiro): miniatura (ou "sem imagem"), nome, fornecedor, valor formatado `R$ 1.234,56`. Estado vazio: "Nenhum produto cadastrado."

Dados realistas para os prototipos: "Cafe torrado em graos 1 kg" / Torrefacao Serra Azul / R$ 54,90; "Caixa organizadora de polipropileno com tampa e travas laterais, 56 litros, transparente" (nome longo) / Plasticos Ipiranga Ltda. / R$ 89,90; "Geladeira frost free inox 480 L" / Eletro Distribuidora Sul / R$ 4.799,00; "Lote de notebooks corporativos" / Tech Atacado / R$ 99.999.999,99 (valor maximo).

## Estados

| Estado | Como aparece hoje | O que o design precisa resolver |
|---|---|---|
| Lista vazia | paragrafo simples | convite a cadastrar o primeiro produto |
| Lista com produtos | tabela | com e sem imagem, nome longo, valor alto |
| Erro por campo | paragrafo vermelho abaixo do campo | campo marcado, mensagem ligada ao campo (`aria-describedby`), resumo no topo do form |
| Erro de imagem | idem | e aviso de que o arquivo precisa ser escolhido de novo |
| Sucesso | nao existe (redirect 303 para `/`) | hoje nao ha mensagem; proposta: destacar o produto recem-cadastrado (topo da lista). Uma mensagem "Produto cadastrado" exigiria mudanca no servidor (parametro na URL ou sessao): fica como opcao para o humano/Dev decidir |

## Tom e personalidade

Sobrio, rapido, confiavel. Ferramenta de trabalho, nao vitrine de marketing. (Os conceitos exploram variacoes desse tom.)

## Restricoes

- Acessibilidade: contraste AA (texto 4.5:1, componentes e foco 3:1), foco visivel, rotulos visiveis em todos os campos, erro associado ao campo, alvo de toque >= 44 px no celular, nada so por cor.
- Sistema de design existente: nenhum ainda (esta tarefa cria `docs/design/sistema/tokens.css`).
- Tecnica: paginas geradas no servidor (FastAPI + Jinja2), sem framework JavaScript; a tela precisa funcionar sem JavaScript.
- CSP (T-0007, RNF-08): `default-src 'self'; img-src 'self'; style-src 'self' 'unsafe-inline'`. **Sem fonte, icone, imagem ou script de outra origem**: fontes do sistema; icones em SVG inline ou caracteres. O CSS deve poder ir para arquivo (`tokens.css` + folha da tela) para depois remover `'unsafe-inline'`. `img-src 'self'` tambem barra `data:` em CSS/HTML: nada de imagem em data URI no produto final.
- Fora do escopo: edicao, exclusao, busca, paginacao, autenticacao.

## Referencias

Sem referencia externa (nenhuma pesquisa pedida). Inspiracao em padroes conhecidos: formulario de cadastro rapido de ERP/PDV, catalogo em cartoes de loja, livro-caixa/planilha. Evitar: excesso de decoracao, placeholders no lugar de rotulos, modais.

## Perguntas ao humano

- Qual direcao (A, B ou C, ou mistura)?
- Quer mensagem de sucesso explicita ("Produto cadastrado") mesmo exigindo mudanca pequena no servidor? (Sem ela, o destaque do item novo na lista faz esse papel.)

## Direcoes exploradas

| Conceito | Ideia central | Arquivo |
|---|---|---|
| A | **Bancada**: duas colunas no desktop, formulario fixo a esquerda e tabela densa a direita; neutro claro com azul-petroleo; foco em cadastro em sequencia | 02-conceito-A.svg |
| B | **Vitrine**: a imagem manda; produtos em cartoes grandes em grade, formulario como painel "Novo produto" no topo com area de soltar a foto; tons quentes (creme e terracota) | 02-conceito-B.svg |
| C | **Livro-caixa**: coluna unica escura de alto contraste, campos em linha tipo ficha, lista como livro de registros com valores em fonte monoespacada alinhados e contagem de itens; verde-menta sobre grafite | 02-conceito-C.svg |

Contraste conferido (WCAG, calculado) nas combinacoes principais de cada conceito, todas AA:

| Conceito | Texto principal | Texto secundario | Erro | Botao | Borda do campo (3:1) |
|---|---|---|---|---|---|
| A | 13,7:1 | 5,4:1 | 6,5:1 | 7,2:1 | 3,0:1 (no limite; no prototipo escurecer um pouco) |
| B | - | 6,3:1 | 7,9:1 | 5,4:1 | 4,2:1 |
| C | - | 7,3:1 | 7,0:1 | 11,8:1 | 3,3:1 |

Observacoes para a escolha:

- O selo "novo"/destaque do item recem-cadastrado (A, B e C) precisa de um ajuste pequeno no servidor: o redirect 303 apontar para a ancora do produto (ex.: `/#produto-12`) e o CSS usar `:target`. Sem isso, o item novo so aparece no topo, sem destaque.
- B depende de fotos boas: com muitos produtos sem imagem, a vitrine fica repetitiva. A e C funcionam bem com ou sem imagem.
- C e escuro por padrao; uma variante clara sai dos mesmos tokens se o humano quiser.
- E possivel misturar (ex.: estrutura de A com a lista em cartoes de B no celular).

**Escolha do humano:** <!-- preenchida depois -->
