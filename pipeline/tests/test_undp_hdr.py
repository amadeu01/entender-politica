from compilador import geography, snapshot
from compilador.snapshot import RawFile
from compilador.sources.undp_hdr import FILE, undp_hdr
from tests.helpers import make_indicator

HDI = make_indicator(id="undp_hdr.hdi", source="undp_hdr", source_code="hdi", max=1)

CSV = (
    "iso3,country,hdi_rank_2023,hdi_1990,hdi_1991,hdi_f_1990\n"
    "BRA,Brazil,84,0.641,0.645,0.6\n"
    "CIV,C\xf4te d'Ivoire,157,0.389,,0.3\n"
    "ZZH.LAC,Latin America and the Caribbean,,0.6,0.61,0.5\n"
).encode("latin-1")


def test_normalize_reads_only_covered_countries_and_exact_column(tmp_path):
    snap = snapshot.write(
        "undp_hdr",
        [RawFile(FILE, "u", CSV)],
        source_version="HDR 2025",
        license=undp_hdr.license,
        raw_dir=tmp_path,
    )
    df = undp_hdr.normalize(snap, [HDI], geography.load())
    assert sorted(zip(df["geo_code"], df["year"], df["value"], strict=True)) == [
        ("BRA", 1990, 0.641),
        ("BRA", 1991, 0.645),
    ]
