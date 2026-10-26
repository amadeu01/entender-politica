"""UNDP — Human Development Report, composite indices complete time series (CSV).

The file is replaced with each report edition; update `EDITION` and `URL` together.
Only countries are read: UNDP regional aggregates have a different composition from the
World Bank ones used elsewhere (e.g. LCN), so they are not mapped onto them.
https://hdr.undp.org/data-center/documentation-and-downloads
"""

import io
from dataclasses import dataclass

import httpx
import pandas as pd

from compilador.catalog import Indicator
from compilador.geography import Geography, Level
from compilador.schema import row
from compilador.snapshot import RawFile, Snapshot

EDITION = "HDR 2025"
URL = "https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Composite_indices_complete_time_series.csv"
FILE = "composite_indices_time_series.csv"


@dataclass(frozen=True)
class UndpHdrSource:
    source_id: str = "undp_hdr"
    license: str = "CC-BY-3.0-IGO"

    def fetch(
        self, indicators: list[Indicator], geos: dict[str, Geography], client: httpx.Client
    ) -> tuple[list[RawFile], str]:
        resp = client.get(URL, follow_redirects=True)
        resp.raise_for_status()
        return [RawFile(FILE, URL, resp.content)], EDITION

    def normalize(
        self, snapshot: Snapshot, indicators: list[Indicator], geos: dict[str, Geography]
    ) -> pd.DataFrame:
        # The HDR 2025 file is Latin-1 (e.g. "C\xf4te d'Ivoire"), not UTF-8.
        table = pd.read_csv(io.BytesIO(snapshot.read(FILE)), encoding="latin-1")
        countries = {c: g for c, g in geos.items() if g.level == Level.COUNTRY}
        table = table[table["iso3"].isin(countries)]
        rows = []
        for ind in indicators:
            prefix = f"{ind.source_code}_"
            columns = [
                c for c in table.columns if c.startswith(prefix) and c[len(prefix) :].isdigit()
            ]
            long = table.melt(id_vars="iso3", value_vars=columns).dropna(subset=["value"])
            for r in long.itertuples():
                year = int(r.variable[len(prefix) :])
                rows.append(row(snapshot, ind, countries[r.iso3], year, float(r.value)))
        return pd.DataFrame(rows)


undp_hdr = UndpHdrSource()
