# Guia do indicador / Indicator guide — design

- **Data / Date:** 2026-10-26
- **Status:** rascunho para aprovação / draft for approval
- **Primeiro de três projetos / First of three projects:** (1) guia do indicador (este
  documento); (2) ligação indicador ↔ políticas ↔ projetos de lei; (3) rastreamento
  legislativo (autoria, mapa de votos, votantes fora do padrão). (2) e (3) terão documentos
  próprios depois.

## pt-BR

### Intenção e porquê

Hoje a página de cada indicador (ex.: <https://amadeu01.github.io/entender-politica/indicadores/wdi.ny_gdp_pcap_kd/>)
tem definição, fórmula, unidade, gráfico, críticas e uma ou poucas referências. Isso serve
para quem já sabe economia. O usuário quer que **um leigo** saia da página sabendo:

- o que o número é e o que ele não é;
- como ler o gráfico e o "marcador" (o valor, a unidade, subir ou descer);
- o que estudos sérios dizem sobre a relação do indicador com a evolução (ou não) da
  sociedade;
- quais políticas públicas, no Brasil e em outros países, foram estudadas como capazes de
  mexer nesse indicador, e com que força de evidência;
- o que o indicador significa para **o trabalhador médio** e para **famílias com renda
  familiar mensal de até US$1 mil, 2 mil, 5 mil e 10 mil**;
- o **custo de vida**: se o dinheiro dentro do Brasil compra mais ou menos para o
  brasileiro médio, ao longo do tempo e comparado a outros países;
- como ler os estudos citados (o que é experimento, correlação, tamanho de efeito etc.).

O valor do site continua sendo o mesmo: evidência rastreável e neutra. O guia não pode
trocar rigor por didática.

### Objetivos

1. **Seções novas em cada página de indicador**, nesta ordem sugerida (o layout fica com
   quem construir):
   - **Entender:** o que mede, em linguagem simples, e o que não mede.
   - **Como ler:** como ler o gráfico e o valor; o que significa subir ou cair; unidade e
     escala; quebras de série; faixas de governo (ADR 0003). Inclui **um exemplo com dado
     real do site**, escrito com marcadores `v`/`diff`/`pct` (ADR 0007).
   - **Armadilhas:** as críticas atuais (`criticisms`) continuam; o guia pode remetê-las.
   - **O que os estudos dizem:** estudos sobre a relação do indicador com bem-estar e
     desenvolvimento (ex.: Jones & Klenow 2016 para PIB per capita), no Brasil e fora.
   - **Políticas estudadas:** entradas curtas — política, país, período, resultado,
     desenho do estudo, nível de evidência, DOI — e link para a ficha de política completa
     quando existir (`policies/*.yaml`). Brasil e outros países.
   - **Por faixa de renda:** ver objetivo 2.
   - **Poder de compra:** ver objetivo 3.
   - **Referências:** separadas entre "sobre o indicador" e "políticas e impactos".
2. **Faixas de renda familiar.** Parte descritiva, com dados:
   - faixas de **renda familiar mensal**: até US$1 mil, até 2 mil, até 5 mil, até 10 mil,
     acima de 10 mil;
   - quanto da população (ou dos domicílios) brasileira está em cada faixa, ao longo do
     tempo;
   - a renda do **trabalhador médio** (mediana da renda do trabalho ou da renda familiar;
     escolha do construtor, documentada) ao lado do indicador.
   - Parte interpretativa, por indicador: "o que este indicador significa para cada faixa"
     **somente com base em estudos citados**. Sem estudo, a página diz que não há estudo
     encontrado, em vez de inventar.
   - **Tradução de grupos dos estudos para as faixas (decisão do usuário):** estudos falam
     em decis, "os 40% mais pobres" ou linhas de pobreza. O guia pode traduzir esse grupo
     para as faixas em US$ usando os dados de distribuição do próprio site, **sempre com a
     conversão visível**: o grupo original do estudo, o ano, a faixa correspondente e a
     conta (ex.: "os 40% mais pobres em 2022 ≈ famílias com renda até US$2 mil"). A
     tradução é calculada pelo pipeline a partir dos dados, nunca digitada, e o build
     rejeita tradução sem grupo original, ano e referência.
   - Thresholds das faixas ficam num único arquivo de dados ou configuração, não digitados
     em cada guia.
3. **Custo de vida e poder de compra** (pedido do usuário durante o design):
   - mostrar se o dinheiro dentro do Brasil compra mais ou menos para o brasileiro médio:
     evolução da renda **real** (descontada a inflação) da família mediana;
   - comparação com outros países pelo **nível de preços** (razão entre PPC e câmbio; dado
     do Banco Mundial) — explica por que US$1 mil em câmbio compra mais no Brasil do que
     nos EUA;
   - no guia do PIB per capita, mostrar a versão em PPC ao lado da versão em câmbio
     (a crítica atual já diz que câmbio distorce comparação entre países).
   - Fontes candidatas: WDI (fator de conversão PPC, nível de preços, PIB per capita PPC),
     IPCA/IBGE para deflacionar, PNAD Contínua para renda. Cesta básica (DIEESE) só se a
     licença permitir (ADR 0006).
4. **Página "Como ler estudos"**, única, bilíngue, ligada de todo guia: tipos de desenho
   (experimento aleatorizado, diferenças-em-diferenças, controle sintético, regressão
   descontínua, variáveis instrumentais, correlação), revisão sistemática e metanálise,
   tamanho de efeito, intervalo de confiança, valor-p e "significativo", validade externa,
   revisado por pares × working paper, conflito de interesse, e como o site atribui o
   nível de evidência (ADR 0007 §6). Exemplos tirados das fichas existentes.
5. **Piloto no PIB per capita** (`wdi.ny_gdp_pcap_kd`) num PR; depois os outros 16
   indicadores em lotes, um PR por lote.

### Não objetivos (por ora)

- Ligar indicadores a projetos de lei, autoria, votos, outliers — projetos 2 e 3.
- Calculadora pessoal ("em que faixa eu estou").
- Afirmar que um governo ou uma política causou a mudança vista no gráfico do site.
- Ranking de políticas ou de governos.

### Anti-objetivos (seria fracasso mesmo funcionando)

- **Sugerir causalidade** onde o estudo não sustenta: "a política X aumentou o PIB" com
  base em correlação. Afirmações causais só com desenho causal (ADR 0003, 0007 §5).
- **Número sem fonte** ou citado de memória (ADR 0007).
- **Seleção partidária de estudos:** só evidência favorável a um lado. Regra igual à das
  fichas: cada guia lista pelo menos um resultado nulo, negativo ou misto, ou diz onde a
  evidência contrária foi procurada.
- **Efeito por faixa de renda inventado:** frases como "o PIB subir ajuda quem ganha até
  US$1 mil" sem estudo que diga isso.
- **Jargão** sem explicação; texto que só economista entende.

### Restrições

- ADR 0002 (proveniência), 0003 (governos e causalidade), 0004 (bilíngue pt-BR/en, termos
  do `docs/glossario.yaml`), 0006 (licenças), 0007 (nenhum número digitado; `cite`/`lit`;
  DOIs verificados com `compilador verify-dois`), 0010 (recorte determinístico + hash se
  a fonte de renda for grande, ex.: microdados da PNAD).
- **Hoje os textos de indicador não passam pelo verificador de números** (só análises e
  fichas). Os campos novos do guia têm de passar pelo mesmo renderizador de conteúdo
  (`pipeline/compilador/content.py`), com a mesma regra de nenhum número digitado e de
  sequência idêntica de marcadores entre idiomas.
- Build continua offline; dados novos entram pelo fluxo de snapshot existente.
- **Só estudos revisados por pares** (decisão do usuário): IPEA Textos para Discussão,
  working papers do NBER e relatórios do Banco Mundial/PNUD não entram como evidência no
  guia. ADR 0007 fica como está. Dados de instituições (WDI, PNAD, WID) continuam como
  fontes de dados, não como estudos.
- Os campos existentes dos indicadores (`definition`, `formula`, `criticisms`) ficam fora
  do verificador de números; só os campos novos do guia passam por ele.
- Pesquisa de estudos: agentes de pesquisa podem achar candidatos, mas todo DOI é
  conferido na Crossref e todo número citado vem do texto lido (resumo, tabela, página).
  Revisores já inventaram DOIs neste projeto.

### Decisões tomadas

**Pelo usuário:**
- Público: leigo. Conteúdo: entender, como ler, estudos de referência, políticas que
  afetam o indicador, efeito por faixa de renda, como ler estudos, custo de vida.
- Faixas: renda **familiar**, limites US$1 mil, 2 mil, 5 mil, 10 mil.
- **Revisão no planejamento (2026-10-26):** o IBGE só publica pronta a distribuição da
  renda domiciliar **per capita** (PNAD Contínua, tabela 7438). O piloto usa renda por
  pessoa da família, com os mesmos limites US$1 mil, 2 mil, 5 mil, 10 mil por pessoa;
  renda familiar total (microdados, ADR 0010) fica para depois. Escolha do usuário.
- Ordem dos projetos: guia primeiro (proposta minha, aceita ao seguir adiante).
- Faixas em **dólar PPC** (Banco Mundial) de um ano-base fixo, com o equivalente em reais
  do ano exibido.
- Tradução de grupos dos estudos para as faixas permitida, com conversão visível.
- Só estudos revisados por pares.

**Minhas (para o usuário conferir):**
- Faixas são **mensais**, com faixa extra "acima de US$10 mil".
- **Seções de faixa de renda e poder de compra só nos indicadores de renda, preço,
  pobreza, desigualdade e desenvolvimento humano** (PIB per capita, inflação, pobreza,
  Gini, Ipeadata, IDH/IDHAD). Nos de democracia, governança e saúde (V-Dem, WGI,
  expectativa de vida, mortalidade infantil) essas seções aparecem só se houver estudo
  revisado que trate o indicador por renda; caso contrário, não aparecem. Assim nenhuma
  tabela de renda fica ao lado de um índice de democracia sugerindo ligação (ADR 0003).
- "Políticas estudadas" no guia são entradas curtas com DOI, não fichas completas; ficha
  completa é opcional e linkada quando existir.
- "Como ler estudos" é página própria, não texto repetido.
- Piloto no PIB per capita antes dos demais.
- Parte descritiva por faixa (distribuição, renda mediana) é igual para todos os
  indicadores; a interpretação por faixa é específica e depende de estudo.

### Deixado para quem construir

- Nomes de campos e formato no YAML do indicador; reaproveitar `Reference`, `Text` e a
  lógica de neutralidade das fichas (`contrary_evidence_search`) onde couber.
- Layout da página e componentes; gráficos seguindo a prática do repositório (skill
  `dataviz`).
- Fonte e tabela exatas da distribuição de renda familiar (tabelas SIDRA da PNAD Contínua
  × microdados × WID), ano-base da PPC, como tratar anos antes da PNAD Contínua (2012) —
  documentando a escolha num ADR se mudar regra existente.
- Se a distribuição por faixa vira um indicador novo no catálogo ou um conjunto de dados
  à parte.
- Lotes dos 16 indicadores restantes.

## English

### Intent

Each indicator page should teach a lay reader what the number is and is not, how to read
the chart and value, what peer-reviewed studies say about the indicator and social
progress, which public policies (Brazil and abroad) were studied as moving it and with
what evidence strength, what it means for the median worker and for families with monthly
household income up to US$1k, 2k, 5k and 10k, whether money inside Brazil buys more or
less for the median Brazilian (cost of living, over time and versus other countries), and
how to read the studies cited. Rigor stays: traceable, neutral evidence.

### Goals

1. New sections on every indicator page: Understand, How to read (with a real-data example
   via `v`/`diff`/`pct`), Pitfalls (existing criticisms), What studies say, Studied policies
   (short entries with design, evidence level, DOI; link to full policy brief when one
   exists), By income bracket, Purchasing power, References split into "about the
   indicator" and "policies and impacts".
2. Income brackets: descriptive data (share of Brazilian households per monthly household
   income bracket over time; median worker or household income beside the indicator);
   per-indicator interpretation **only from cited studies**, otherwise say none was found.
   A study's group (decile, bottom 40%, poverty line) may be translated to the US$
   brackets using the site's distribution data, always showing the original group, year,
   matching bracket and computation; computed by the pipeline, never typed. Thresholds
   live in one data/config file. Bracket and purchasing-power sections appear on income,
   price, poverty, inequality and HDI indicators; on democracy, governance and health
   indicators only when a peer-reviewed study treats the indicator by income.
3. Cost of living: real (inflation-adjusted) income of the median family over time;
   price level versus other countries (PPP / exchange-rate ratio); GDP per capita in PPP
   beside the exchange-rate version. Candidate sources: WDI, IPCA, PNAD Contínua; DIEESE
   basic basket only if its license allows.
4. A single bilingual "How to read studies" page linked from every guide.
5. Pilot on GDP per capita in one PR, then the other 16 indicators in batches.

### Non-goals

Legislative links, votes and outliers (projects 2 and 3); personal calculator; causal
claims about governments; rankings.

### Anti-goals

Implied causality without a causal design; unsourced or remembered numbers; one-sided
selection of studies (each guide needs a null/negative/mixed finding or a documented
contrary-evidence search); invented per-bracket effects; unexplained jargon.

### Constraints

ADRs 0002, 0003, 0004, 0006, 0007, 0010. Indicator text is not checked for bare numbers
today; the new guide fields must go through `content.py` with the same rules. Offline
build. Every DOI verified on Crossref; every quoted number read in the source.

### Decisions

User: lay audience; the content list above; household income, revised during planning to
**household income per capita** (IBGE publishes only that distribution; total household
income needs microdata, deferred); brackets US$1k/2k/5k/10k;
PPP dollars of a fixed base year with the reais equivalent shown; study-group-to-bracket
translation allowed with visible conversion; **peer-reviewed studies only** (ADR 0007
unchanged; existing indicator fields stay outside the bare-number check).
Mine (for review): monthly brackets plus "above US$10k"; bracket and purchasing-power
sections limited to economic/HDI indicators unless a study covers others; studied policies as short entries rather than full
briefs; a standalone "How to read studies" page; GDP per capita pilot first; descriptive
bracket data shared across indicators, interpretation per indicator and study-backed.

### Left to the builder

Field names and YAML shape; page layout and charts (`dataviz`); exact income-distribution
source, PPP base year and pre-2012 handling (ADR if a rule changes); whether bracket
distribution becomes a catalog indicator; batching of the remaining 16 indicators.
