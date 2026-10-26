import json

import httpx
import pandas as pd
import pytest

from compilador import geography, snapshot
from compilador.snapshot import RawFile
from compilador.sources.sidra import sidra
from tests.helpers import make_indicator

GINI = make_indicator(
    id="ibge_sidra.gini_pnadc",
    source="ibge_sidra",
    source_code="7435/10681",
    source_params={"table": "7435", "variable": "10681", "cv_variable": "10682"},
    min=0,
    max=1,
)
HEADER = {"D2C": "Variável (Código)", "D3C": "Ano (Código)", "V": "Valor"}


def values(*rows):
    return json.dumps([HEADER] + [{"D2C": v, "D3C": y, "V": x} for v, y, x in rows]).encode()


def test_normalize_builds_95_percent_interval_from_cv_and_skips_symbols(tmp_path):
    payload = values(
        ("10681", "2012", "0.540"),
        ("10682", "2012", "1.0"),
        ("10681", "2013", "..."),
        ("10681", "2014", "0.526"),
    )
    snap = snapshot.write(
        "ibge_sidra",
        [RawFile("7435-10681.json", "u", payload)],
        source_version="2026-05-08",
        license=sidra.license,
        raw_dir=tmp_path,
    )
    df = sidra.normalize(snap, [GINI], geography.load()).set_index("year")
    assert list(df.index) == [2012, 2014]
    assert df.loc[2012, "lower"] == pytest.approx(0.540 - 1.96 * 0.540 * 0.01)
    assert df.loc[2012, "upper"] == pytest.approx(0.540 + 1.96 * 0.540 * 0.01)
    assert pd.isna(df.loc[2014, "lower"])
    assert set(df["geo_code"]) == {"BRA"}


def test_fetch_requests_value_and_cv_and_uses_latest_modification_as_version():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if "periodos" in str(request.url):
            return httpx.Response(
                200,
                json=[
                    {"id": "2012", "modificacao": "08/05/2026"},
                    {"id": "2024", "modificacao": "15/12/2025"},
                ],
            )
        return httpx.Response(200, content=values())

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        files, version = sidra.fetch([GINI], geography.load(), client)

    assert version == "2026-05-08"
    assert "/t/7435/n1/all/v/10681,10682/p/all" in seen[0]
    assert [f.name for f in files] == ["7435-10681.json", "7435-periodos.json"]


def _percentile(category: str) -> object:
    return make_indicator(
        id=f"ibge_sidra.renda_{category}",
        source="ibge_sidra",
        source_code="7438/10769",
        source_params={
            "table": "7438",
            "variable": "10769",
            "classification": "1019",
            "category": category,
        },
    )


def test_normalize_filters_by_classification_category(tmp_path):
    header = {"D2C": "v", "D3C": "y", "D4C": "c", "V": "Valor"}
    records = [
        {"D2C": "10769", "D3C": "2019", "D4C": "49264", "V": "1200"},
        {"D2C": "10769", "D3C": "2019", "D4C": "49260", "V": "400"},
    ]
    snap = snapshot.write(
        "ibge_sidra",
        [RawFile("7438-10769-c1019.json", "u", json.dumps([header] + records).encode())],
        source_version="2026-05-08",
        license=sidra.license,
        raw_dir=tmp_path,
    )
    df = sidra.normalize(snap, [_percentile("49264")], geography.load())
    assert df["value"].tolist() == [1200.0]


def test_fetch_shares_one_file_per_table_classification():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        if "periodos" in str(request.url):
            return httpx.Response(200, json=[{"id": "2019", "modificacao": "08/05/2026"}])
        return httpx.Response(200, content=values())

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        files, _ = sidra.fetch(
            [_percentile("49260"), _percentile("49264")], geography.load(), client
        )

    assert [f.name for f in files].count("7438-10769-c1019.json") == 1
    assert any("/t/7438/n1/all/v/10769/p/all/c1019/all" in u for u in seen)
