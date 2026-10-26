"""Offline build: latest raw snapshots -> validated common format -> site artifacts.

Never touches the network, so CI and anyone cloning the repository regenerate exactly
the published data from committed raw files.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from compilador import (
    DATA_DIR,
    REPO_ROOT,
    analyses,
    brackets,
    catalog,
    changelog,
    content,
    dois,
    geography,
    governments,
    guides,
    periods,
    snapshot,
)
from compilador.analyses import ANALYSES_DIR, POLICIES_DIR
from compilador.dois import DOIS_FILE
from compilador.schema import COLUMNS, empty, tidy
from compilador.sources import SOURCES
from compilador.validate import Report, ValidationError, validate

PROCESSED_DIR = DATA_DIR / "processed"
CHANGELOG_FILE = DATA_DIR / "CHANGELOG.md"
SITE_DATA_DIR = REPO_ROOT / "site" / "public" / "data"
OBSERVATIONS = "observations"
SERIES_POINT_COLUMNS = ["geo_code", "year", "value", "lower", "upper", "series_break"]


@dataclass(frozen=True)
class Paths:
    raw: Path = snapshot.RAW_DIR
    processed: Path = PROCESSED_DIR
    changelog: Path = CHANGELOG_FILE
    site: Path = SITE_DATA_DIR
    indicators: Path = catalog.INDICATORS_DIR
    analyses: Path = ANALYSES_DIR
    policies: Path = POLICIES_DIR
    guides: Path = guides.GUIDES_DIR
    dois: Path = DOIS_FILE
    brackets: Path = brackets.BRACKETS_FILE


@dataclass(frozen=True)
class Result:
    observations: pd.DataFrame
    report: Report
    changes: changelog.Changes


def _mark_series_breaks(df: pd.DataFrame, indicators: dict[str, catalog.Indicator]) -> None:
    for ind in indicators.values():
        for brk in ind.series_breaks:
            rows = (df["indicator_id"] == ind.id) & (df["year"] == brk.year)
            if brk.geo is not None:
                rows &= df["geo_code"] == brk.geo
            df.loc[rows, "series_break"] = True


def compile_observations(paths: Paths) -> tuple[pd.DataFrame, dict[str, str]]:
    indicators = catalog.load(paths.indicators)
    geos = geography.load()
    frames, versions = [], {}
    for source_id, source in SOURCES.items():
        wanted = catalog.for_source(indicators, source_id)
        if not wanted:
            continue
        snap = snapshot.latest(source_id, paths.raw)
        if snap is None:
            raise FileNotFoundError(f"no raw snapshot for '{source_id}': run `compilador fetch`")
        # A source may return no rows at all (e.g. every value null); keep the columns.
        frames.append(source.normalize(snap, wanted, geos).reindex(columns=COLUMNS))
        versions[source_id] = snap.source_version
    df = pd.concat(frames, ignore_index=True) if frames else empty()
    _mark_series_breaks(df, indicators)
    return tidy(df), versions


def build(paths: Paths | None = None, today: str | None = None) -> Result:
    paths = paths or Paths()
    today = today or datetime.now(UTC).strftime("%Y-%m-%d")
    indicators = catalog.load(paths.indicators)
    df, versions = compile_observations(paths)
    report = validate(df, indicators, geography.load())
    documents = compile_documents(df, indicators, paths)

    previous = paths.processed / f"{OBSERVATIONS}.parquet"
    old = pd.read_parquet(previous) if previous.exists() else empty()
    changes = changelog.diff(old, df)

    paths.processed.mkdir(parents=True, exist_ok=True)
    df.to_parquet(previous, index=False)
    df.to_csv(paths.processed / f"{OBSERVATIONS}.csv", index=False)
    _write_json(paths.processed / "validation.json", report.to_dict())
    export_site(df, indicators, paths.site, bracket_config(paths, indicators))
    for name, doc in documents.items():
        _write_json(paths.site / name, doc)
    registry = dois.load(paths.dois)
    (paths.site / "references.bib").write_text(
        "\n\n".join(registry[d]["bibtex"] for d in sorted(all_dois(paths)) if d in registry) + "\n"
    )
    # Logged last, so a failed write never leaves a changelog entry for data that is not there.
    if changes:
        _prepend_changelog(paths.changelog, changelog.render(changes, today, versions))
    return Result(df, report, changes)


ICP_GUARD_INDICATOR = "wdi.ny_gdp_pcap_pp_kd"


def bracket_config(
    paths: Paths, indicators: dict[str, catalog.Indicator]
) -> brackets.Config | None:
    """Income bracket config, or None when its input indicators are not in the catalog.

    Also guards against the World Bank moving to a new ICP round: the WDI name of the
    PPP series must still mention the base year the brackets are expressed in.
    """
    config = brackets.load(paths.brackets)
    if not set(config.input_indicators) <= set(indicators):
        return None
    config = brackets.load(paths.brackets, indicators)
    if ICP_GUARD_INDICATOR in indicators:
        snap = snapshot.latest("wdi", paths.raw)
        code = indicators[ICP_GUARD_INDICATOR].source_code
        if snap is not None and f"{code}.json" in snap.files:
            payload = json.loads(snap.read(f"{code}.json"))
            name = payload[1][0]["indicator"]["value"] if len(payload) > 1 and payload[1] else ""
            if str(config.ppp_base_year) not in name:
                raise ValidationError(
                    [
                        f"WDI names {code} '{name}', which lacks the PPP base year "
                        f"{config.ppp_base_year}: the ICP round changed, review "
                        f"{paths.brackets.name}"
                    ]
                )
    return config


def all_dois(paths: Paths) -> set[str]:
    """Every DOI cited in the catalog, analyses and policy briefs."""
    indicators = catalog.load(paths.indicators)
    found = {r.doi.lower() for i in indicators.values() for r in i.references if r.doi}
    return (
        found
        | analyses.cited_dois(
            analyses.load_analyses(paths.analyses), analyses.load_policies(paths.policies)
        )
        | guides.cited_dois(guides.load_guides(paths.guides))
    )


def citation_errors(paths: Paths, registry: dict[str, dict]) -> list[str]:
    """A citation's year must match the publication year recorded by Crossref."""
    refs = [r for i in catalog.load(paths.indicators).values() for r in i.references]
    refs += [r for a, _ in analyses.load_analyses(paths.analyses) for r in a.references]
    refs += [r for p in analyses.load_policies(paths.policies) for r in p.references]
    refs += [r for g in guides.load_guides(paths.guides) for r in g.references]
    return sorted(
        {
            f"citation year differs from Crossref ({entry['year']}): {r.citation}"
            for r in refs
            if r.doi
            and (entry := registry.get(r.doi.lower()))
            and "year" in entry
            and f"({entry['year']})" not in r.citation
        }
    )


def compile_documents(
    df: pd.DataFrame, indicators: dict[str, catalog.Indicator], paths: Paths
) -> dict[str, object]:
    """Check and render analyses, policy briefs and guides: {site path: JSON document}."""
    docs = analyses.load_analyses(paths.analyses)
    policies = analyses.load_policies(paths.policies)
    guide_docs = guides.load_guides(paths.guides)
    bracket_cfg = bracket_config(paths, indicators)
    registry = dois.load(paths.dois)
    errors = analyses.check(docs, policies, indicators, set(geography.load()))
    errors += guides.check(guide_docs, indicators, {p.slug for p in policies}, bracket_cfg)
    errors += [
        f"DOI not verified: {d} (run `compilador verify-dois`)"
        for d in dois.missing(all_dois(paths), registry)
    ]
    errors += citation_errors(paths, registry)
    if errors:
        raise ValidationError(errors)

    out: dict[str, object] = {}
    index: dict[str, list] = {"analyses": [], "policies": [], "guides": []}
    try:
        for lang in analyses.LANGS:
            for a, bodies in docs:
                doc = analyses.render_analysis(a, bodies[lang], lang, df, indicators, registry)
                out[f"analyses/{a.slug}.{lang}.json"] = doc
                index["analyses"].append({"slug": a.slug, "lang": lang, "title": doc["title"]})
            for p in policies:
                doc = analyses.render_policy(p, lang, df, indicators, registry)
                out[f"policies/{p.slug}.{lang}.json"] = doc
                index["policies"].append(
                    {"slug": p.slug, "lang": lang, "name": doc["name"], "country": p.country}
                )
        for g in guide_docs:
            for lang in analyses.LANGS:
                path = f"guides/{g.indicator}.{lang}.json"
                out[path] = guides.render_guide(g, lang, df, indicators, registry, bracket_cfg)
            index["guides"].append(g.indicator)
    except content.ContentError as e:
        raise ValidationError([str(e)]) from e
    out["documents.json"] = index
    return out


def _prepend_changelog(path: Path, entry: str) -> None:
    header = "# Changelog dos dados / Data changelog\n\n"
    body = path.read_text().removeprefix(header) if path.exists() else ""
    path.write_text(header + entry + ("\n" + body if body else ""))


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str) + "\n")


def export_site(
    df: pd.DataFrame,
    indicators: dict[str, catalog.Indicator],
    out: Path,
    bracket_cfg: brackets.Config | None = None,
) -> None:
    """Write the JSON/CSV files the static site reads."""
    _write_json(out / "catalog.json", [i.model_dump(mode="json") for i in indicators.values()])
    govs = governments.load()
    _write_json(out / "governments.json", govs.model_dump(mode="json"))
    units = {i.id: i.unit for i in indicators.values()}
    last_year = int(df["year"].max()) if len(df) else govs.periods[0].start.year
    if set(periods.TABLE_INDICATORS) <= set(units):
        _write_json(out / "period_changes.json", periods.changes(df, govs, units, last_year))
    if bracket_cfg is not None:
        _write_json(
            out / "income_brackets.json",
            {
                "config": bracket_cfg.model_dump(mode="json")
                | {"labels": bracket_cfg.labels, "method": "linear_interpolation"},
                "years": brackets.distribution(df, bracket_cfg),
                "sources": brackets.sources(df, bracket_cfg),
            },
        )
    _write_json(
        out / "geographies.json", [g.model_dump(mode="json") for g in geography.load().values()]
    )
    series_dir = out / "series"
    series_dir.mkdir(parents=True, exist_ok=True)
    for ind_id, series in df.groupby("indicator_id", sort=True):
        series.to_csv(series_dir / f"{ind_id}.csv", index=False)
        points = series[SERIES_POINT_COLUMNS].astype(object)
        first = series.iloc[0]
        _write_json(
            series_dir / f"{ind_id}.json",
            {
                "indicator_id": ind_id,
                "unit": first["unit"],
                "source_id": first["source_id"],
                "source_version": first["source_version"],
                "retrieved_at": first["retrieved_at"],
                "license": first["license"],
                "observations": points.where(points.notna(), None).to_dict(orient="records"),
            },
        )
