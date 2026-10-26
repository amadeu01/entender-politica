# 0002 — Formato comum dos dados / Common data format

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
Cada fonte (Banco Mundial, PNUD, IBGE/SIDRA, Ipeadata, ...) publica em formato próprio.
Para comparar séries, rastrear a origem de cada número e verificar citações, tudo precisa
chegar a um formato único.

### Decisão
Formato longo: **uma observação por linha**, com as colunas:

| Coluna | Tipo | Descrição |
|---|---|---|
| `geo_code` | texto | ISO 3166-1 alfa-3 para países (`BRA`), código IBGE para UF/município, códigos de agregados do Banco Mundial (`LCN`) |
| `geo_level` | texto | `country`, `aggregate`, `state`, `municipality` |
| `year` | inteiro | ano de referência |
| `indicator_id` | texto | identificador do catálogo, `<fonte>.<código>` (ex.: `wdi.si_pov_gini`) |
| `value` | decimal | valor |
| `lower`, `upper` | decimal, opcional | limites do intervalo quando a fonte publica incerteza |
| `unit` | texto | unidade (ex.: `index_0_100`, `percent`, `usd_2021_ppp`) |
| `source_id` | texto | fonte (`wdi`, `undp_hdr`, `ibge_sidra`, `ipeadata`) |
| `source_version` | texto | versão ou data de atualização publicada pela fonte |
| `retrieved_at` | data e hora (UTC) | quando foi coletado |
| `license` | texto | identificador SPDX ou URL da licença |
| `series_break` | booleano | `true` se a metodologia da série muda a partir deste ano |

Os dados brutos ficam em `data/raw/<fonte>/<data-da-coleta>/` com um `manifest.json`
(URL, sha256, data, licença, versão). Os normalizados em `data/processed/` como Parquet
e CSV.

Enquanto cada fonte tiver menos de 5 MB, os brutos são commitados. Acima disso, vale o
[ADR 0010](0010-recortes-de-fontes-grandes.md): um recorte determinístico mais o hash do
arquivo original.

### Consequências
- Qualquer número no site é rastreável até uma linha, e daí até um arquivo bruto com hash.
- Revisões feitas pelas fontes em séries antigas ficam visíveis no changelog de dados.
- O formato longo é verboso, mas o volume é pequeno (dezenas de indicadores × ~45 anos ×
  dezenas de países).

## English

### Context
Each source publishes in its own format. Comparing series, tracing each number back to its
origin and checking citations require a single format.

### Decision
Long format, **one observation per row**, with the columns in the table above: `geo_code`
(ISO3, IBGE code or World Bank aggregate code), `geo_level`, `year`, `indicator_id`
(`<source>.<code>`), `value`, optional `lower`/`upper`, `unit`, `source_id`,
`source_version`, `retrieved_at` (UTC), `license` and `series_break`.

Raw data goes to `data/raw/<source>/<collection-date>/` with a `manifest.json` (URL,
sha256, date, license, version); normalized data to `data/processed/` as Parquet and CSV.
Raw files are committed while each source is under 5 MB; beyond that, ADR 0010 applies
(a deterministic extract plus the original file's hash).

### Consequences
Every number on the site traces to one row and from there to a hashed raw file. Upstream
revisions of past values show up in the data changelog. The long format is verbose but
the data volume is small.
