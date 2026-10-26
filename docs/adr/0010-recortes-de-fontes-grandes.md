# 0010 — Recortes de fontes grandes / Extracts of large sources

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
O ADR 0002 manda commitar os dados brutos enquanto cada fonte tiver menos de 5 MB. O V-Dem
publica um único arquivo de cerca de 16 MB compactado (200 MB descompactado) com todos os
países desde 1789, do qual usamos poucas colunas de poucos países.

### Decisão
Para fontes acima do limite, o snapshot guarda:
- um **recorte determinístico** do arquivo original: só as geografias cobertas, só as
  colunas do catálogo, só os anos a partir de 1975, com os valores copiados como texto e
  as linhas ordenadas;
- um `upstream.json` com a URL, o nome do arquivo dentro do pacote, o tamanho e o sha256
  do arquivo original, e o filtro aplicado.

Qualquer pessoa pode baixar o original, conferir o hash e reproduzir o recorte com a função
`extract` do conector. O CI reconstrói tudo a partir do recorte commitado.

### Consequências
- O repositório fica pequeno e o build continua offline.
- Se a fonte trocar o arquivo sem mudar a URL, o hash registrado mostra a diferença.
- Adicionar um país ou indicador exige nova coleta, porque o recorte só tem o que o
  catálogo pedia na data da coleta.

### Alternativas consideradas
- Commitar o arquivo original: 16 MB por coleta semanal incha o histórico do Git.
- Anexar o original às Releases do GitHub: possível no futuro; por ora o hash e a URL
  versionada da fonte bastam para reproduzir.

## English

### Decision
For sources above the size limit, the snapshot keeps a **deterministic extract** (covered
geographies, catalog columns, years from 1975, values copied as text, sorted rows) and an
`upstream.json` with the original file's URL, archive member, size, sha256 and the filter.
Anyone can download the original, check the hash and re-derive the extract with the
connector's `extract` function. CI rebuilds everything from the committed extract.

### Consequences
Small repository and offline builds; a changed upstream file under the same URL shows up
in the hash; adding a country or indicator requires a new collection.

### Alternatives considered
Committing the original (16 MB per weekly collection bloats Git history); attaching it to
GitHub Releases (possible later).
