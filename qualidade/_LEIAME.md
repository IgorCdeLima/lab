# qualidade — catálogo do projeto lab

- `verificacoes/` — `VER-####`: o que foi checado, por quem, em qual commit, com qual resultado (incluindo o que **não** foi verificado).
- `bugs/` — `BUG-####`: um arquivo por defeito.
- `seguranca/` — `SEC-####`: achados de segurança. **Nunca registrar segredos.**

Templates: `D:\01_IA\BRAIN\99_Sistema\Templates\Qualidade`.

**Escrevem:** revisor, segurança, coordenador (e o humano). **Demais agentes: somente leitura** — protegido pelo hook do Git.
Antes de alterar um arquivo, consulte os bugs abertos relacionados a ele.
