// Build-time access to the files the pipeline writes to public/data (`compilador build`).
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { Lang } from "./i18n";

const DATA_DIR = join(process.cwd(), "public", "data");

function read<T>(path: string): T {
  const file = join(DATA_DIR, path);
  if (!existsSync(file)) {
    throw new Error(`${file} not found: run \`uv run compilador build\` first`);
  }
  return JSON.parse(readFileSync(file, "utf-8")) as T;
}

export type Text = { pt: string; en: string };
export type Reference = { citation: string; doi: string | null; url: string | null };
export type Indicator = {
  id: string;
  source: string;
  source_code: string;
  name: Text;
  unit: string;
  definition: Text;
  formula: Text;
  uncertainty: Text | null;
  criticisms: Text[];
  references: Reference[];
  series_breaks: { year: number; geo: string | null; note: Text }[];
  listed?: boolean;
};
export type Geography = { code: string; level: string; name: Text };
export type Period = {
  id: string;
  president: string;
  short_name: string;
  condition: "titular" | "interino";
  term: Text;
  start: string;
  end: string | null;
  note: Text | null;
};
export type Observation = {
  geo_code: string;
  year: number;
  value: number;
  lower: number | null;
  upper: number | null;
  series_break: boolean;
};
export type Series = {
  indicator_id: string;
  unit: string;
  source_id: string;
  source_version: string;
  retrieved_at: string;
  license: string;
  observations: Observation[];
};
export type Cited = {
  ref: number;
  text: string;
  function: "v" | "diff" | "pct" | "cite" | "lit";
  args: (string | number)[];
  indicator_id: string | null;
  source_id: string | null;
  source_version: string | null;
  retrieved_at: string | null;
  doi: string | null;
  note: string | null;
};
export type RenderedReference = Reference & { bibtex: string | null };
export type ChartSpec = {
  id: string;
  title: string;
  alt: string;
  indicators: string[];
  geographies: string[];
  log_scale: boolean;
};
export type Analysis = {
  slug: string;
  lang: Lang;
  title: string;
  question: string;
  hypothesis: string;
  result: string;
  indicators: string[];
  period: { start: number; end: number };
  method: string;
  method_description: string;
  causal_claims: boolean;
  body: string;
  evidence_for: { text: string; references: string[] }[];
  evidence_against: { text: string; references: string[] }[];
  limitations: string[];
  charts: ChartSpec[];
  related_policies: string[];
  references: RenderedReference[];
  numbers: Cited[];
};
export type Policy = {
  slug: string;
  lang: Lang;
  name: string;
  country: string;
  period: { start: number; end: number };
  evidence_level: "high" | "moderate" | "low";
  summary: string;
  mechanism: string;
  findings: {
    outcome: string;
    result: string;
    direction: "positive" | "null" | "negative" | "mixed";
    method: string;
    references: string[];
  }[];
  external_validity: string;
  limitations: string[];
  contrary_evidence_search: string | null;
  references: RenderedReference[];
  numbers: Cited[];
};
export type PeriodChange = {
  period_id: string;
  indicator_id: string;
  geo_code: string;
  lag: number;
  start_year: number;
  end_year: number;
  change: number | null;
  relative: boolean;
  mixed_years: number[];
};
export type Translation = {
  cut: number;
  side: "bottom" | "top";
  year: number;
  limit_brl: number;
  limit_usd_ppp: number;
  bracket: string;
};
export type Guide = {
  indicator: string;
  lang: Lang;
  understand: string;
  how_to_read: string;
  studies: { text: string; method: string; references: string[] }[];
  policies: {
    name: string;
    country: string;
    period: { start: number; end: number };
    result: string;
    direction: "positive" | "null" | "negative" | "mixed";
    method: string;
    evidence_level: "high" | "moderate" | "low";
    brief: string | null;
    references: string[];
  }[];
  by_income: {
    text: string;
    study_period: { start: number; end: number };
    references: string[];
    translation: Translation | null;
  }[];
  show_income: boolean;
  purchasing_power: string | null;
  contrary_evidence_search: string | null;
  references_indicator: RenderedReference[];
  references_policies: RenderedReference[];
  numbers: Cited[];
};
export type IncomeBrackets = {
  config: {
    thresholds_usd_ppp: number[];
    ppp_base_year: number;
    labels: string[];
    method: string;
    percentile_indicators: Record<string, string>;
  };
  years: {
    year: number;
    reais_per_usd_ppp: number;
    thresholds_brl: number[];
    brackets: { label: string; low: number; high: number }[];
  }[];
  sources: { indicator_id: string; source_id: string; source_version: string; retrieved_at: string }[];
};
type Documents = {
  analyses: { slug: string; lang: Lang; title: string }[];
  policies: { slug: string; lang: Lang; name: string; country: string }[];
  guides: string[];
};

export const catalog = (): Indicator[] => read("catalog.json");
export const indicator = (id: string): Indicator => {
  const found = catalog().find((i) => i.id === id);
  if (!found) throw new Error(`indicator ${id} not in catalog`);
  return found;
};
export const geographies = (): Geography[] => read("geographies.json");
export const governments = (): { sources: string[]; periods: Period[] } => read("governments.json");
export const series = (id: string): Series => read(`series/${id}.json`);
export const documents = (): Documents => read("documents.json");
export const analysis = (slug: string, lang: Lang): Analysis => read(`analyses/${slug}.${lang}.json`);
export const policy = (slug: string, lang: Lang): Policy => read(`policies/${slug}.${lang}.json`);
/** The guide of an indicator, or null when it has none. Stale files left by an old build are ignored. */
export const guide = (id: string, lang: Lang): Guide | null =>
  documents().guides.includes(id) ? read(`guides/${id}.${lang}.json`) : null;
export const incomeBrackets = (): IncomeBrackets | null =>
  existsSync(join(DATA_DIR, "income_brackets.json")) ? read("income_brackets.json") : null;
export const periodChanges = (): PeriodChange[] => read("period_changes.json");

export const geoName = (code: string, lang: Lang): string =>
  geographies().find((g) => g.code === code)?.name[lang] ?? code;
