# 0011 — Guias dos indicadores / Indicator guides

- **Status:** aceito / accepted
- **Data / Date:** 2026-10-26

## pt-BR

### Contexto
Quem abre um indicador (por exemplo, o PIB per capita) precisa entender o que ele mede,
como ler o gráfico, o que a literatura revisada por pares diz sobre ele, o que políticas
públicas já fizeram com ele e o que isso significa em renda de verdade. Esse texto não cabe
na definição curta do indicador nem em uma análise, e precisa seguir as mesmas regras de
rastreabilidade (ADR 0007).

### Decisão
1. **Guia é um tipo de conteúdo**, em `guides/<id_do_indicador>.yaml`, validado no build
   com as mesmas regras das fichas de política: texto bilíngue, números só por marcadores,
   DOIs verificados (`verify-dois`). O ADR 0007 vale para o texto do guia. Os campos já
   existentes do indicador continuam fora da verificação de números soltos.
2. **Evidência só de artigos revisados por pares.** Documentos de trabalho e relatórios
   institucionais ficam de fora. Artigos encomendados no estilo do *Journal of Economic
   Perspectives* também ficam de fora (decisão tomada no piloto).
3. **Neutralidade vale para as políticas estudadas**, não para os estudos sobre a medida:
   um guia pode apresentar críticas ao indicador sem equilibrá-las com elogios.
4. **Faixas de renda.** Renda domiciliar per capita mensal (percentis P5 a P99 da PNAD
   Contínua, tabela 7438 do IBGE), em faixas de dólares PPC de 2021: até 250, 250 a 500,
   500 a 1.000, 1.000 a 2.000 e acima de 2.000. O dólar PPC vem do consumo das famílias do
   Banco Mundial (`PA.NUS.PRVT.PP`), convertido em reais de cada ano com o IPC
   (`FP.CPI.TOTL`): reais por dólar PPC no ano Y = PPC[2021] × IPC[Y] / IPC[2021].
5. **Desvio da primeira escolha (renda domiciliar total).** O IBGE só publica percentis
   prontos da renda per capita; a renda domiciliar total exigiria os microdados da PNAD
   (ADR 0010), adiados. Os limiares também foram reduzidos (antes 1 mil, 2 mil, 5 mil e
   10 mil dólares), porque, em termos per capita, os limites antigos colocavam cerca de
   82% das pessoas na primeira faixa em 2024.
6. **Participações por interpolação linear.** A participação de cada faixa é uma estimativa
   pontual por interpolação linear entre os percentis publicados. Abaixo de P5 ou acima de
   P99 é um intervalo. O método fica registrado em `income_brackets.json`.
7. **Tradução dos grupos dos estudos.** Quando um estudo fala em "os X% mais pobres/ricos",
   o pipeline calcula a faixa correspondente e o site mostra a tradução junto do grupo
   original, do ano e da conversão. Convenção do ponto de corte: "10% mais ricos" é o corte
   90, lado `top`; "40% mais pobres" é o corte 40, lado `bottom`. A tradução é opcional e
   exige ano a partir de 2012.
8. **Números derivados e rastreabilidade.** Participações e limites das faixas são números
   derivados, mostrados fora dos marcadores `v`/`cite` e rastreados pelo campo `sources` de
   `income_brackets.json` (precedente: `period_changes`).
9. **Quando as seções de renda aparecem:** para os indicadores listados em
   `income_indicators` em `data/reference/faixas-de-renda.yaml`, ou quando o guia tem
   entradas `by_income`.
10. **Guarda da rodada do ICP.** O build falha se o nome da série de PIB em PPC do WDI deixar
    de mencionar o ano-base configurado, sinal de que a rodada do Programa de Comparação
    Internacional mudou.

### Consequências
- Cada guia novo é um arquivo, revisado como qualquer ficha.
- As faixas valem para renda per capita, não domiciliar total; o site diz isso.
- Se o IBGE ou o Banco Mundial mudarem a série, o build avisa em vez de publicar faixas
  defasadas.
- **Adiado:** renda domiciliar total (microdados), grupos por decil e por linha de pobreza,
  incerteza amostral das participações.

### Alternativas consideradas
- Renda domiciliar total: precisa de microdados, adiada.
- Limiares de 1 mil a 10 mil dólares: concentravam quase todos na primeira faixa.
- Incluir documentos de trabalho como evidência: mais cobertura, menos controle de qualidade.

## English

### Context
Someone opening an indicator (for example GDP per capita) needs to know what it measures,
how to read the chart, what peer-reviewed literature says about it, what public policies
have done with it, and what it means in real income. That text fits neither the short
indicator definition nor an analysis, and must follow the same traceability rules (ADR 0007).

### Decision
1. **A guide is a content type**, in `guides/<indicator_id>.yaml`, validated at build time
   by the same rules as policy briefs: bilingual text, numbers only through markers,
   verified DOIs (`verify-dois`). ADR 0007 applies to guide text; existing indicator fields
   stay outside the bare-number check.
2. **Evidence is peer-reviewed journal articles only.** Working papers and institutional
   reports are excluded, as are commissioned *Journal of Economic Perspectives*-style
   articles (a ruling made during the pilot).
3. **Neutrality applies to studied policies**, not to studies about the measure: a guide may
   present criticism of an indicator without balancing it with praise.
4. **Income brackets.** Monthly household income per capita (IBGE Continuous PNAD table
   7438, percentiles P5 to P99) in 2021 PPP-dollar brackets: up to 250, 250 to 500, 500 to
   1,000, 1,000 to 2,000 and above 2,000. The PPP rate comes from World Bank household
   consumption PPP (`PA.NUS.PRVT.PP`), converted to reais of each year with CPI
   (`FP.CPI.TOTL`): reais per PPP dollar in year Y = PPP[2021] × CPI[Y] / CPI[2021].
5. **Deviation from the first choice (total household income).** IBGE publishes ready
   percentiles only per capita; total household income would need PNAD microdata
   (ADR 0010), deferred. Thresholds were also lowered (formerly US$1k, 2k, 5k and 10k)
   because, per capita, the old limits put about 82% of people in the first bracket in 2024.
6. **Shares by linear interpolation.** Each bracket's share is a point estimate by linear
   interpolation between published percentiles; below P5 or above P99 it is a range. The
   method is recorded in `income_brackets.json`.
7. **Translating study groups.** When a study speaks of "the poorest/richest X%", the
   pipeline computes the matching bracket and the site shows the translation next to the
   original group, the year and the conversion. Cut-point convention: "top 10%" is cut 90,
   side `top`; "bottom 40%" is cut 40, side `bottom`. The translation is optional and
   requires a year of 2012 or later.
8. **Derived numbers and traceability.** Bracket shares and limits are derived numbers,
   shown outside the `v`/`cite` markers and traced through the `sources` field of
   `income_brackets.json` (precedent: `period_changes`).
9. **When income sections show:** for indicators listed in `income_indicators` in
   `data/reference/faixas-de-renda.yaml`, or when the guide has `by_income` entries.
10. **ICP round guard.** The build fails if the WDI PPP GDP series name no longer mentions the
    configured base year, a sign that the International Comparison Program round changed.

### Consequences
- Each new guide is one file, reviewed like any brief.
- Brackets describe per capita, not total household, income; the site says so.
- If IBGE or the World Bank change a series, the build fails instead of publishing stale
  brackets.
- **Deferred:** total household income (microdata), decile and poverty-line groups, sampling
  uncertainty of the shares.

### Alternatives considered
- Total household income: needs microdata, deferred.
- US$1k to 10k thresholds: nearly everyone in the first bracket.
- Working papers as evidence: wider coverage, weaker quality control.
