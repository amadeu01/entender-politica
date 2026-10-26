import httpx
import pytest

from compilador import geography, snapshot
from compilador.snapshot import RawFile
from compilador.sources.worldbank import wdi, wgi
from tests.helpers import make_indicator, wdi_payload


@pytest.fixture
def geos():
    return geography.load()


def test_normalize_maps_rows_and_drops_nulls(tmp_path, gini, geos):
    payload = wdi_payload(
        "SI.POV.GINI", [("BRA", 1990, 60.5), ("BRA", 1991, None), ("MEX", 1990, 50.1)]
    )
    snap = snapshot.write(
        "wdi",
        [RawFile("SI.POV.GINI.json", "u", payload)],
        source_version="2026-10-08",
        license=wdi.license,
        raw_dir=tmp_path,
    )
    df = wdi.normalize(snap, [gini], geos)
    assert sorted(zip(df["geo_code"], df["year"], df["value"], strict=True)) == [
        ("BRA", 1990, 60.5),
        ("MEX", 1990, 50.1),
    ]
    row = df.iloc[0]
    assert row["indicator_id"] == "wdi.si_pov_gini"
    assert row["geo_level"] == "country"
    assert row["license"] == "CC-BY-4.0"
    assert row["source_version"] == "2026-10-08"


def test_fetch_requests_all_geographies_and_reports_latest_version(gini, geos):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, content=wdi_payload("SI.POV.GINI", [], updated="2026-09-30"))

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        files, version = wdi.fetch([gini], geos, client)

    assert version == "2026-09-30"
    assert [f.name for f in files] == ["SI.POV.GINI.json"]
    assert "country/ARG;BRA;CHL;COL;LCN;MEX;WLD/indicator/SI.POV.GINI?source=2" in seen[0]
    assert "date=1975:" in seen[0]


def test_fetch_surfaces_api_errors(gini, geos):
    def handler(request):
        return httpx.Response(200, json=[{"message": [{"id": "120", "value": "Invalid value"}]}])

    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(RuntimeError, match="World Bank API error"),
    ):
        wdi.fetch([gini], geos, client)


def test_wgi_turns_standard_errors_into_90_percent_interval(tmp_path, geos):
    va = make_indicator(
        id="wgi.gov_wgi_va_est", source="wgi", source_code="GOV_WGI_VA.EST", min=-3, max=3
    )
    snap = snapshot.write(
        "wgi",
        [
            RawFile(
                "GOV_WGI_VA.EST.json", "u", wdi_payload("GOV_WGI_VA.EST", [("BRA", 2020, 0.4)])
            ),
            RawFile("GOV_WGI_VA.SE.json", "u", wdi_payload("GOV_WGI_VA.SE", [("BRA", 2020, 0.1)])),
        ],
        source_version="v",
        license=wgi.license,
        raw_dir=tmp_path,
    )
    r = wgi.normalize(snap, [va], geos).iloc[0]
    assert r["value"] == 0.4
    assert r["lower"] == pytest.approx(0.4 - 0.1645)
    assert r["upper"] == pytest.approx(0.4 + 0.1645)


def test_wgi_fetches_estimate_and_standard_error(geos):
    va = make_indicator(id="wgi.gov_wgi_va_est", source="wgi", source_code="GOV_WGI_VA.EST")
    with httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=wdi_payload("x", [])))
    ) as client:
        files, _ = wgi.fetch([va], geos, client)
    assert [f.name for f in files] == ["GOV_WGI_VA.EST.json", "GOV_WGI_VA.SE.json"]


def test_wgi_requires_estimate_code(geos):
    bad = make_indicator(id="wgi.gov_wgi_va", source="wgi", source_code="GOV_WGI_VA.SC")
    with pytest.raises(ValueError, match=".EST"):
        wgi.fetch([bad], geos, httpx.Client())
