import hashlib
import io
import json
import zipfile

import httpx
import pandas as pd
import pytest

from compilador import geography, snapshot
from compilador.sources.vdem import EXTRACT, MEMBER, UPSTREAM, vdem
from tests.helpers import make_indicator

POLYARCHY = make_indicator(
    id="vdem.v2x_polyarchy", source="vdem", source_code="v2x_polyarchy", min=0, max=1
)
CSV = (
    "country_name,country_text_id,year,v2x_polyarchy,v2x_polyarchy_codelow,"
    "v2x_polyarchy_codehigh,v2x_other\n"
    "Brazil,BRA,1974,0.2,0.1,0.3,9\n"
    "Brazil,BRA,1990,0.814,0.772,0.868,9\n"
    "Brazil,BRA,1980,0.251,0.221,0.277,9\n"
    "Sweden,SWE,1990,0.9,0.85,0.95,9\n"
    "Mexico,MEX,1990,0.4,,,9\n"
)


def archive() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(MEMBER, CSV)
    return buf.getvalue()


@pytest.fixture
def fetched(tmp_path):
    data = archive()
    with httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=data))
    ) as c:
        files, version = vdem.fetch([POLYARCHY], geography.load(), c)
    snap = snapshot.write(
        "vdem", files, source_version=version, license=vdem.license, raw_dir=tmp_path
    )
    return data, snap


def test_extract_keeps_covered_countries_catalog_columns_and_years_sorted(fetched):
    _, snap = fetched
    assert snap.read(EXTRACT).decode() == (
        "country_text_id,year,v2x_polyarchy,v2x_polyarchy_codelow,v2x_polyarchy_codehigh\n"
        "BRA,1980,0.251,0.221,0.277\n"
        "BRA,1990,0.814,0.772,0.868\n"
        "MEX,1990,0.4,,\n"
    )


def test_upstream_records_the_original_archive(fetched):
    data, snap = fetched
    upstream = json.loads(snap.read(UPSTREAM))
    assert upstream["sha256"] == hashlib.sha256(data).hexdigest()
    assert upstream["bytes"] == len(data)
    assert upstream["filter"]["from_year"] == 1975
    assert snap.source_version == "v16"


def test_normalize_uses_68_percent_hpd_interval(fetched):
    _, snap = fetched
    df = vdem.normalize(snap, [POLYARCHY], geography.load()).set_index(["geo_code", "year"])
    assert df.loc[("BRA", 1990), ["value", "lower", "upper"]].tolist() == [0.814, 0.772, 0.868]
    assert pd.isna(df.loc[("MEX", 1990), "lower"])
    assert df.loc[("BRA", 1990), "license"] == "CC-BY-SA-4.0"
