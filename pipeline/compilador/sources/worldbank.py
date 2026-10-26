"""World Bank Indicators API v2: World Development Indicators (WDI) and Worldwide
Governance Indicators (WGI).

https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import pandas as pd

from compilador import START_YEAR
from compilador.catalog import Indicator
from compilador.geography import Geography
from compilador.schema import row
from compilador.snapshot import RawFile, Snapshot

API = "https://api.worldbank.org/v2"
PER_PAGE = 20000
# WGI publishes 90% confidence intervals: estimate ± 1.645 standard errors
# (Kaufmann, Kraay and Mastruzzi, 2011).
Z_90 = 1.645


@dataclass(frozen=True)
class WorldBankSource:
    source_id: str
    api_source: int
    license: str = "CC-BY-4.0"
    # WGI: fetch the `.SE` series next to each `.EST` and turn it into an interval.
    standard_errors: bool = False

    def _codes(self, ind: Indicator) -> list[str]:
        if self.standard_errors:
            return [ind.source_code, _se_code(ind)]
        return [ind.source_code]

    def fetch(
        self, indicators: list[Indicator], geos: dict[str, Geography], client: httpx.Client
    ) -> tuple[list[RawFile], str]:
        geo_codes = ";".join(sorted(geos))
        files, versions = [], []
        for code in [c for ind in indicators for c in self._codes(ind)]:
            url = (
                f"{API}/country/{geo_codes}/indicator/{code}?source={self.api_source}"
                f"&format=json&per_page={PER_PAGE}&date={START_YEAR}:{datetime.now(UTC).year}"
            )
            resp = client.get(url)
            resp.raise_for_status()
            meta = resp.json()[0]
            if "message" in meta:
                raise RuntimeError(f"World Bank API error for {code}: {meta['message']}")
            if meta["pages"] > 1:
                raise RuntimeError(f"{code}: response paginated, raise PER_PAGE")
            files.append(RawFile(f"{code}.json", url, resp.content))
            versions.append(meta["lastupdated"])
        return files, max(versions)

    def normalize(
        self, snapshot: Snapshot, indicators: list[Indicator], geos: dict[str, Geography]
    ) -> pd.DataFrame:
        rows = []
        for ind in indicators:
            values = _read(snapshot, ind.source_code)
            errors = _read(snapshot, _se_code(ind)) if self.standard_errors else {}
            for (geo_code, year), value in values.items():
                geo = geos.get(geo_code)
                if geo is None:
                    continue
                se = errors.get((geo_code, year))
                if se is None:
                    rows.append(row(snapshot, ind, geo, year, value))
                else:
                    rows.append(
                        row(snapshot, ind, geo, year, value, value - Z_90 * se, value + Z_90 * se)
                    )
        return pd.DataFrame(rows)


def _se_code(ind: Indicator) -> str:
    if not ind.source_code.endswith(".EST"):
        raise ValueError(f"{ind.id}: WGI source_code must end in .EST, got {ind.source_code}")
    return ind.source_code.removesuffix(".EST") + ".SE"


def _read(snapshot: Snapshot, code: str) -> dict[tuple[str, int], float]:
    _, records = json.loads(snapshot.read(f"{code}.json"))
    return {
        (r["countryiso3code"], int(r["date"])): float(r["value"])
        for r in records or []
        if r["value"] is not None
    }


wdi = WorldBankSource("wdi", api_source=2)
wgi = WorldBankSource("wgi", api_source=3, standard_errors=True)
