"""V-Dem (Varieties of Democracy), Country-Year Core dataset.

The upstream archive (about 16 MB zipped, 200 MB unzipped) is too large to commit
(ADR 0002), so the snapshot keeps a deterministic extract (covered countries, catalog
columns, years from START_YEAR) and `upstream.json` with the archive's URL, size and
sha256, so anyone can download the original and re-derive the extract (ADR 0010).
https://v-dem.net/data/the-v-dem-dataset/
"""

import hashlib
import io
import json
import zipfile
from dataclasses import dataclass

import httpx
import pandas as pd

from compilador import START_YEAR
from compilador.catalog import Indicator
from compilador.geography import Geography, Level
from compilador.schema import row
from compilador.snapshot import RawFile, Snapshot

# New V-Dem versions re-estimate the whole series (values are not comparable across
# versions), so the version is pinned here and changed deliberately.
VERSION = "v16"
URL = f"https://v-dem.net/media/datasets/V-Dem-CY-Core-{VERSION}_csv.zip"
MEMBER = f"V-Dem-CY-Core-{VERSION}.csv"
EXTRACT = "vdem-extract.csv"
UPSTREAM = "upstream.json"
KEYS = ["country_text_id", "year"]


def _source_columns(indicators: list[Indicator]) -> list[str]:
    # `_codelow`/`_codehigh` bound the 68% highest posterior density interval.
    return [f"{i.source_code}{s}" for i in indicators for s in ("", "_codelow", "_codehigh")]


def extract(archive: bytes, columns: list[str], countries: list[str]) -> bytes:
    """Deterministic subset of the upstream CSV: same text values, sorted rows."""
    with zipfile.ZipFile(io.BytesIO(archive)) as z, z.open(MEMBER) as f:
        table = pd.read_csv(f, usecols=KEYS + columns, dtype=str, keep_default_na=False)
    table = table[table["country_text_id"].isin(countries)]
    table = table[table["year"].astype(int) >= START_YEAR]
    table = table.sort_values(KEYS, key=lambda c: c.astype(int) if c.name == "year" else c)
    return table[KEYS + columns].to_csv(index=False, lineterminator="\n").encode()


@dataclass(frozen=True)
class VdemSource:
    source_id: str = "vdem"
    license: str = "CC-BY-SA-4.0"

    def fetch(
        self, indicators: list[Indicator], geos: dict[str, Geography], client: httpx.Client
    ) -> tuple[list[RawFile], str]:
        # The archive is ~16 MB: allow longer than the CLI's default per-request timeout.
        resp = client.get(URL, follow_redirects=True, timeout=300)
        resp.raise_for_status()
        archive = resp.content
        columns = _source_columns(indicators)
        countries = sorted(c for c, g in geos.items() if g.level == Level.COUNTRY)
        upstream = {
            "url": URL,
            "member": MEMBER,
            "sha256": hashlib.sha256(archive).hexdigest(),
            "bytes": len(archive),
            "filter": {"countries": countries, "from_year": START_YEAR, "columns": columns},
        }
        return [
            # Derived from the archive at URL; upstream.json says how.
            RawFile(EXTRACT, f"{URL}#extract-see-{UPSTREAM}", extract(archive, columns, countries)),
            RawFile(UPSTREAM, URL, (json.dumps(upstream, indent=2) + "\n").encode()),
        ], VERSION

    def normalize(
        self, snapshot: Snapshot, indicators: list[Indicator], geos: dict[str, Geography]
    ) -> pd.DataFrame:
        # Read exactly as written by `extract`: text, with empty cells for missing values.
        table = pd.read_csv(io.BytesIO(snapshot.read(EXTRACT)), dtype=str, keep_default_na=False)
        records = table.to_dict("records")
        rows = []
        for ind in indicators:
            code = ind.source_code
            for r in records:
                geo = geos.get(r["country_text_id"])
                if geo is None or r[code] == "":
                    continue
                low, high = (_number(r[f"{code}{s}"]) for s in ("_codelow", "_codehigh"))
                rows.append(row(snapshot, ind, geo, int(r["year"]), float(r[code]), low, high))
        return pd.DataFrame(rows)


def _number(text: str) -> float | None:
    return float(text) if text else None


vdem = VdemSource()
