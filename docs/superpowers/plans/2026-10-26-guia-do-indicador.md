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
- Brackets: monthly household income **per capita** of up to US$1,000, 2,000, 5,000 and 10,000, plus above 10,000, in **2021 PPP dollars** (World Bank household-consumption PPP), with the reais equivalent per year shown. The threshold values live only in `data/reference/faixas-de-renda.yaml`.
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

---

### Task 1: SIDRA classification support and unlisted indicators

**Files:**
- Modify: `pipeline/compilador/sources/sidra.py`
- Modify: `pipeline/compilador/catalog.py` (`Indicator`)
- Modify: `site/src/views/Indicators.astro`
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
- [ ] **Step 4: Filter the index page.** `Indicators.astro` lists only `listed !== false`. The page `/indicadores/<id>/` still exists for unlisted indicators.
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
| `wdi.pa_nus_prvt_pp` | WDI | `PA.NUS.PRVT.PP` | `lcu_per_intl_usd` |
| `wdi.pa_nus_fcrf` | WDI | `PA.NUS.FCRF` | `lcu_per_usd` |
| `wdi.fp_cpi_totl` | WDI | `FP.CPI.TOTL` | `index_2010_100` |

- [ ] **Step 1: Generate the 12 percentile YAMLs** with a throwaway script (don't commit the script). They share one bilingual definition, criticism and reference, citing IBGE's PNAD Contínua methodology note by URL, with `min: 0`. Write the other six by hand. Each needs `criticisms` and `references` (URL allowed), and the WDI ones point at the World Bank metadata page.
- [ ] **Step 2: Add units.** Decimals: `brl_month` 0, `brl_month_real` 0, `usd_ppp_2021` 0, `lcu_per_intl_usd` 2, `lcu_per_usd` 2, `index_2010_100` 1. Add matching pt/en labels to `UNIT_LABELS`.
- [ ] **Step 3: Fetch.** Run `uv run compilador fetch ibge_sidra wdi`. Expected: snapshot written, and all four WDI codes return Brazil rows (if `PA.NUS.FCRF` is empty, stop and report).
- [ ] **Step 4: Build and test.** Run `uv run compilador build && uv run pytest`. Expected: PASS. Review new validation warnings in `data/processed/validation.json`; tune `min`/`max` if a warning is a false alarm (ADR 0009).
- [ ] **Step 5: Commit** the YAMLs, snapshots, unit changes and `data/CHANGELOG.md`: `feat(data): add income percentiles, medians and PPP series`.

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
    - `thresholds_usd_ppp: list[int]` (`[1000, 2000, 5000, 10000]`);
    - `percentile_indicators: dict[int, str]` (`{5: "ibge_sidra.rdpc_p05_pnadc", …}`);
    - `ppp_indicator: str`;
    - `cpi_indicator: str`;
    - `income_indicators: list[str]`, the guides that always show the income and purchasing-power sections: `wdi.ny_gdp_pcap_kd`, `wdi.fp_cpi_totl_zg`, `wdi.si_pov_dday`, `wdi.si_pov_gini`, `ibge_sidra.gini_pnadc`, `ipeadata.disoc_ppy`, `ipeadata.disoc_rdcg`, `undp_hdr.hdi`, `undp_hdr.ihdi`.
  - `Share(low: float, high: float)`: a percent of people, where `low == high` when exact.
  - `reais_per_usd_ppp(df, config, year) -> float | None` returns `PPP[base] * CPI[year] / CPI[base]`, or `None` when any input is missing.
  - `share_below(limits: dict[int, float], value: float) -> Share` interpolates linearly between known `(percentile, limit)` points. It returns `Share(0, 5)` when `value < limits[5]` and `Share(99, 100)` when `value > limits[99]`.
  - `distribution(df, config) -> list[dict]`, one dict per year that has all inputs: `{"year", "reais_per_usd_ppp", "thresholds_brl": [..], "brackets": [{"label": "ate_1000"|…|"acima_10000", "low", "high"}]}`. A bracket's share is `(F_hi.low − F_lo.high, F_hi.high − F_lo.low)`, clipped at 0.
  - `translate(df, config, percentile: int, side: Literal["bottom", "top"], year: int) -> dict` returns `{"percentile", "side", "year", "limit_brl", "limit_usd_ppp", "bracket"}`. It raises `BracketError` when the year lacks data or the percentile is not in `percentile_indicators`.

- [ ] **Step 1: Write failing tests**

```python
LIMITS = {5: 300, 10: 450, 20: 700, 30: 900, 40: 1100, 50: 1300, 60: 1600,
          70: 2000, 80: 2700, 90: 4200, 95: 6500, 99: 15000}

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
    assert t["bracket"] == "ate_1000" and t["limit_usd_ppp"] == pytest.approx(1100 / 2.94)

def test_translate_year_without_data_raises(df):
    with pytest.raises(BracketError, match="2011"):
        translate(df, config, 40, "bottom", 2011)

def test_bracket_shares_cover_everyone(df):
    b = distribution(df, config)[-1]["brackets"]
    assert sum(x["low"] for x in b) <= 100 <= sum(x["high"] for x in b)
```

- [ ] **Step 2: Run** `uv run pytest pipeline/tests/test_brackets.py -v`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** `brackets.py` and the YAML. Add `BRACKETS_FILE = DATA_DIR / "reference" / "faixas-de-renda.yaml"`.
- [ ] **Step 4: Export.** `export_site` writes `income_brackets.json` = `{"config": {...}, "years": distribution(...), "sources": [...]}`, where `sources` holds each input indicator's `source_id`, `source_version` and `retrieved_at`, taken from the observations. Add a test in `test_build.py` that the file exists after the build.
- [ ] **Step 5: Run** `uv run pytest && uv run compilador build`. Expected: PASS. Spot-check the latest year in `site/public/data/income_brackets.json`; under the Global Constraints values, most people should fall in the first bracket.
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
  - `IncomeGroup(percentile: int, side: Literal["bottom", "top"], year: int)`
  - `IncomeEffect(text: Text, group: IncomeGroup, references: list[str])` (min 1)
  - `StudyEntry(text: Text, method: Method, references: list[str])`
  - `PolicyEntry(name: Text, country: str (ISO3), period: Period, result: Text, direction: Direction, method: Method, references: list[str], brief: str | None)`, where `brief` is a policy slug
  - `Guide(indicator: str, understand: Text, how_to_read: Text, studies: list[StudyEntry] (min 1), policies: list[PolicyEntry] (min 1), by_income: list[IncomeEffect] = [], purchasing_power: Text | None, contrary_evidence_search: Text | None, references: list[Reference] (min 1))`. Its validator applies `needs_contrary_search` over the policy directions.
  - `load_guides(directory=GUIDES_DIR) -> list[Guide]` (file stem must equal `indicator`)
  - `check(guides, indicators, policy_slugs) -> list[str]`
  - `render_guide(g, lang, df, indicators, registry, brackets_config) -> dict`. Keys: `indicator`, `lang`, `understand`, `how_to_read`, `studies[]` (with `evidence_level`), `policies[]` (with `evidence_level`, `brief`), `by_income[]` (each with `translation` from `brackets.translate`), `show_income` (`indicator in config.income_indicators or bool(by_income)`), `purchasing_power`, `contrary_evidence_search`, `references`, `numbers`.
  - The build writes `guides/{indicator}.{lang}.json` and adds `"guides": [indicator ids]` to `documents.json`.

- [ ] **Step 1: Write failing tests**

```python
def test_guide_for_unknown_indicator_is_rejected(): ...        # "not in catalog"
def test_guide_file_name_must_match_indicator(tmp_path): ...
def test_bare_number_in_guide_text_is_rejected(): ...           # error names guides/<id>.yaml
def test_guide_translations_must_cite_same_data(): ...
def test_only_positive_policies_need_contrary_search(): ...
def test_policy_entry_brief_must_exist(): ...
def test_entry_cites_reference_not_listed_is_rejected(): ...
def test_show_income_false_for_non_income_indicator_without_effects(): ...
def test_by_income_translation_is_computed(): ...                # bracket in rendered dict
def test_by_income_year_without_data_fails_build(): ...          # ValidationError mentions year
def test_policy_evidence_level_unchanged_after_refactor(): ...   # existing test still passes
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

- [ ] **Step 1: Write the data helpers and the component.** `IncomeBrackets` shows, for the latest year: a table of bracket, threshold in reais, and share of people (a range when `low != high`), plus a line with `reais_per_usd_ppp` and the sources/retrieval dates. Below the table, `Chart` shows `ibge_sidra.rdpc_mediana_real_pnadc` and `ibge_sidra.trabalho_mediana_real_pnadc` for BRA (median person and median worker, real reais), so the reader sees the typical income beside the brackets. Each `by_income` item shows the study text and the translation box: original group, year, the limit in R$ and in US$ PPP, and the matching bracket.
- [ ] **Step 2: Build** with `cd site && npm run build`. Expected: PASS, and every existing indicator page's HTML has no new headings (no guides exist yet). Check: `grep -c "<h2" dist/indicadores/wdi.ny_gdp_pcap_kd/index.html` equals the pre-change count.
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

  Each concept gets one example linked to an existing policy brief. No digits except years.
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
  - `understand`, `how_to_read` (with a real `v`/`pct` example for BRA), at least 2 `studies`, at least 3 `policies` (Brazil and elsewhere, at least one not positive), and `by_income` items only where a study reports results by group.
  - `purchasing_power` uses `v("wdi.pa_nus_prvt_pp", "BRA", Y)` beside `v("wdi.pa_nus_fcrf", "BRA", Y)`, `v("wdi.ny_gdp_pcap_pp_kd", …)`, and the real median from `ibge_sidra.rdpc_mediana_real_pnadc`.
  - No causal wording for observational studies.
- [ ] **Step 4: Build and check.** Run `uv run compilador build && cd site && npm run build`, then render the page with `google-chrome-stable --headless=new --screenshot=...` against `npx astro preview`, in pt and en. Expected: all sections present; bracket table shows ranges for thresholds above P99.
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
  - when income sections show.
- [ ] **Step 2: Run** `uv run ruff check . && uv run ruff format --check . && uv run pytest`. Expected: PASS.
- [ ] **Step 3: Commit** `docs: record indicator guide decisions`.

After Task 8: open the PR (`superpowers:finishing-a-development-branch`), run the two-axis review (`code-review`), fix, merge. The other 16 guides follow in batches as separate plans or PRs.
