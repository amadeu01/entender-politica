# Indicator Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give each indicator page a lay-reader guide (understand, how to read, studies, studied policies, income brackets, purchasing power) plus a standalone "How to read studies" page, piloted on GDP per capita.

**Architecture:** Guides live in `guides/<indicator_id>.yaml`, a content type like `policies/`, loaded, checked and rendered by a new `compilador.guides` module that reuses the policy brief machinery (`analyses.Renderer`, `_text_field_errors`, `Direction`, `Method`). Income-bracket data comes from new catalog indicators (IBGE per capita household income percentiles, World Bank PPP and CPI). A new `compilador.brackets` module turns those into bracket shares and study-group translations, all computed and never typed. The site reads `guides/<id>.<lang>.json` and `income_brackets.json`.

**Tech Stack:** Python 3 (pydantic, pandas, pytest, uv), Astro static site, IBGE SIDRA API, World Bank API v2.

**Spec:** `docs/superpowers/specs/2026-10-26-guia-do-indicador-design.md`

## Global Constraints

- Bilingual pt-BR/en for every user-facing string; use `docs/glossario.yaml` terms (ADR 0004).
- No hand-typed numbers in guide text. Numbers come through `v`/`diff`/`pct`/`cite`/`lit`, and pt and en use the identical data-placeholder sequence (ADR 0007).
- Peer-reviewed studies only, as guide evidence. Every DOI goes through `uv run compilador verify-dois`, and every quoted number is read in the source (abstract, table, page), never recalled.
- No causal claim without a causal design. Never attribute a change to a government (ADR 0003).
- Neutrality: each guide's policy list has at least one null, negative or mixed result, or a `contrary_evidence_search`.
- Brackets: monthly household income **per capita** of up to US$250, 500, 1,000 and 2,000, plus above 2,000 (user's choice after seeing the 2024 distribution), in **2021 PPP dollars** (World Bank household-consumption PPP), with the reais equivalent per year shown. The threshold values live only in `data/reference/faixas-de-renda.yaml`.
- Existing indicator fields (`definition`, `formula`, `criticisms`) stay outside the bare-number check.
- Offline build. New data enters only via `compilador fetch` snapshots.
- Stage explicit paths and never use `git add -A`. Commit messages are Conventional Commits ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Checks: `uv run pytest`, `uv run ruff check . && uv run ruff format --check .`, `uv run compilador build`, `cd site && npm run build`.

## Review Focus

1. **A threshold above IBGE's top published percentile (P99) or below P5.** Expected: the page shows a range ("less than 1%"), never a made-up exact share. Owned by Task 3.
2. **A year that has PNAD data but no CPI or PPP value yet** (WDI lags IBGE). Expected: that year is left out of the bracket table, and a guide translating a study group for that year fails the build with a clear message. Owned by Tasks 3 and 4.
3. **An indicator with no guide file.** Expected: the page renders exactly as today, with no empty headings. Owned by Task 5.
4. **A non-income indicator (V-Dem, WGI, health) whose guide has no `by_income` entries.** Expected: no income or purchasing-power section, so nothing suggests a link (ADR 0003). Owned by Tasks 4 and 5.
5. **A guide whose pt and en texts cite different data, or that contains a bare number.** Expected: the build fails and names the guide file. Owned by Task 4.
6. **A "top 10%" study group.** Expected: it uses the P90 limit, never P10. Owned by Task 4.
7. **A study about years before 2012 (before PNAD Contínua).** Expected: the guide can still cite it. A translation is optional and, when present, uses a 2012+ year the author picks, with both periods shown. Owned by Task 4.

---

### Task 1: SIDRA classification support and unlisted indicators

**Files:**
- Modify: `pipeline/compilador/sources/sidra.py`
- Modify: `pipeline/compilador/catalog.py` (`Indicator`)
- Modify: `site/src/views/Indicators.astro`, `site/src/views/Home.astro`, `site/src/lib/data.ts`
- Test: `pipeline/tests/test_sidra.py`, `pipeline/tests/test_catalog.py`

**Interfaces:**
- Produces: `source_params` keys `classification` and `category` for SIDRA. One request fetches the whole classification (`/c{classification}/all`) into file `{table}-{variable}-c{classification}.json`, shared by every indicator of that table and deduplicated by `_dedupe`. `normalize` keeps the records whose `D4C == category`. Also produces `Indicator.listed: bool = True`; `catalog.json` carries it.

- [ ] **Step 1: Write failing tests**

```python
def test_normalize_filters_by_classification_category(tmp_path):
    # records with D4C 49264 (P50) and 49260 (P10); indicator asks for 49264
    ...
    assert df["value"].tolist() == [1200.0]


def test_fetch_shares_one_file_per_table_classification():
    # two indicators, same table/variable/classification, different category
    files, _ = sidra.fetch([p10, p50], geos, client)
    assert [f.name for f in files].count("7438-10769-c1019.json") == 1


def test_listed_defaults_true_and_can_be_false():
    assert make_indicator().listed is True
    assert make_indicator(listed=False).listed is False
```

- [ ] **Step 2: Run** `uv run pytest pipeline/tests/test_sidra.py pipeline/tests/test_catalog.py -v`. Expected: the new tests FAIL.
- [ ] **Step 3: Implement.** Without `classification`, URLs and file names must stay byte-identical to today, so the Gini snapshot keeps working.
- [ ] **Step 4: Filter the index and home pages.** `Indicators.astro` and the count in `Home.astro` use only `listed !== false`. Add `listed?: boolean` to the `Indicator` type in `site/src/lib/data.ts`. The page `/indicadores/<id>/` still exists for unlisted indicators.
- [ ] **Step 5: Run** the full test suite. Expected: PASS.
- [ ] **Step 6: Commit** `feat(pipeline): support SIDRA classification categories and unlisted indicators`.

### Task 2: New catalog indicators for income distribution and purchasing power

**Files:**
- Create: `indicators/ibge_sidra.rdpc_p{05,10,20,30,40,50,60,70,80,90,95,99}_pnadc.yaml` (12 files, `listed: false`)
- Create: `indicators/ibge_sidra.rdpc_mediana_real_pnadc.yaml`
- Create: `indicators/ibge_sidra.trabalho_mediana_real_pnadc.yaml`
- Create: `indicators/wdi.ny_gdp_pcap_pp_kd.yaml`, `indicators/wdi.pa_nus_prvt_pp.yaml`, `indicators/wdi.pa_nus_fcrf.yaml`, `indicators/wdi.fp_cpi_totl.yaml`
- Modify: `pipeline/compilador/content.py` (`UNIT_DECIMALS`), `site/src/lib/i18n.ts` (`UNIT_LABELS`)
- Snapshots: `data/raw/ibge_sidra/<date>/`, `data/raw/wdi/<date>/`

**Interfaces:**
- Produces these indicator ids, used by Task 3:

| id | source | params / code | unit |
|---|---|---|---|
| `ibge_sidra.rdpc_pNN_pnadc` | SIDRA 7438, var 10769, cv 10837, classification 1019, category P5=49259, P10=49260, P20=49261 … P90=49268, P95=49269, P99=49270 | — | `brl_month` |
| `ibge_sidra.rdpc_mediana_real_pnadc` | SIDRA 7526, var 10838, cv 10839, classification 1019, category 49264 | — | `brl_month_real` |
| `ibge_sidra.trabalho_mediana_real_pnadc` | SIDRA 7540 (labor income habitually received, prices of the latest year), classification 1043, category P50 (look up the variable and category ids via `https://servicodados.ibge.gov.br/api/v3/agregados/7540/metadados`; table 7536 has P50 = 49304) | — | `brl_month_real` |
| `wdi.ny_gdp_pcap_pp_kd` | WDI | `NY.GDP.PCAP.PP.KD` | `usd_ppp_2021` |
| `wdi.pa_nus_prvt_pp` | WDI | `PA.NUS.PRVT.PP` | `lcu_per_intl_usd` (`listed: false`) |
| `wdi.pa_nus_fcrf` | WDI | `PA.NUS.FCRF` | `lcu_per_usd` (`listed: false`) |
| `wdi.fp_cpi_totl` | WDI | `FP.CPI.TOTL` | `index_2010_100` (`listed: false`) |

Verified ids: table 7540 has variable 10846, CV 10847, classification 1043, P50 = 49304. Each SIDRA `source_code` is `"<table>/<variable>/<category>"` (e.g. `"7438/10769/49264"`). All 14 SIDRA indicators copy Gini's `series_breaks` for 2020 and 2022 (fifth-visit income).

- [ ] **Step 1: Generate the 12 percentile YAMLs** with a throwaway script (don't commit the script). They share one bilingual definition, criticism and reference, citing IBGE's PNAD Contínua methodology note by URL, with `min: 0`. Write the other six by hand. Each needs `criticisms` and `references` (URL allowed), and the WDI ones point at the World Bank metadata page.
- [ ] **Step 2: Add units.** Decimals: `brl_month` 0, `brl_month_real` 0, `usd_ppp_2021` 0, `lcu_per_intl_usd` 2, `lcu_per_usd` 2, `index_2010_100` 1. Set them in both `UNIT_DECIMALS` maps (`content.py` and `site/src/lib/i18n.ts`) and add pt/en labels to `UNIT_LABELS`. The `brl_month_real` label says "reais at prices of the latest year" and does not type a year; the page reads the price year from the latest year in the series.
- [ ] **Step 3: Fetch.** Run `uv run compilador fetch ibge_sidra wdi`. Expected: snapshot written, and all four WDI codes return Brazil rows (if `PA.NUS.FCRF` is empty, stop and report).
- [ ] **Step 4: Build and test.** Run `uv run compilador build && uv run pytest`. Expected: PASS. Review new validation warnings in `data/processed/validation.json`; tune `min`/`max` if a warning is a false alarm (ADR 0009). Expect about 84 new "no observations" warnings for non-Brazil geographies of the Brazil-only SIDRA series; that is normal.
- [ ] **Step 5: Commit** the YAMLs, snapshots, unit changes and `data/CHANGELOG.md`: `feat(data): add income percentiles, medians and PPP series`. The fetch also refreshes the 7 existing WDI series; say so in the commit body if values were revised.

### Task 3: Income brackets module

**Files:**
- Create: `data/reference/faixas-de-renda.yaml`
- Create: `pipeline/compilador/brackets.py`
- Modify: `pipeline/compilador/build.py` (`export_site` writes `income_brackets.json`)
- Test: `pipeline/tests/test_brackets.py`

**Interfaces:**
- Consumes: the indicator ids from Task 2 and the observations DataFrame.
- Produces:
  - `Config` (pydantic) loaded by `load(path=BRACKETS_FILE) -> Config`, with fields:
    - `ppp_base_year: int` (2021);
    - `thresholds_usd_ppp: list[int]` (`[250, 500, 1000, 2000]`);
    - `percentile_indicators: dict[int, str]` (`{5: "ibge_sidra.rdpc_p05_pnadc", …}`);
    - `ppp_indicator: str`;
    - `cpi_indicator: str`;
    - `income_indicators: list[str]`, the guides that always show the income and purchasing-power sections: `wdi.ny_gdp_pcap_kd`, `wdi.fp_cpi_totl_zg`, `wdi.si_pov_dday`, `wdi.si_pov_gini`, `ibge_sidra.gini_pnadc`, `ipeadata.disoc_ppy`, `ipeadata.disoc_rdcg`, `undp_hdr.hdi`, `undp_hdr.ihdi`.
  - `Share(low: float, high: float)`: a percent of people. `low == high` is a **point estimate by linear interpolation** between IBGE percentiles, not an exact value. The page and `income_brackets.json` (`"method": "linear_interpolation"`) say so.
  - `reais_per_usd_ppp(df, config, year) -> float | None` returns `PPP[base] * CPI[year] / CPI[base]`, or `None` when any input is missing.
  - `share_below(limits: dict[int, float], value: float) -> Share` interpolates linearly between known `(percentile, limit)` points. It returns `Share(0, 5)` when `value < limits[5]` and `Share(99, 100)` when `value > limits[99]`. When two adjacent percentiles have the same limit and `value` equals it, it returns `Share(lower_pct, upper_pct)` instead of dividing by zero.
  - `distribution(df, config) -> list[dict]`, one dict per year that has all inputs: `{"year", "reais_per_usd_ppp", "thresholds_brl": [..], "brackets": [{"label": "ate_250"|"ate_500"|"ate_1000"|"ate_2000"|"acima_2000", "low", "high"}]}`. A bracket's share is `(F_hi.low − F_lo.high, F_hi.high − F_lo.low)`, clipped at 0. `ate_250` uses `F_lo = Share(0, 0)` and `acima_2000` uses `F_hi = Share(100, 100)`.
  - `translate(df, config, cut: int, side: Literal["bottom", "top"], year: int) -> dict` returns `{"cut", "side", "year", "limit_brl", "limit_usd_ppp", "bracket"}`. `cut` is always the **percentile cut point**: "bottom 40%" is `cut=40, side="bottom"` (people below P40); "top 10%" is `cut=90, side="top"` (people above P90). For `bottom`, `bracket` is the one containing the group's upper limit; for `top`, the one where the group starts. It raises `BracketError` when the year lacks data or `cut` is not in `percentile_indicators`.
  - `load` raises when an id in `percentile_indicators`, `ppp_indicator`, `cpi_indicator` or `income_indicators` is not in the catalog, and when the WDI snapshot's name for `ppp_indicator`'s companion `wdi.ny_gdp_pcap_pp_kd` does not contain `ppp_base_year` (guards against WDI moving to a new ICP round).
  - Deferred, recorded in ADR 0011: decile groups not bounded by a published percentile, and poverty-line groups (a natural fit for `share_below`).

- [ ] **Step 1: Write failing tests**

```python
LIMITS = {
    5: 300,
    10: 450,
    20: 700,
    30: 900,
    40: 1100,
    50: 1300,
    60: 1600,
    70: 2000,
    80: 2700,
    90: 4200,
    95: 6500,
    99: 15000,
}


def test_share_below_interpolates():
    assert share_below(LIMITS, 1200) == Share(45.0, 45.0)


def test_share_below_above_p99_is_a_range():
    assert share_below(LIMITS, 20000) == Share(99, 100)


def test_share_below_under_p5_is_a_range():
    assert share_below(LIMITS, 100) == Share(0, 5)


def test_reais_per_usd_ppp_uses_base_ppp_and_cpi_ratio(df):
    # PPP 2021 = 2.45, CPI 2021 = 100, CPI 2024 = 120
    assert reais_per_usd_ppp(df, config, 2024) == pytest.approx(2.94)


def test_year_without_cpi_is_skipped(df_missing_cpi_2025):
    assert 2025 not in [d["year"] for d in distribution(df_missing_cpi_2025, config)]


def test_translate_bottom_40_maps_limit_to_bracket(df):
    t = translate(df, config, 40, "bottom", 2024)
    assert t["bracket"] == "ate_500" and t["limit_usd_ppp"] == pytest.approx(1100 / 2.94)


def test_translate_year_without_data_raises(df):
    with pytest.raises(BracketError, match="2011"):
        translate(df, config, 40, "bottom", 2011)


def test_translate_top_10_uses_p90(df):
    t = translate(df, config, 90, "top", 2024)
    assert t["limit_brl"] == LIMITS[90]


def test_tied_percentiles_do_not_divide_by_zero():
    assert share_below({**LIMITS, 20: 450}, 450) == Share(10, 20)


def test_real_2024_shares():
    # table 7438 2024 percentiles, PPP 2021 = 2.4499, CPI 2024 = 223.216, CPI 2021 = 187.117
    # P5..P99 = 276, 405, 626, 815, 1029, 1328, 1526, 1964, 2607, 4026, 6027, 13316
    b = distribution(real_2024_df, config)[-1]["brackets"]
    assert [round(x["low"], 1) for x in b] == [25.5, 31.2, 25.5, 12.3, 5.5]
    assert all(x["low"] == x["high"] for x in b)
```

- [ ] **Step 2: Run** `uv run pytest pipeline/tests/test_brackets.py -v`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** `brackets.py` and the YAML. Add `BRACKETS_FILE = DATA_DIR / "reference" / "faixas-de-renda.yaml"` and `Paths.brackets`. Build the `real_2024_df` fixture from the real values (fetch them once from SIDRA table 7438 and copy them into the test).
- [ ] **Step 4: Export.** `export_site` writes `income_brackets.json` = `{"config": {...}, "years": distribution(...), "sources": [...]}`, where `sources` holds each input indicator's `source_id`, `source_version` and `retrieved_at`, taken from the observations. Like `period_changes`, it is skipped when the input indicators are not in the catalog, so existing `test_build` fixtures keep passing. Add a test in `test_build.py` that the file exists after a build with the inputs present.
- [ ] **Step 5: Run** `uv run pytest && uv run compilador build`. Expected: PASS. Spot-check 2024 in `site/public/data/income_brackets.json`: about 25.5 / 31.2 / 25.5 / 12.3 / 5.5%.
- [ ] **Step 6: Commit** `feat(pipeline): compute per capita income bracket shares in PPP dollars`.

### Task 4: Guide content type

**Files:**
- Create: `pipeline/compilador/guides.py`
- Create: `guides/` (empty folder with `.gitkeep`)
- Modify: `pipeline/compilador/analyses.py` (extract `evidence_level(methods: set[Method]) -> str` and `needs_contrary_search(directions) -> bool` from `Policy`; `Policy` calls them, behavior unchanged)
- Modify: `pipeline/compilador/build.py` (`Paths.guides`, `compile_documents`, `all_dois`, `citation_errors`)
- Test: `pipeline/tests/test_guides.py`

**Interfaces:**
- Consumes: `analyses.Strict`, `Period`, `Direction`, `Method`, `Renderer`, `_text_field_errors`, `_texts`, `_reference_errors`, `content.Resolver`; `brackets.translate`, `brackets.load`.
- Produces:
  - `IncomeGroup(cut: int, side: Literal["bottom", "top"], year: int)`, with `cut` meaning the same as in `brackets.translate` and `year` ≥ 2012
  - `IncomeEffect(text: Text, study_period: Period, group: IncomeGroup | None = None, references: list[str])` (min 1). Translation is optional. When `group` is present and its year falls outside `study_period`, the page shows both periods.
  - `StudyEntry(text: Text, method: Method, references: list[str])`. Studies about the indicator show their design but **no evidence level** (ADR 0007 §6 rates policy-effect claims). The neutrality rule applies to `policies` only; ADR 0011 says so.
  - `PolicyEntry(name: Text, country: str (ISO3), period: Period, result: Text, direction: Direction, method: Method, references: list[str], brief: str | None)`, where `brief` is a policy slug
  - `Guide(indicator: str, understand: Text, how_to_read: Text, studies: list[StudyEntry] (min 1), policies: list[PolicyEntry] (min 1), by_income: list[IncomeEffect] = [], purchasing_power: Text | None, contrary_evidence_search: Text | None, references: list[Reference] (min 1))`. Its validator applies `needs_contrary_search` over the policy directions.
  - `load_guides(directory=GUIDES_DIR) -> list[Guide]` (file stem must equal `indicator`)
  - `check(guides, indicators, policy_slugs) -> list[str]`
  - `render_guide(g, lang, df, indicators, registry, brackets_config) -> dict`. Keys: `indicator`, `lang`, `understand`, `how_to_read`, `studies[]` (with `method`), `policies[]` (with `evidence_level`, `brief`), `by_income[]` (each with `translation` from `brackets.translate`, or `null` without a group), `show_income` (`indicator in config.income_indicators or bool(by_income)`), `purchasing_power`, `contrary_evidence_search`, `references_indicator` (DOIs cited only in `studies`), `references_policies` (all the others), `numbers`.
  - The build writes `guides/{indicator}.{lang}.json` and adds `"guides": [indicator ids]` to `documents.json`.

- [ ] **Step 1: Write failing tests**

```python
def test_guide_for_unknown_indicator_is_rejected(): ...  # "not in catalog"
def test_guide_file_name_must_match_indicator(tmp_path): ...
def test_bare_number_in_guide_text_is_rejected(): ...  # error names guides/<id>.yaml
def test_guide_translations_must_cite_same_data(): ...
def test_only_positive_policies_need_contrary_search(): ...
def test_policy_entry_brief_must_exist(): ...
def test_entry_cites_reference_not_listed_is_rejected(): ...
def test_show_income_false_for_non_income_indicator_without_effects(): ...
def test_by_income_translation_is_computed(): ...  # bracket in rendered dict
def test_by_income_year_without_data_fails_build(): ...  # ValidationError mentions year
def test_by_income_without_group_renders_null_translation(): ...
def test_top_10_group_translates_with_p90(): ...
def test_references_split_by_where_cited(): ...
def test_policy_evidence_level_unchanged_after_refactor(): ...  # existing test still passes
```

- [ ] **Step 2: Run** `uv run pytest pipeline/tests/test_guides.py -v`. Expected: FAIL.
- [ ] **Step 3: Refactor** `analyses.py` (helper extraction only), then run `uv run pytest pipeline/tests/test_analyses.py`. Expected: PASS.
- [ ] **Step 4: Implement** `guides.py` and wire it into `build.py`. Guide DOIs are included in `all_dois` and `citation_errors`. A `BracketError` or `ContentError` raised during rendering becomes a `ValidationError`.
- [ ] **Step 5: Run** `uv run pytest && uv run compilador build`. Expected: PASS (no guides yet, so no guide JSON written).
- [ ] **Step 6: Commit** `feat(pipeline): add indicator guide content type`.

### Task 5: Guide sections on the indicator page

Load the `dataviz` skill before touching the bracket display.

**Files:**
- Modify: `site/src/lib/data.ts` (`guide(id, lang): Guide | null`, which returns null when the file is missing; `incomeBrackets()`)
- Create: `site/src/components/IncomeBrackets.astro`
- Modify: `site/src/views/Indicator.astro`, `site/src/lib/i18n.ts` (section titles, bracket labels, "between a% and b%", "less than", direction and evidence-level names reused from Policy)

**Interfaces:**
- Consumes: the Task 4 JSON shape and the Task 3 `income_brackets.json`.
- Produces: page section order: Understand, How to read, (existing definition/facts/chart), Pitfalls (existing criticisms), What studies say, Studied policies (link to `/politicas/<brief>/` when `brief` is set), By income bracket (only if `show_income`), Purchasing power (only if `show_income` and `purchasing_power` is set), References (guide references first under "Policies and impacts", existing ones under "About the indicator"), Numbers (`Numbers` component).

- [ ] **Step 0: Record the baseline.** Before editing, build the site and save `grep -c "<h2" dist/indicadores/wdi.ny_gdp_pcap_kd/index.html`.
- [ ] **Step 1: Write the data helpers and the component.** `IncomeBrackets` shows, for the latest year: a table of bracket, threshold in reais, and share of people (a range when `low != high`), plus a line with `reais_per_usd_ppp` and the sources/retrieval dates. Below the table, `Chart` shows `ibge_sidra.rdpc_mediana_real_pnadc` and `ibge_sidra.trabalho_mediana_real_pnadc` for BRA (median person and median worker, real reais), so the reader sees the typical income beside the brackets. The chart caption names the price year, read from the latest year in the series.
  - **Over time:** a second view shows each bracket's share for every year in `income_brackets.json`; ranges are drawn as ranges.
  - Every share carries the note "≈ estimated by linear interpolation between IBGE percentiles".
  - When `show_income` is true and `by_income` is empty, the section says no peer-reviewed study by income group was found for this indicator.
  - **Purchasing power:** besides the guide's `purchasing_power` text, `Chart` shows `wdi.ny_gdp_pcap_pp_kd` beside `wdi.ny_gdp_pcap_kd` for all the site's geographies, so the reader can compare countries in cost-of-living-adjusted terms. Each `by_income` item shows the study text and the translation box: original group, year, the limit in R$ and in US$ PPP, and the matching bracket.
- [ ] **Step 2: Build** with `cd site && npm run build`. Expected: PASS, and every existing indicator page's HTML has no new headings (no guides exist yet). Check: `grep -c "<h2" dist/indicadores/wdi.ny_gdp_pcap_kd/index.html` equals the Step 0 count.
- [ ] **Step 3: Commit** `feat(site): render indicator guides and income brackets`.

### Task 6: "How to read studies" page

**Files:**
- Create: `site/src/views/ReadingStudies.astro`, `site/src/pages/como-ler-estudos/index.astro`, `site/src/pages/en/reading-studies/index.astro`
- Modify: `site/src/lib/i18n.ts` (`ROUTES.studies = { pt: "como-ler-estudos", en: "reading-studies" }`, nav label), `site/src/views/Indicator.astro` (link from the studies section), `site/src/views/Methodology.astro` (link)

**Interfaces:**
- Produces: route `studies`, linked from every guide's "What studies say" heading.

- [ ] **Step 1: Write the bilingual text** inline, following `Methodology.astro`. Cover:
  - each design in `Method` and what it can and cannot show;
  - systematic review and meta-analysis;
  - effect size;
  - confidence interval;
  - p-value and what "significant" means;
  - external validity;
  - peer reviewed versus working paper, and why the site uses only peer-reviewed studies;
  - conflict of interest;
  - the evidence levels (ADR 0007 §6).

  Each concept gets an example: a link to a policy brief where one uses that design, otherwise a study cited in the pilot guide (Task 7 adds them back here if Task 6 runs first). Numbers such as "95%" or "0.05" are allowed: the page is inline Astro, outside `content.py`, and explaining them is the point.
- [ ] **Step 2: Build** with `cd site && npm run build`. Expected: PASS, and both pages exist in `dist/`.
- [ ] **Step 3: Commit** `feat(site): add how to read studies page`.

### Task 7: Pilot guide for GDP per capita

**Files:**
- Create: `guides/wdi.ny_gdp_pcap_kd.yaml`
- Modify: `data/reference/dois.json` (via `verify-dois`)

- [ ] **Step 1: Research.** Use the `research` skill or a research agent to find peer-reviewed studies on:
  - (a) GDP per capita versus welfare and social progress (keep Jones & Klenow 2016);
  - (b) policies studied as moving GDP per capita or growth, in Brazil and elsewhere, including null or mixed results;
  - (c) how growth reached different income groups in Brazil (growth incidence; studies by decile or by bottom 40%).

  Record the DOI and the exact passage read for each study.
- [ ] **Step 2: Verify.** Run `uv run compilador verify-dois` after adding the references. Expected: every DOI verified, and citation years match Crossref.
- [ ] **Step 3: Write the guide.**
  - `understand`, `how_to_read` (with a real `v`/`pct` example for BRA), at least 2 `studies`, at least 3 `policies` (Brazil and elsewhere, at least one not positive), and `by_income` items only where a study reports results by group. Pre-2012 studies keep `study_period` and either omit `group` or translate to a 2012+ year.
  - `purchasing_power` uses `v("wdi.pa_nus_prvt_pp", "BRA", Y)` beside `v("wdi.pa_nus_fcrf", "BRA", Y)`, `v("wdi.ny_gdp_pcap_pp_kd", …)`, and the change in the real median from `ibge_sidra.rdpc_mediana_real_pnadc` via `pct`/`diff` only (its price base moves every IBGE release, so `v` of a past year would go stale).
  - No causal wording for observational studies.
- [ ] **Step 4: Build and check.** Run `uv run compilador build && cd site && npm run build`, then render the page with `google-chrome-stable --headless=new --screenshot=...` against `npx astro preview`, in pt and en. Expected: all sections present; 2024 bracket shares match the Task 3 spot-check.
- [ ] **Step 5: Review.** Dispatch a reviewer to check every `cite` against its source passage and to look for causal wording and one-sided selection. Fix valid findings.
- [ ] **Step 6: Commit** `content: add GDP per capita guide`.

### Task 8: ADR and docs

**Files:**
- Create: `docs/adr/0011-guias-dos-indicadores.md` (bilingual, template `0000`)
- Modify: `CONTRIBUTING.md` (how to write a guide), `docs/glossario.yaml` (new terms: "faixa de renda" / "income bracket", "paridade do poder de compra (PPC)" / "purchasing power parity (PPP)", "renda domiciliar per capita" / "household income per capita", "percentil" / "percentile")

- [ ] **Step 1: Write the ADR.** Record:
  - guides as a content type;
  - per capita household income brackets in 2021 PPP dollars, deflated by CPI, and the deviation from total household income (microdata deferred);
  - study-group translation, computed and shown;
  - peer-reviewed only;
  - when income sections show;
  - bracket shares and limits are derived numbers shown outside the `v`/`cite` markers, traced through `income_brackets.json` `sources` (precedent: `period_changes`);
  - fixed parameters: PPP base year 2021, linear interpolation, the cut-point convention for study groups;
  - neutrality applies to studied policies, not to studies about the measure;
  - deferred: decile and poverty-line groups, sampling uncertainty of shares.
- [ ] **Step 2: Run** `uv run ruff check . && uv run ruff format --check . && uv run pytest`. Expected: PASS.
- [ ] **Step 3: Commit** `docs: record indicator guide decisions`.

After Task 8: open the PR (`superpowers:finishing-a-development-branch`), run the two-axis review (`code-review`), fix, merge. The other 16 guides follow in batches as separate plans or PRs.
