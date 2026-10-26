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
