"""World Bank — World Development Indicators, via the Indicators API v2.

https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
"""

import json
from datetime import UTC, datetime

import httpx
import pandas as pd

from compilador import START_YEAR
from compilador.catalog import Indicator
from compilador.geography import Geography
from compilador.snapshot import RawFile, Snapshot

SOURCE_ID = "wdi"
LICENSE = "CC-BY-4.0"
API = "https://api.worldbank.org/v2"
PER_PAGE = 20000


def _file_name(ind: Indicator) -> str:
    return f"{ind.source_code}.json"


def fetch(
    indicators: list[Indicator], geos: dict[str, Geography], client: httpx.Client
) -> tuple[list[RawFile], str]:
    codes = ";".join(sorted(geos))
    files, versions = [], []
    for ind in indicators:
        url = (
            f"{API}/country/{codes}/indicator/{ind.source_code}"
            f"?format=json&per_page={PER_PAGE}&date={START_YEAR}:{datetime.now(UTC).year}"
        )
        resp = client.get(url)
        resp.raise_for_status()
        meta = resp.json()[0]
        if "message" in meta:
            raise RuntimeError(f"World Bank API error for {ind.source_code}: {meta['message']}")
        if meta["pages"] > 1:
            raise RuntimeError(f"{ind.source_code}: response paginated, raise PER_PAGE")
        files.append(RawFile(_file_name(ind), url, resp.content))
        versions.append(meta["lastupdated"])
    return files, max(versions)


def normalize(
    snapshot: Snapshot, indicators: list[Indicator], geos: dict[str, Geography]
) -> pd.DataFrame:
    rows = []
    for ind in indicators:
        _, records = json.loads(snapshot.read(_file_name(ind)))
        for r in records or []:
            geo = geos.get(r["countryiso3code"])
            if r["value"] is None or geo is None:
                continue
            rows.append(
                {
                    "geo_code": geo.code,
                    "geo_level": geo.level.value,
                    "year": int(r["date"]),
                    "indicator_id": ind.id,
                    "value": float(r["value"]),
                    "lower": None,
                    "upper": None,
                    "unit": ind.unit,
                    "source_id": SOURCE_ID,
                    "source_version": snapshot.source_version,
                    "retrieved_at": snapshot.retrieved_at,
                    "license": snapshot.license,
                    "series_break": False,
                }
            )
    return pd.DataFrame(rows)
