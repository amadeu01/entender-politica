# 0005 — Fontes do MVP / MVP data sources

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
O plano original previa três fontes no MVP: Banco Mundial, PNUD e IBGE/SIDRA. Com o foco
em 1980–hoje, essas fontes deixam os anos 1980 quase vazios: o IDH do PNUD começa em 1990
e a PNAD Contínua no SIDRA começa em 2012.

### Decisão
O MVP usa quatro fontes:

| Fonte | Para quê | Cobertura |
|---|---|---|
| Banco Mundial (WDI, WGI) | indicadores comparáveis entre países (PIB per capita, inflação, mortalidade infantil, Gini, governança) | WDI desde 1960; WGI desde 1996 |
| PNUD (Relatório de Desenvolvimento Humano) | IDH e IDH ajustado à desigualdade | desde 1990 |
| IBGE/SIDRA | PNAD Contínua (renda, Gini, desemprego) | desde 2012 |
| Ipeadata | séries longas do Brasil (Gini e pobreza pela PNAD antiga, salário mínimo real) | desde 1976 |

Nesta fase entram, das séries citadas acima, o Gini da PNAD Contínua (SIDRA) e o Gini e a
taxa de pobreza da PNAD antiga (Ipeadata). Renda média e desemprego da PNAD Contínua e
salário mínimo real do Ipeadata ficam para um PR seguinte.

### Consequências
- A série brasileira de Gini e pobreza combina PNAD (até 2015) e PNAD Contínua (desde
  2012). As séries **não** são emendadas: aparecem como séries separadas, com a quebra
  marcada e os anos de sobreposição visíveis.
- A PNAD antiga não foi a campo em anos de Censo (1980, 1991, 2000, 2010) nem em 1994;
  esses anos ficam sem valor, e não interpolados.

## English

### Context
The original plan had three MVP sources: World Bank, UNDP and IBGE/SIDRA. With the focus
on 1980–present they leave the 1980s almost empty: UNDP's HDI starts in 1990 and the
continuous PNAD on SIDRA in 2012.

### Decision
The MVP uses four sources: World Bank (WDI, WGI), UNDP (HDI, inequality-adjusted HDI),
IBGE/SIDRA (continuous PNAD, from 2012) and Ipeadata (long Brazilian series from 1976).
This phase adds the Continuous PNAD Gini (SIDRA) and the old-PNAD Gini and poverty rate
(Ipeadata); Continuous PNAD mean income and unemployment and Ipeadata's real minimum wage
come in a later PR.

### Consequences
Brazilian Gini and poverty combine the old PNAD (to 2015) and the continuous PNAD (from
2012). The series are **not** spliced: they are shown separately with the break marked and
overlap years visible. The old PNAD was not fielded in census years (1980, 1991, 2000,
2010) or 1994; those years stay empty, not interpolated.
