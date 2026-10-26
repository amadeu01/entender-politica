# Plano do MVP / MVP plan

**pt-BR** · [English](#english)

Objetivo: linha do tempo do Brasil de 1980 até hoje, por governo, com comparação
internacional, uma análise completa (desigualdade) ligada a uma ficha de política de
referência (Progresa/Oportunidades, México), tudo em pt-BR e inglês, publicado no
GitHub Pages.

| Fase | Entrega | PR |
|---|---|---|
| 1 | Base: estrutura, licenças, CITATION, CONTRIBUTING, ADRs 0001–0005, tabela de governos, CI | `fase-1/base` |
| 2 | Núcleo do pipeline: esquema do formato comum, manifesto, validação, changelog; conector Banco Mundial (WDI/WGI) | `fase-2/pipeline-wdi` |
| 3 | Conectores PNUD, IBGE/SIDRA e Ipeadata; catálogo de indicadores | `fase-3/fontes` |
| 4 | Camada de análises e políticas: verificador de números, checagem de DOI, análise de desigualdade, ficha Progresa | `fase-4/analises` |
| 5 | Site Astro bilíngue: início, Brasil 1980–hoje, catálogo, análises, políticas, metodologia, referências, como contribuir | `fase-5/site` |
| 6 | Publicação: workflows de deploy e de atualização agendada | `fase-6/deploy` |

Depois do MVP, uma fonte por PR: V-Dem, Our World in Data, FAOSTAT, INEP, DataSUS, OCDE,
UNESCO UIS, WID, Base dos Dados. E uma análise ou ficha de política por PR.

## English

Goal: a Brazil 1980–present timeline by government with international comparison, one
complete analysis (inequality) linked to a reference policy brief (Progresa/Oportunidades,
Mexico), all in Portuguese and English, published on GitHub Pages. Phases as in the
table above: (1) foundation, (2) pipeline core + World Bank, (3) UNDP, IBGE/SIDRA and
Ipeadata + indicator catalog, (4) analyses and policy layer, (5) bilingual Astro site,
(6) deploy and scheduled refresh. After the MVP: one source, analysis or policy brief per PR.
