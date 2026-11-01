# 0014 — Gasto federal em educação (Siconfi) / Federal education spending (Siconfi)

- **Status:** aceito / accepted
- **Data / Date:** 2026-11-01

## pt-BR

### Contexto
Para olhar cortes e bloqueios (ADR 0013) faltava uma série de gasto **federal** em reais. O
gasto do Banco Mundial (% do PIB) soma União, estados e municípios e sobe quando o PIB cai.
Dotação autorizada, bloqueio e contingenciamento por ano não estão em nenhuma API alcançável
do ambiente de desenvolvimento (SIOP e SIGA Brasil só têm páginas de consulta; o Portal da
Transparência exige chave).

### Decisão
1. **Fonte:** DCA (Declaração de Contas Anuais), Anexo I-E, da União, na API de dados abertos
   do Tesouro (Siconfi), de 2014 em diante: despesa empenhada e paga na função Educação e
   nas subfunções Ensino Superior e Ensino Profissional, além das Transferências para a
   Educação Básica, que pertence à função Encargos Especiais e não soma no total de Educação. A DCA é o fechamento contábil, sem revisões posteriores.
2. **Preços constantes:** cada valor é dividido pela média anual do IPCA (série 433 do
   Banco Central, baixada junto no mesmo snapshot) e multiplicado pela média do ano-base, o
   último ano com os doze meses. O ano-base muda quando um novo snapshot cobre mais um ano.
3. **O que a série não mostra:** dotação, bloqueio e contingenciamento. Um bloqueio revertido
   no mesmo ano não aparece, e "pago" menor que "empenhado" pode ser adiamento (restos a
   pagar), não corte. Os críticos estão no cadastro de cada indicador.
4. **Antes de 2014:** sem série federal em reais. Fica como lacuna registrada na auditoria
   (`docs/auditoria-dados-educacao.md`), não preenchida com número digitado.

## English

### Context
To look at cuts and withholdings (ADR 0013) we lacked a **federal** spending series in reais.
The World Bank series (% of GDP) adds the Union, states and municipalities and rises when GDP
falls. Authorized appropriation, withholding and *contingenciamento* per year are on no API
reachable from the development environment (SIOP and SIGA Brasil only have query pages; the
Transparency Portal needs a key).

### Decision
1. **Source:** the Union's DCA (annual accounts), Annex I-E, from the Treasury open data API
   (Siconfi), 2014 on: committed and paid spending in the Education function and the Higher
   Education and Vocational Education sub-functions, plus Transfers to Basic Education, which belongs to the Special Charges function and does not add to the Education total. The DCA is
   the accounting close, with no later revisions.
2. **Constant prices:** each value is divided by the year's average IPCA (Central Bank series
   433, fetched in the same snapshot) and multiplied by the base year's average, the latest
   year with twelve months. The base year moves when a new snapshot covers one more year.
3. **What the series does not show:** appropriation, withholding and *contingenciamento*. A
   block reversed within the year does not appear, and "paid" below "committed" can be
   deferral (*restos a pagar*), not a cut. Critics are in each indicator's record.
4. **Before 2014:** no federal series in reais. Recorded as a gap in the audit
   (`docs/auditoria-dados-educacao.md`), not filled with typed numbers.
