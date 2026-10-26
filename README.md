# Entender Política

**pt-BR** · [English](#english)

Dados abertos e evidência científica para entender mudanças políticas e de políticas
públicas no Brasil, de 1980 até hoje, com comparações internacionais.

Todo argumento do site segue a mesma estrutura:

> **Afirmação → Métrica → Dados → Fonte científica (DOI) → Limitações**

## Princípios

- **Rastreabilidade:** todo número citado vem de um dado do repositório, com fonte,
  data de coleta, licença e versão. Números digitados à mão são rejeitados pelo CI.
- **Correlação não é causalidade:** linhas do tempo por governo são descritivas.
  Ver [ADR 0003](docs/adr/0003-governos-e-causalidade.md).
- **Incerteza visível:** intervalos, margens de erro e quebras metodológicas nas séries.
- **Neutralidade:** evidências favoráveis e contrárias; políticas que funcionaram e que
  não funcionaram.
- **Reprodutibilidade:** qualquer pessoa regenera cada gráfico a partir do código.
- **Bilíngue:** todo conteúdo existe em pt-BR e inglês.

## Estrutura

| Pasta | Conteúdo |
|---|---|
| `pipeline/` | "Compilador" em Python: coleta, normaliza, valida e gera artefatos (+ testes) |
| `data/raw/` | Dados brutos, com manifesto (URL, sha256, data, licença) |
| `data/processed/` | Observações normalizadas |
| `data/reference/` | Tabelas de referência (períodos de governo, marcos) |
| `indicators/` | Catálogo de indicadores: definição, fórmula, fonte, críticas |
| `analyses/` | Análises (pergunta, hipótese, método, resultado, limitações) |
| `policies/` | Fichas de políticas públicas de referência, com nível de evidência |
| `site/` | Site estático (Astro) publicado no GitHub Pages |
| `docs/` | Metodologia e decisões (ADRs) |

## Rodar localmente

```sh
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run compilador build          # dados brutos -> dados processados e arquivos do site (offline)
uv run compilador fetch          # baixa novos snapshots das fontes (rede)
uv run compilador verify-dois    # confere DOIs novos na Crossref (rede)
cd site && npm ci && npm run dev # site em http://localhost:4321/entender-politica/
```

Site: <https://amadeu01.github.io/entender-politica/> (no ar depois do primeiro deploy, com o
GitHub Pages configurado para "GitHub Actions"). Automação:
[ADR 0008](docs/adr/0008-automacao-e-publicacao.md).

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md).

## Licença

Código: [MIT](LICENSE). Conteúdo: [CC BY 4.0](LICENSE-CONTENT.md). Dados: licença de cada
fonte original. Como citar: [CITATION.cff](CITATION.cff).

---

## English

Open data and peer-reviewed evidence to understand political and public policy change in
Brazil from 1980 to the present, with international comparisons.

Every argument on the site follows the same structure:

> **Claim → Metric → Data → Scientific source (DOI) → Limitations**

Principles: every cited number is traceable to repository data (hand-typed numbers fail
CI); timelines by government are descriptive, not causal
([ADR 0003](docs/adr/0003-governos-e-causalidade.md)); uncertainty and series breaks are
shown; evidence for and against is presented; everything is reproducible from code; all
content exists in Portuguese and English.

Run locally with `uv sync && uv run pytest && uv run compilador build`, then
`cd site && npm ci && npm run dev`. Site: <https://amadeu01.github.io/entender-politica/>
(live after the first deploy, with GitHub Pages set to "GitHub Actions"). See
[CONTRIBUTING.md](CONTRIBUTING.md).

License: code [MIT](LICENSE), content [CC BY 4.0](LICENSE-CONTENT.md), data under each
source's license.
