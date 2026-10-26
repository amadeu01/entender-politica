export type Lang = "pt" | "en";
export const LANGS: Lang[] = ["pt", "en"];

export const ROUTES = {
  home: { pt: "", en: "" },
  brazil: { pt: "brasil", en: "brazil" },
  indicators: { pt: "indicadores", en: "indicators" },
  analyses: { pt: "analises", en: "analyses" },
  policies: { pt: "politicas", en: "policies" },
  methodology: { pt: "metodologia", en: "methodology" },
  studies: { pt: "como-ler-estudos", en: "reading-studies" },
  references: { pt: "referencias", en: "references" },
  contribute: { pt: "contribuir", en: "contribute" },
} as const;
export type Route = keyof typeof ROUTES;

const BASE = import.meta.env.BASE_URL.replace(/\/?$/, "/");

/** Site-relative URL for a page in a language, e.g. url("en", "analyses", "x"). */
export function url(lang: Lang, route: Route, slug?: string): string {
  const parts = [lang === "en" ? "en" : "", ROUTES[route][lang], slug ?? ""].filter(Boolean);
  return BASE + parts.map((p) => p + "/").join("");
}

export function asset(path: string): string {
  return BASE + path.replace(/^\//, "");
}

export const REPO = "https://github.com/amadeu01/entender-politica";

export const UI = {
  pt: {
    siteName: "Entender Política",
    tagline: "Dados abertos e evidência científica sobre políticas públicas no Brasil",
    skip: "Pular para o conteúdo",
    nav: {
      home: "Início",
      brazil: "Brasil 1980–hoje",
      indicators: "Indicadores",
      analyses: "Análises",
      policies: "Políticas",
      methodology: "Metodologia",
      studies: "Como ler estudos",
      references: "Referências",
      contribute: "Como contribuir",
    },
    mainNav: "Principal",
    yes: "Sim",
    usedIn: "Usado em",
    result: "Resultado",
    noDataFor: "Sem dado nesta fonte",
    logDropped: "Valores menores ou iguais a zero não aparecem na escala logarítmica; ver a tabela.",
    unassigned: "nenhum ano atribuído (menos de seis meses, sem 1º de julho)",
    viewSourceCode: "código da coleta",
    otherLang: "English",
    otherLangCode: "en",
    footer:
      "Código sob licença MIT. Conteúdo sob CC BY 4.0. Dados e gráficos sob a licença de cada fonte, indicada em cada gráfico (os derivados do V-Dem são CC BY-SA 4.0).",
    source: "Fonte",
    license: "Licença",
    version: "Versão da fonte",
    retrieved: "Coletado em",
    metricPaper: "Artigo que fundamenta a métrica",
    downloadCsv: "Baixar dados (CSV)",
    viewCode: "Ver o código",
    tableView: "Ver os dados em tabela",
    year: "Ano",
    governments: "Faixas ao fundo: presidentes do Brasil",
    governmentsOthers: "não das outras geografias do gráfico",
    coverage: "Anos com dados",
    allSeries: "todas as séries",
    yearsCount: (n: number) => `${n} anos`,
    seriesBreak: "quebra de série",
    seriesBreaks: "Quebras de série",
    notice:
      "Esta visualização é descritiva e não demonstra que um governo causou a mudança. Ver a metodologia.",
    definition: "Definição",
    formula: "Fórmula",
    uncertainty: "Incerteza",
    criticisms: "Críticas à métrica",
    references: "Referências",
    unit: "Unidade",
    question: "Pergunta",
    hypothesis: "Hipótese",
    method: "Método",
    causal: "Afirma causalidade",
    descriptiveOnly: "Não: análise descritiva",
    evidenceFor: "Evidências a favor da hipótese",
    evidenceAgainst: "Evidências contrárias ou em disputa",
    limitations: "Limitações",
    numbers: "De onde vem cada número",
    number: "Número",
    origin: "Origem",
    relatedPolicies: "Políticas relacionadas",
    relatedAnalyses: "Análises relacionadas",
    summary: "Resumo",
    mechanism: "Mecanismo",
    findings: "Resultados das avaliações",
    outcome: "Resultado avaliado",
    externalValidity: "Vale para o Brasil?",
    contrarySearch: "Busca por evidência contrária",
    evidenceLevel: "Nível de evidência",
    levels: { high: "Alto", moderate: "Moderado", low: "Baixo" },
    directions: {
      positive: "Efeito positivo",
      null: "Sem efeito claro",
      negative: "Efeito negativo",
      mixed: "Resultado misto",
    },
    period: "Período",
    country: "País",
    bibtex: "Baixar as referências com DOI (BibTeX)",
    lag: "Defasagem",
    lagYears: (n: number) => (n === 0 ? "sem defasagem" : n === 1 ? "1 ano" : `${n} anos`),
    indicator: "Indicador",
    years: "Anos",
    change: "Variação",
    mixedYear: "ano com troca de presidente",
    acting: "interino",
    noData: "sem dado",
    readMore: "Ler",
    all: "Todos",
    guideUnderstand: "Entender o indicador",
    guideHowToRead: "Como ler este indicador",
    guideStudies: "O que dizem os estudos",
    guideStudiesHow: "Como ler estudos: o que cada desenho mostra e o que não mostra",
    guidePolicies: "Políticas estudadas",
    guideIncome: "Por faixa de renda",
    guideIncomeNone:
      "Não encontramos estudo revisado por pares sobre este indicador por grupo de renda.",
    guidePurchasing: "Poder de compra",
    guideRefsImpacts: "Políticas e impactos",
    guideRefsIndicator: "Sobre o indicador",
    briefLink: "Ver a ficha da política",
    translationTitle: "Em faixas de renda",
    translationGroup: (side: "bottom" | "top", cut: number) =>
      side === "bottom" ? `Os ${cut}% mais pobres` : `Os ${100 - cut}% mais ricos`,
    translationText: (year: number, brl: string, usd: string, bracket: string) =>
      `Em ${year}, o limite desse grupo era ${brl} por pessoa por mês, ou ${usd}. Faixa: ${bracket}.`,
    ppp: "US$ PPC",
    pppTerm: "Dólares PPC",
    pppExplain: (base: number) =>
      `Dólares ajustados pela paridade do poder de compra (PPC): um dólar PPC compra, no Brasil, o que um dólar comprava nos Estados Unidos em ${base}. A faixa é a renda domiciliar mensal por pessoa.`,
    bracketsTitle: "Quantas pessoas vivem em cada faixa de renda",
    bracketsCaption: (year: number) =>
      `Pessoas por faixa de renda domiciliar per capita mensal, Brasil, ${year}`,
    bracket: "Faixa (US$ PPC por pessoa por mês)",
    inReais: (year: number) => `Em reais por mês (${year})`,
    shareOfPeople: "Parcela das pessoas",
    interpolationNote: "≈ estimado por interpolação linear entre os percentis do IBGE",
    reaisPerUsd: (base: number) => `Reais por dólar PPC de ${base}`,
    reaisPerUsdNote: (base: number) =>
      `Essa taxa difere do fator de conversão PPC do ano corrente citado em Poder de compra, porque os limites das faixas estão fixos em dólares de ${base} e são atualizados pela inflação brasileira.`,
    breakLegend: "Área cinza e traço tracejado: anos afetados por quebra de série (veja a nota abaixo).",
    breakFlag: "quebra de série",
    priceLevelTitle: "Nível de preços em relação aos Estados Unidos",
    priceLevelCaption: "Fator de conversão PPC do consumo das famílias dividido pela taxa de câmbio, último ano com os dois valores",
    priceLevelNote:
      "Abaixo de 1, os preços são mais baixos que nos Estados Unidos; acima de 1, mais altos.",
    priceLevelCol: "Nível de preços",
    sourcesLabel: "Fontes",
    overTime: "Ao longo dos anos",
    overTimeAlt: (label: string, first: number, last: number) =>
      `Parcela das pessoas na faixa ${label} de ${first} a ${last}: faixa sombreada entre o mínimo e o máximo estimados e linha no ponto médio. Os valores estão na tabela abaixo.`,
    rangeBetween: (a: string, b: string) => `entre ${a} e ${b}`,
    approx: (a: string) => `≈ ${a}`,
    lessThan: (a: string) => `menos de ${a}`,
    upTo: (a: string) => `até ${a}`,
    moreThan: (a: string) => `mais de ${a}`,
    fromTo: (a: string, b: string) => `de ${a} a ${b}`,
    medianTitle: "Renda típica no Brasil",
    medianAlt:
      "Linhas do tempo da mediana do rendimento domiciliar per capita e da mediana do rendimento do trabalho no Brasil, em reais.",
    medianNote: (year: number) =>
      `Valores reais a preços de ${year}, último ano da série (PNAD Contínua).`,
    ppAlt: "Linha do tempo do PIB per capita ajustado pelo poder de compra, por geografia.",
    ppNominalAlt: "Linha do tempo do PIB per capita a preços constantes de 2015, por geografia.",
    ppNote:
      "O primeiro gráfico corrige as diferenças de custo de vida entre países; o segundo usa o câmbio e não corrige.",
    ppTitle: "PIB per capita em dólares PPC de 2021",
    nominalTitle: "PIB per capita em dólares de 2015",
    overTimeLegend: "Faixa sombreada: do mínimo ao máximo estimado; linha: ponto médio.",
  },
  en: {
    siteName: "Understanding Politics",
    tagline: "Open data and scientific evidence on public policy in Brazil",
    skip: "Skip to content",
    nav: {
      home: "Home",
      brazil: "Brazil 1980–today",
      indicators: "Indicators",
      analyses: "Analyses",
      policies: "Policies",
      methodology: "Methodology",
      studies: "Reading studies",
      references: "References",
      contribute: "Contribute",
    },
    mainNav: "Main",
    yes: "Yes",
    usedIn: "Used in",
    result: "Result",
    noDataFor: "No data in this source",
    logDropped: "Values at or below zero are not shown on the log scale; see the table.",
    unassigned: "no year assigned (under six months, no July 1)",
    viewSourceCode: "collection code",
    otherLang: "Português",
    otherLangCode: "pt-BR",
    footer:
      "Code under the MIT license. Content under CC BY 4.0. Data and charts under each source's license, shown on each chart (V-Dem-derived ones are CC BY-SA 4.0).",
    source: "Source",
    license: "License",
    version: "Source version",
    retrieved: "Collected on",
    metricPaper: "Paper behind the metric",
    downloadCsv: "Download data (CSV)",
    viewCode: "View the code",
    tableView: "View the data as a table",
    year: "Year",
    governments: "Background bands: Brazil's presidents",
    governmentsOthers: "not those of the chart's other geographies",
    coverage: "Years with data",
    allSeries: "all series",
    yearsCount: (n: number) => `${n} years`,
    seriesBreak: "series break",
    seriesBreaks: "Series breaks",
    notice:
      "This visualization is descriptive and does not show that a government caused the change. See the methodology.",
    definition: "Definition",
    formula: "Formula",
    uncertainty: "Uncertainty",
    criticisms: "Criticisms of the metric",
    references: "References",
    unit: "Unit",
    question: "Question",
    hypothesis: "Hypothesis",
    method: "Method",
    causal: "Claims causality",
    descriptiveOnly: "No: descriptive analysis",
    evidenceFor: "Evidence for the hypothesis",
    evidenceAgainst: "Contrary or disputed evidence",
    limitations: "Limitations",
    numbers: "Where each number comes from",
    number: "Number",
    origin: "Origin",
    relatedPolicies: "Related policies",
    relatedAnalyses: "Related analyses",
    summary: "Summary",
    mechanism: "Mechanism",
    findings: "Evaluation findings",
    outcome: "Outcome evaluated",
    externalValidity: "Does it apply to Brazil?",
    contrarySearch: "Search for contrary evidence",
    evidenceLevel: "Level of evidence",
    levels: { high: "High", moderate: "Moderate", low: "Low" },
    directions: {
      positive: "Positive effect",
      null: "No clear effect",
      negative: "Negative effect",
      mixed: "Mixed result",
    },
    period: "Period",
    country: "Country",
    bibtex: "Download references with a DOI (BibTeX)",
    lag: "Lag",
    lagYears: (n: number) => (n === 0 ? "no lag" : n === 1 ? "1 year" : `${n} years`),
    indicator: "Indicator",
    years: "Years",
    change: "Change",
    mixedYear: "year with a change of president",
    acting: "acting",
    noData: "no data",
    readMore: "Read",
    all: "All",
    guideUnderstand: "Understanding the indicator",
    guideHowToRead: "How to read this indicator",
    guideStudies: "What studies say",
    guideStudiesHow: "How to read studies: what each design can and cannot show",
    guidePolicies: "Studied policies",
    guideIncome: "By income bracket",
    guideIncomeNone: "We found no peer-reviewed study of this indicator by income group.",
    guidePurchasing: "Purchasing power",
    guideRefsImpacts: "Policies and impacts",
    guideRefsIndicator: "About the indicator",
    briefLink: "See the policy brief",
    translationTitle: "In income brackets",
    translationGroup: (side: "bottom" | "top", cut: number) =>
      side === "bottom" ? `The poorest ${cut}%` : `The richest ${100 - cut}%`,
    translationText: (year: number, brl: string, usd: string, bracket: string) =>
      `In ${year}, this group's limit was ${brl} per person per month, or ${usd}. Bracket: ${bracket}.`,
    ppp: "PPP US$",
    pppTerm: "PPP dollars",
    pppExplain: (base: number) =>
      `Dollars adjusted by purchasing power parity (PPP): one PPP dollar buys in Brazil what one dollar bought in the United States in ${base}. The bracket is monthly household income per person.`,
    bracketsTitle: "How many people live in each income bracket",
    bracketsCaption: (year: number) =>
      `People by monthly household income per capita bracket, Brazil, ${year}`,
    bracket: "Bracket (PPP US$ per person per month)",
    inReais: (year: number) => `In reais per month (${year})`,
    shareOfPeople: "Share of people",
    interpolationNote: "≈ estimated by linear interpolation between IBGE percentiles",
    reaisPerUsd: (base: number) => `Reais per ${base} PPP dollar`,
    reaisPerUsdNote: (base: number) =>
      `This rate differs from the current-year PPP conversion factor quoted under Purchasing power, because the bracket limits are fixed in ${base} dollars and updated by Brazilian inflation.`,
    breakLegend: "Grey area and dashed line: years affected by a series break (see the note below).",
    breakFlag: "series break",
    priceLevelTitle: "Price level relative to the United States",
    priceLevelCaption: "Household consumption PPP conversion factor divided by the exchange rate, latest year with both values",
    priceLevelNote:
      "Below 1, prices are lower than in the United States; above 1, higher.",
    priceLevelCol: "Price level",
    sourcesLabel: "Sources",
    overTime: "Over the years",
    overTimeAlt: (label: string, first: number, last: number) =>
      `Share of people in the ${label} bracket from ${first} to ${last}: shaded band between the estimated minimum and maximum and a line at the midpoint. Values are in the table below.`,
    rangeBetween: (a: string, b: string) => `between ${a} and ${b}`,
    approx: (a: string) => `≈ ${a}`,
    lessThan: (a: string) => `less than ${a}`,
    upTo: (a: string) => `up to ${a}`,
    moreThan: (a: string) => `more than ${a}`,
    fromTo: (a: string, b: string) => `from ${a} to ${b}`,
    medianTitle: "Typical income in Brazil",
    medianAlt:
      "Timelines of the median household income per capita and the median labor income in Brazil, in reais.",
    medianNote: (year: number) =>
      `Real values at ${year} prices, the last year of the series (Continuous PNAD).`,
    ppAlt: "Timeline of GDP per capita adjusted for purchasing power, by geography.",
    ppNominalAlt: "Timeline of GDP per capita at constant 2015 prices, by geography.",
    ppNote:
      "The first chart corrects for cost-of-living differences between countries; the second uses exchange rates and does not.",
    ppTitle: "GDP per capita in 2021 PPP dollars",
    nominalTitle: "GDP per capita in 2015 dollars",
    overTimeLegend: "Shaded band: estimated minimum to maximum; line: midpoint.",
  },
} as const;

export const SOURCE_NAMES: Record<string, Record<Lang, string>> = {
  wdi: { pt: "Banco Mundial — World Development Indicators", en: "World Bank — World Development Indicators" },
  wgi: { pt: "Banco Mundial — Worldwide Governance Indicators", en: "World Bank — Worldwide Governance Indicators" },
  undp_hdr: { pt: "PNUD — Relatório de Desenvolvimento Humano", en: "UNDP — Human Development Report" },
  ibge_sidra: { pt: "IBGE — SIDRA (PNAD Contínua)", en: "IBGE — SIDRA (Continuous PNAD)" },
  ipeadata: { pt: "Ipea — Ipeadata", en: "Ipea — Ipeadata" },
  vdem: { pt: "V-Dem — Varieties of Democracy", en: "V-Dem — Varieties of Democracy" },
};

export const METHOD_NAMES: Record<string, Record<Lang, string>> = {
  descriptive: { pt: "Descritivo", en: "Descriptive" },
  decomposition: { pt: "Decomposição", en: "Decomposition" },
  systematic_review: { pt: "Revisão sistemática", en: "Systematic review" },
  rct: { pt: "Experimento aleatorizado", en: "Randomized experiment" },
  difference_in_differences: { pt: "Diferenças em diferenças", en: "Difference-in-differences" },
  regression_discontinuity: { pt: "Regressão descontínua", en: "Regression discontinuity" },
  synthetic_control: { pt: "Controle sintético", en: "Synthetic control" },
  instrumental_variables: { pt: "Variáveis instrumentais", en: "Instrumental variables" },
  observational: { pt: "Observacional", en: "Observational" },
};

/** Pipeline module that collects each source, linked from every chart. */
export const SOURCE_CODE: Record<string, string> = {
  wdi: "pipeline/compilador/sources/worldbank.py",
  wgi: "pipeline/compilador/sources/worldbank.py",
  undp_hdr: "pipeline/compilador/sources/undp_hdr.py",
  ibge_sidra: "pipeline/compilador/sources/sidra.py",
  ipeadata: "pipeline/compilador/sources/ipeadata.py",
  vdem: "pipeline/compilador/sources/vdem.py",
};

/** Entities keep the same color on every chart (color follows the entity, not its rank). */
export const GEO_ORDER = ["BRA", "ARG", "CHL", "COL", "MEX", "LCN", "WLD"];

/** Rendered HTML to plain text for <title>, meta tags and attributes. */
export function plain(html: string): string {
  return html
    .replace(/<[^>]+>/g, "")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&amp;/g, "&");
}

export function formatNumber(value: number, lang: Lang, decimals: number): string {
  return new Intl.NumberFormat(lang === "pt" ? "pt-BR" : "en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export const UNIT_DECIMALS: Record<string, number> = {
  index_0_1: 3,
  index_0_100: 1,
  percent: 1,
  usd_2015: 0,
  years: 1,
  per_1000_live_births: 1,
  wgi_estimate: 2,
  brl_month: 0,
  brl_month_real: 0,
  usd_ppp_2021: 0,
  lcu_per_intl_usd: 2,
  lcu_per_usd: 2,
  index_2010_100: 1,
};

export const UNIT_LABELS: Record<string, Record<Lang, string>> = {
  index_0_1: { pt: "índice (0 a 1)", en: "index (0 to 1)" },
  index_0_100: { pt: "índice (0 a 100)", en: "index (0 to 100)" },
  percent: { pt: "%", en: "%" },
  usd_2015: { pt: "US$ de 2015", en: "2015 US$" },
  years: { pt: "anos", en: "years" },
  per_1000_live_births: { pt: "por 1.000 nascidos vivos", en: "per 1,000 live births" },
  wgi_estimate: { pt: "estimativa (≈ −2,5 a +2,5)", en: "estimate (≈ −2.5 to +2.5)" },
  brl_month: { pt: "R$ por mês", en: "R$ per month" },
  brl_month_real: { pt: "R$ por mês, a preços do último ano", en: "R$ per month, at prices of the latest year" },
  usd_ppp_2021: { pt: "US$ PPC de 2021", en: "2021 PPP US$" },
  lcu_per_intl_usd: { pt: "moeda local por US$ internacional", en: "local currency per international $" },
  lcu_per_usd: { pt: "moeda local por US$", en: "local currency per US$" },
  index_2010_100: { pt: "índice (2010 = 100)", en: "index (2010 = 100)" },
};
