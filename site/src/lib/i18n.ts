export type Lang = "pt" | "en";
export const LANGS: Lang[] = ["pt", "en"];

export const ROUTES = {
  home: { pt: "", en: "" },
  brazil: { pt: "brasil", en: "brazil" },
  indicators: { pt: "indicadores", en: "indicators" },
  analyses: { pt: "analises", en: "analyses" },
  policies: { pt: "politicas", en: "policies" },
  methodology: { pt: "metodologia", en: "methodology" },
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
