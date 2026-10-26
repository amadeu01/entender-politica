import json
from datetime import UTC, datetime

import pandas as pd

from compilador import build, snapshot
from compilador.snapshot import RawFile
from tests.helpers import wdi_payload


def _paths(tmp_path, gini) -> build.Paths:
    indicators = tmp_path / "indicators"
    indicators.mkdir()
    data = gini.model_dump(mode="json") | {
        "series_breaks": [{"year": 2012, "geo": "BRA", "note": {"pt": "q", "en": "b"}}]
    }
    (indicators / f"{gini.id}.yaml").write_text(json.dumps(data))
    registry = tmp_path / "dois.json"
    registry.write_text(json.dumps({"10.1016/0022-0531(70)90039-6": {"bibtex": "@article{x}"}}))
    return build.Paths(
        analyses=tmp_path / "no-analyses",
        policies=tmp_path / "no-policies",
        dois=registry,
        raw=tmp_path / "raw",
        processed=tmp_path / "processed",
        changelog=tmp_path / "CHANGELOG.md",
        site=tmp_path / "site",
        indicators=indicators,
    )


def _fetch(paths, rows, day):
    snapshot.write(
        "wdi",
        [RawFile("SI.POV.GINI.json", "u", wdi_payload("SI.POV.GINI", rows))],
        source_version=f"v{day}",
        license="CC-BY-4.0",
        raw_dir=paths.raw,
        now=datetime(2026, 10, day, tzinfo=UTC),
    )


def test_build_end_to_end_is_idempotent_and_logs_revisions(tmp_path, gini):
    paths = _paths(tmp_path, gini)
    _fetch(paths, [("BRA", 2011, 52.0), ("BRA", 2012, 53.0), ("MEX", 2012, 49.0)], 24)

    first = build.build(paths, today="2026-10-24")
    assert first.changes.added == 3
    processed = pd.read_parquet(paths.processed / "observations.parquet")
    breaks = processed.set_index(["geo_code", "year"])["series_break"].to_dict()
    assert breaks == {("BRA", 2011): False, ("BRA", 2012): True, ("MEX", 2012): False}

    series = json.loads((paths.site / "series" / "wdi.si_pov_gini.json").read_text())
    assert series["license"] == "CC-BY-4.0"
    assert series["observations"][1] == {
        "geo_code": "BRA",
        "year": 2012,
        "value": 53.0,
        "lower": None,
        "upper": None,
        "series_break": True,
    }
    assert (paths.site / "catalog.json").exists()
    assert (paths.site / "governments.json").exists()

    again = build.build(paths, today="2026-10-24")
    assert not again.changes
    assert paths.changelog.read_text().count("## ") == 1

    _fetch(paths, [("BRA", 2011, 52.0), ("BRA", 2012, 52.8), ("MEX", 2012, 49.0)], 25)
    revised = build.build(paths, today="2026-10-25")
    assert revised.changes.revised == ["wdi.si_pov_gini BRA 2012: 53.0 → 52.8"]
    log = paths.changelog.read_text()
    assert log.index("## 2026-10-25") < log.index("## 2026-10-24")
