import json

import httpx
import pytest

from compilador import geography, snapshot
from compilador.snapshot import RawFile
from compilador.sources.siconfi import _annual_index, siconfi
from tests.helpers import make_indicator


def _ind(**params):
    p = {"coluna": "Despesas Pagas", "conta": "12 - Educação", "real": "true"} | params
    return make_indicator(
        id="siconfi.educ",
        source="siconfi",
        source_code="x",
        source_params=p,
        unit="brl_billion_real",
    )


def _months(year, pct):
    return [{"data": f"01/{m:02d}/{year}", "valor": str(pct)} for m in range(1, 13)]


def _dca(year, paid):
    base = {"coluna": "Despesas Pagas", "conta": "12 - Educação", "valor": paid}
    other = {"coluna": "Despesas Pagas", "conta": "12.364 - Ensino Superior", "valor": 1.0}
    return json.dumps([base, other]).encode()


def test_annual_index_needs_twelve_months():
    records = _months(2014, 0) + _months(2015, 1.0)[:11]
    assert set(_annual_index(records)) == {2014}


def test_real_values_use_the_base_year_prices(tmp_path):
    ipca = _months(2013, 0) + _months(2014, 0) + _months(2015, 10)
    snap = snapshot.write(
        "siconfi",
        [
            RawFile("dca-2014.json", "u", _dca(2014, 2e9)),
            RawFile("dca-2015.json", "u", _dca(2015, 4e9)),
            RawFile("ipca-sgs433.json", "u", json.dumps(ipca).encode()),
        ],
        source_version="v",
        license=siconfi.license,
        raw_dir=tmp_path,
    )
    df = siconfi.normalize(snap, [_ind()], geography.load())
    got = dict(zip(df["year"], df["value"], strict=True))
    index = _annual_index(ipca)
    # 2015 is the base year: its real value is its nominal value; 2014 is raised to 2015 prices.
    assert got[2015] == pytest.approx(4.0)
    assert got[2014] == pytest.approx(2.0 * index[2015] / index[2014])
    assert set(df["geo_code"]) == {"BRA"}


def test_nominal_indicator_and_missing_account_are_handled(tmp_path):
    snap = snapshot.write(
        "siconfi",
        [
            RawFile("dca-2014.json", "u", _dca(2014, 2e9)),
            RawFile("ipca-sgs433.json", "u", json.dumps(_months(2014, 0)).encode()),
        ],
        source_version="v",
        license=siconfi.license,
        raw_dir=tmp_path,
    )
    nominal = _ind(real="false")
    absent = _ind(conta="28.847 - Transferências para a Educação Básica")
    df = siconfi.normalize(snap, [nominal, absent], geography.load())
    assert list(df["value"]) == [pytest.approx(2.0)]


def test_fetch_pages_through_results_and_adds_the_price_index():
    def handler(request):
        if "bcb" in request.url.host:
            return httpx.Response(200, json=_months(2013, 0.5))
        offset = int(request.url.params.get("offset", 0))
        item = {"coluna": "Despesas Pagas", "conta": f"c{offset}", "valor": 1.0}
        return httpx.Response(
            200, json={"items": [item], "hasMore": offset == 0, "limit": 1, "offset": offset}
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        files, version = siconfi.fetch([_ind()], geography.load(), client)
    names = [f.name for f in files]
    assert names[0] == "dca-2014.json" and names[-1] == "ipca-sgs433.json"
    assert len(json.loads(files[0].content)) == 2
    assert version.startswith("DCA 2014-")
