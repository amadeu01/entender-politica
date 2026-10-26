import json

import httpx

from compilador import geography, snapshot
from compilador.snapshot import RawFile
from compilador.sources.ipeadata import ipeadata
from tests.helpers import make_indicator

GINI = make_indicator(id="ipeadata.disoc_rdcg", source="ipeadata", source_code="DISOC_RDCG", max=1)


def test_normalize_keeps_national_values_and_drops_gaps(tmp_path):
    payload = json.dumps(
        {
            "value": [
                {"VALDATA": "1979-01-01T00:00:00-03:00", "VALVALOR": 0.593, "NIVNOME": ""},
                {"VALDATA": "1980-01-01T00:00:00-03:00", "VALVALOR": None, "NIVNOME": ""},
                {"VALDATA": "1981-01-01T00:00:00-02:00", "VALVALOR": 0.584, "NIVNOME": ""},
                {"VALDATA": "1981-01-01T00:00:00-02:00", "VALVALOR": 0.6, "NIVNOME": "Regiões"},
            ]
        }
    ).encode()
    snap = snapshot.write(
        "ipeadata",
        [RawFile("DISOC_RDCG-valores.json", "u", payload)],
        source_version="2016-01-06",
        license=ipeadata.license,
        raw_dir=tmp_path,
    )
    df = ipeadata.normalize(snap, [GINI], geography.load())
    assert list(zip(df["year"], df["value"], strict=True)) == [(1979, 0.593), (1981, 0.584)]


def test_fetch_stores_values_and_metadata_and_reads_update_date():
    def handler(request):
        if "Metadados" in str(request.url):
            return httpx.Response(
                200, json={"value": [{"SERATUALIZACAO": "2016-01-06T19:33:38-02:00"}]}
            )
        return httpx.Response(200, json={"value": []})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        files, version = ipeadata.fetch([GINI], geography.load(), client)
    assert version == "2016-01-06"
    assert [f.name for f in files] == ["DISOC_RDCG-valores.json", "DISOC_RDCG-metadados.json"]
