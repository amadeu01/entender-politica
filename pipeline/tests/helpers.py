import json

from compilador.catalog import Indicator


def wdi_payload(code: str, rows: list[tuple[str, int, float | None]], updated="2026-10-08"):
    meta = {"page": 1, "pages": 1, "per_page": 20000, "total": len(rows), "lastupdated": updated}
    records = [
        {
            "indicator": {"id": code, "value": code},
            "country": {"id": geo[:2], "value": geo},
            "countryiso3code": geo,
            "date": str(year),
            "value": value,
            "unit": "",
            "obs_status": "",
            "decimal": 1,
        }
        for geo, year, value in rows
    ]
    return json.dumps([meta, records]).encode()


def make_indicator(**overrides) -> Indicator:
    data = {
        "id": "wdi.si_pov_gini",
        "source": "wdi",
        "source_code": "SI.POV.GINI",
        "name": {"pt": "Gini", "en": "Gini"},
        "unit": "index_0_100",
        "definition": {"pt": "d", "en": "d"},
        "formula": {"pt": "f", "en": "f"},
        "criticisms": [{"pt": "c", "en": "c"}],
        "references": [{"citation": "Atkinson 1970", "doi": "10.1016/0022-0531(70)90039-6"}],
        "min": 0,
        "max": 100,
    }
    return Indicator.model_validate(data | overrides)
