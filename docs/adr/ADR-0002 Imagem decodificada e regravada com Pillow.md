---
tipo: decisao
status: proposta
decidido_em:
decidido_por:
substituida_por:
criado: 2026-09-30
tags: [lab, upload, imagem, seguranca, dependencias]
---
# ADR-0002 Imagem decodificada e regravada com Pillow

## Contexto

Na T-0003 a imagem do produto passou a ser validada so pelos bytes iniciais (magic bytes) e gravada como veio. O VER-0006 mostrou que um arquivo com cabecalho JPEG seguido de lixo e um poliglota JPEG + HTML sao aceitos. O risco de execucao no navegador esta mitigado (`Content-Type` fixo e `nosniff`), mas:

- o arquivo gravado e servido e conteudo arbitrario do usuario;
- arquivo corrompido aparece como imagem quebrada, sem mensagem;
- metadados da foto (EXIF, inclusive GPS de celular) sao servidos a quem abre a listagem.

O humano adiou a decisao de decodificar/reprocessar (Pillow, dependencia nova) para a T-0006. Avaliacao completa: `docs/avaliacoes/validacao-da-imagem.md` (C 76, A 69, B 53).

## Decisao

**Proposta:** decodificar a imagem enviada com o Pillow e gravar um arquivo **regravado pela aplicacao**, no mesmo formato detectado:

1. Manter a checagem atual de tamanho (2 MB) e de magic bytes, que e barata e da a mensagem de tipo.
2. Abrir com o Pillow restrito a JPEG, PNG e WebP; conferir que o formato decodificado e o mesmo dos magic bytes.
3. Recusar dimensoes acima do limite **antes** de decodificar os pixels (premissa: lado ate 10.000 px e area ate 50 megapixels).
4. Decodificar por completo; arquivo truncado ou corrompido vira erro de validacao 422 na pagina, com os campos preservados.
5. Aplicar a orientacao do EXIF nos pixels e gravar sem metadados (EXIF, XMP, comentarios). So o primeiro quadro de imagem animada e mantido.
6. O Pillow entra **so depois** do travamento de dependencias com hash (ADR-0003, T-0009) e fica sujeito ao `pip-audit`.

Implementacao: cartao T-0010.

## Alternativas consideradas

| Alternativa | Pros | Contras |
|---|---|---|
| A - Manter so o cabecalho (status quo, risco aceito) | Nenhuma dependencia nova; mais simples e rapido | Conteudo arbitrario no volume; EXIF/GPS servido; imagem corrompida aparece quebrada |
| B - Pillow so para validar, gravando os bytes originais | Recusa arquivo corrompido com mensagem | Paga toda a superficie de decodificacao e mantem poliglota e metadados no arquivo gravado |
| C - Pillow para decodificar e regravar (escolhida) | Arquivo gravado gerado pela aplicacao; sem metadados; corrompido recusado; orientacao correta | Dependencia nova com historico de avisos (16 GHSA em 20/07/2026, corrigidos na 12.3.0); mais CPU/memoria; JPEG regravado perde um pouco de qualidade; animacao perdida |

## Consequencias

- **Positivas:** fecha a observacao do VER-0006/VER-0007; alinha o projeto a [[CWE-434 upload sem restricao exige validar o tipo pelo conteudo e servir por nome gerado]] ("tentar abrir/reprocessar com biblioteca de imagem"); remove dado pessoal (GPS) da listagem.
- **Negativas / riscos:**
  - O Pillow decodifica dado nao confiavel em C. Mitigacoes: `formats=` restrito, limite de pixels, versao travada com hash e auditada, container sem root (T-0008).
  - Atualizacao rapida do Pillow passa a ser rotina (o `pip-audit` acusa; o Dev regenera o arquivo travado).
  - Imagens ja gravadas antes da mudanca continuam como estao (sem migracao retroativa; premissa).
  - Regra de validacao da imagem em `docs/requisitos/requisitos.md` muda (ver secao "Proposto pela T-0006").
- **Se o humano rejeitar:** vale a alternativa A com o risco aceito e registrado; o cartao T-0010 e cancelado e as observacoes do VER-0006/VER-0007 ficam encerradas como "risco aceito".

## Relacionadas

- `docs/avaliacoes/validacao-da-imagem.md`
- ADR-0003 Dependencias travadas com hash via pip-tools
- [[Upload de imagem valida tipo por magic bytes e serve por nome gerado]]
- VER-0006, VER-0007 (observacoes)
