import json
from datetime import UTC, datetime

import pandas as pd
import pytest

from compilador import brackets, build, snapshot
from compilador.snapshot import RawFile
from compilador.validate import ValidationError
from tests.helpers import make_indicator, wdi_payload


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


def test_source_with_only_null_values_builds_an_empty_dataset(tmp_path, gini):
    paths = _paths(tmp_path, gini)
    _fetch(paths, [("BRA", 2011, None)], 24)
    result = build.build(paths, today="2026-10-24")
    assert result.observations.empty


def _bracket_catalog(guard=True):
    config = brackets.load()
    ids = [*config.input_indicators, *config.income_indicators]
    if guard:
        ids.append("wdi.ny_gdp_pcap_pp_kd")
    return {
        i: make_indicator(
            id=i,
            source=i.split(".")[0],
            source_code=i.split(".")[1].upper().replace("_", "."),
        )
        for i in ids
    }


def _icp_snapshot(paths, name, day=24):
    payload = wdi_payload("NY.GDP.PCAP.PP.KD", [("BRA", 2024, 1.0)])
    payload = payload.replace(b'"value": "NY.GDP.PCAP.PP.KD"', f'"value": "{name}"'.encode())
    snapshot.write(
        "wdi",
        [RawFile("NY.GDP.PCAP.PP.KD.json", "u", payload)],
        source_version="v",
        license="CC-BY-4.0",
        raw_dir=paths.raw,
        now=datetime(2026, 10, day, tzinfo=UTC),
    )


def test_export_writes_income_brackets_when_inputs_present(tmp_path):
    config = brackets.load()
    rows = []
    for p, ind in config.percentile_indicators.items():
        rows.append((ind, 2024, 300.0 * p))
    rows += [(config.ppp_indicator, 2021, 2.5), (config.cpi_indicator, 2021, 100.0)]
    rows += [(config.cpi_indicator, 2024, 120.0)]
    df = pd.DataFrame(
        [
            {
                "geo_code": "BRA",
                "geo_level": "country",
                "year": y,
                "indicator_id": i,
                "value": v,
                "source_id": "s",
                "source_version": "v1",
                "retrieved_at": "2026-10-26",
                "unit": "x",
                "license": "l",
                "lower": None,
                "upper": None,
                "series_break": False,
            }
            for i, y, v in rows
        ]
    )
    build.export_site(df, {}, tmp_path, config)
    out = json.loads((tmp_path / "income_brackets.json").read_text())
    assert out["config"]["method"] == "linear_interpolation"
    assert out["years"][0]["year"] == 2024
    assert len(out["years"][0]["brackets"]) == 5
    assert {s["indicator_id"] for s in out["sources"]} == set(config.input_indicators)


def test_export_skips_income_brackets_without_inputs(tmp_path, gini):
    build.export_site(pd.DataFrame(columns=["year", "indicator_id"]), {gini.id: gini}, tmp_path)
    assert not (tmp_path / "income_brackets.json").exists()


def test_bracket_config_skipped_when_inputs_not_in_catalog(tmp_path, gini):
    assert build.bracket_config(_paths(tmp_path, gini), {gini.id: gini}) is None


def test_icp_base_year_guard(tmp_path, gini):
    paths = _paths(tmp_path, gini)
    catalog = _bracket_catalog()
    _icp_snapshot(paths, "GDP per capita, PPP (constant 2021 international $)")
    assert build.bracket_config(paths, catalog) is not None
    _icp_snapshot(paths, "GDP per capita, PPP (constant 2027 international $)", 25)
    with pytest.raises(ValidationError, match="ICP"):
        build.bracket_config(paths, catalog)


def test_icp_guard_skipped_without_the_indicator(tmp_path, gini):
    paths = _paths(tmp_path, gini)
    assert build.bracket_config(paths, _bracket_catalog(guard=False)) is not None
