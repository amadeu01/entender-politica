# 0013 — Educação por governo / Education by government

- **Status:** aceito / accepted
- **Data / Date:** 2026-11-01

## pt-BR

### Contexto
Queremos mostrar, para cada período de governo, o que começou na educação, o que foi
cortado ou limitado e as séries que podem ter relação, sem sugerir que o governo causou a
mudança (ADR 0003). O ambiente de desenvolvimento não alcança o Crossref nem o Planalto,
então DOIs novos não podem ser verificados (ADR 0007) e os textos oficiais não foram lidos.

### Decisão
1. **Um arquivo por período** em `education/governos/<id-do-período>.yaml`
   (`pipeline/compilador/edu_governments.py`), com `started` (normas e programas),
   `cuts` (corte, bloqueio, regra fiscal, vinculação, veto), séries mostradas, outros fatores,
   limitações e fontes. Interinidades entram no período do titular por `includes`.
2. **Mesmas regras de número da ADR 0007:** só `v`, `diff`, `pct` e `lit`. Não há `cite`:
   literatura revisada por pares só entra depois que o DOI está no registro verificado.
   Valores de cortes em reais não são digitados; aparecem quando houver série coletada.
3. **Conferência por item:** cada início e corte tem `source` (URL) e `checked` (data em que
   foi conferido com o registro oficial). Sem `checked`, o site mostra o aviso.
4. **Página** `/educacao/governos/<id>/`: o que começou, cortes, variação das séries na
   janela do período com defasagem 0 a 2 e comparação regional, gráficos, outros fatores e
   limitações. Descritiva: não demonstra causa.

## English

### Context
For each government period we show what began in education, what was cut or limited and
the series that may relate, without implying the government caused the change (ADR 0003).
The development environment cannot reach Crossref or Planalto, so new DOIs cannot be
verified (ADR 0007) and official texts were not read.

### Decision
1. **One file per period** in `education/governos/<period-id>.yaml`
   (`pipeline/compilador/edu_governments.py`) with `started` (laws and programs), `cuts`
   (cut, withholding, fiscal rule, earmark, veto), the series shown, other factors,
   limitations and sources. Acting periods fold into the incumbent's via `includes`.
2. **Same number rules as ADR 0007:** only `v`, `diff`, `pct` and `lit`. No `cite`:
   peer-reviewed literature enters only once its DOI is in the verified registry. Cut
   amounts in reais are not typed; they appear once a series is collected.
3. **Per-item checking:** every start and cut has a `source` URL and `checked` (the date it
   was matched against the official record). Without `checked` the site shows a notice.
4. **Page** `/en/education/governments/<id>/`: what started, cuts, change in the series
   over the period's window with lags 0 to 2 and regional comparison, charts, other factors
   and limitations. Descriptive: it does not show causation.
