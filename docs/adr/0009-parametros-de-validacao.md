# 0009 — Parâmetros de coleta e validação / Collection and validation parameters

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-25

## pt-BR

### Contexto
O pipeline usa alguns números fixos que afetam o que é coletado e o que vira alerta.
Eles precisam estar documentados e justificados.

### Decisão
- **Ano inicial da coleta: 1975.** O foco é 1980–hoje, mas variações de 1980 precisam de
  um ano-base, e a tabela por governo usa defasagem de até 2 anos.
- **Saltos atípicos:** z-score robusto da variação anual (mediana e desvio absoluto
  mediano × 1,4826) acima de 5, calculado só entre anos consecutivos e só com pelo menos
  8 variações. Gera **aviso**, nunca erro nem correção: hiperinflação, pandemia e crises
  são reais.
- **Séries sem dado:** um indicador do catálogo sem nenhuma observação para uma geografia
  coberta gera aviso.
- **Tolerância do changelog:** diferenças menores que 10⁻⁹ são ruído de formatação da
  fonte e não contam como revisão.

### Consequências
Séries modeladas e suaves (mortalidade infantil) geram muitos avisos de salto, porque a
variação típica é quase constante. Os avisos são para revisão humana; o limiar pode ser
ajustado por indicador no futuro.

## English

### Decision
Collection starts in 1975 (baselines for 1980 changes and lagged tables). Atypical jumps:
robust z-score of year-over-year changes (median, MAD × 1.4826) above 5, consecutive years
only, at least 8 changes; a **warning**, never an error or correction. A catalog indicator
with no observation for a covered geography is a warning. Changelog tolerance: differences
below 10⁻⁹ are source formatting noise.

### Consequences
Smooth modeled series (infant mortality) produce many jump warnings; they are for human
review and the threshold may become per-indicator later.
