# 0001 — Stack técnica / Technical stack

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
O projeto precisa de um pipeline de dados reprodutível, mantido por pessoas de ciências
sociais e de software, e de um site estático bilíngue com gráficos interativos que
funcione bem no celular e seja publicado no GitHub Pages.

### Decisão
- **Pipeline:** Python 3.12, gerenciado com `uv` (lockfile garante versões idênticas no CI
  e localmente). `pandas` + `pyarrow` para tabelas, `pydantic` para validar YAML de
  referência e metadados, `httpx` para coleta, `pytest` e `ruff` para qualidade.
- **Site:** Astro.
  - i18n nativo (pt-BR em `/`, inglês em `/en/`).
  - Arquitetura de "ilhas": só os gráficos carregam JavaScript; o resto é HTML estático,
    bom para celulares e conexões lentas.
  - *Content collections* com esquema validado no build: uma análise sem limitações ou
    sem tradução quebra o build.
- **Gráficos:** Observable Plot. Cerca de 150 KB, adequado para séries temporais com faixas
  de incerteza, faixas de período de governo e marcação de quebras de série.
- **Automação:** GitHub Actions para CI, atualização agendada de dados (via PR) e
  publicação no GitHub Pages.

### Consequências
- Duas linguagens no repositório (Python e TypeScript/JavaScript). A fronteira é clara:
  o pipeline escreve arquivos em `site/public/data/`, o site só os lê.
- O site nunca coleta dados em tempo real; o que está publicado corresponde a um commit.

### Alternativas consideradas
- **MkDocs Material:** ótimo para documentação e todo em Python, mas gráficos
  interativos e i18n dependem de plugins e ficam remendados.
- **Eleventy:** flexível, mas sem validação de conteúdo por esquema; mais coisa feita à mão.
- **Plotly:** mais recursos, porém cerca de 3 MB de JavaScript por página.
- **polars** em vez de pandas: mais rápido, mas o volume de dados é pequeno e pandas é mais
  conhecido por quem contribui com análises.

## English

### Context
The project needs a reproducible data pipeline maintained by both social scientists and
software developers, and a bilingual static site with interactive charts that works well
on phones and is published on GitHub Pages.

### Decision
- **Pipeline:** Python 3.12 managed with `uv` (the lockfile pins identical versions in CI
  and locally); `pandas` + `pyarrow`, `pydantic`, `httpx`, `pytest`, `ruff`.
- **Site:** Astro, for native i18n (Portuguese at `/`, English at `/en/`), islands
  architecture (JavaScript only for charts) and schema-validated content collections.
- **Charts:** Observable Plot (~150 KB), suited to time series with uncertainty bands,
  government period bands and series-break markers.
- **Automation:** GitHub Actions for CI, scheduled data refresh (via PR) and Pages deploy.

### Consequences
Two languages in the repository with a clear boundary: the pipeline writes files to
`site/public/data/`, the site only reads them. The published site always matches a commit.

### Alternatives considered
MkDocs Material (interactive charts and i18n are bolted on), Eleventy (no schema-validated
content), Plotly (~3 MB per page), polars (faster, but data is small and pandas is better
known among contributors).
