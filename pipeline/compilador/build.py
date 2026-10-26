"""Offline build: latest raw snapshots -> validated common format -> site artifacts.

Never touches the network, so CI and anyone cloning the repository regenerate exactly
the published data from committed raw files.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from compilador import DATA_DIR, REPO_ROOT, catalog, changelog, geography, governments, snapshot
from compilador.schema import COLUMNS, empty, tidy
from compilador.sources import SOURCES
from compilador.validate import Report, validate

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


@dataclass(frozen=True)
class Result:
    observations: pd.DataFrame
    report: Report
    changes: changelog.Changes


def _mark_series_breaks(df: pd.DataFrame, indicators: dict[str, catalog.Indicator]) -> None:
    for ind in indicators.values():
        for brk in ind.series_breaks:
            df.loc[(df["indicator_id"] == ind.id) & (df["year"] == brk.year), "series_break"] = True


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

    previous = paths.processed / f"{OBSERVATIONS}.parquet"
    old = pd.read_parquet(previous) if previous.exists() else empty()
    changes = changelog.diff(old, df)

    paths.processed.mkdir(parents=True, exist_ok=True)
    df.to_parquet(previous, index=False)
    df.to_csv(paths.processed / f"{OBSERVATIONS}.csv", index=False)
    _write_json(paths.processed / "validation.json", report.to_dict())
    export_site(df, indicators, paths.site)
    # Logged last, so a failed write never leaves a changelog entry for data that is not there.
    if changes:
        _prepend_changelog(paths.changelog, changelog.render(changes, today, versions))
    return Result(df, report, changes)


def _prepend_changelog(path: Path, entry: str) -> None:
    header = "# Changelog dos dados / Data changelog\n\n"
    body = path.read_text().removeprefix(header) if path.exists() else ""
    path.write_text(header + entry + ("\n" + body if body else ""))


def _write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str) + "\n")


def export_site(df: pd.DataFrame, indicators: dict[str, catalog.Indicator], out: Path) -> None:
    """Write the JSON/CSV files the static site reads."""
    _write_json(out / "catalog.json", [i.model_dump(mode="json") for i in indicators.values()])
    _write_json(out / "governments.json", governments.load().model_dump(mode="json"))
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
