"""Ipeadata (Ipea), OData v4 API. Annual national series only.

http://www.ipeadata.gov.br/api/
"""

import json
from dataclasses import dataclass

import httpx
import pandas as pd

from compilador.catalog import Indicator
from compilador.geography import Geography
from compilador.schema import row
from compilador.snapshot import RawFile, Snapshot

API = "https://www.ipeadata.gov.br/api/odata4"
BRAZIL = "BRA"


@dataclass(frozen=True)
class IpeadataSource:
    source_id: str = "ipeadata"
    # Ipea allows reuse with attribution; no SPDX identifier exists (ADR 0006).
    license: str = "LicenseRef-Ipeadata-reuse-with-attribution"

    def fetch(
        self, indicators: list[Indicator], geos: dict[str, Geography], client: httpx.Client
    ) -> tuple[list[RawFile], str]:
        files, versions = [], []
        for ind in indicators:
            code = ind.source_code
            for name, url in (
                (_values_file(ind), f"{API}/ValoresSerie(SERCODIGO='{code}')"),
                (_metadata_file(ind), f"{API}/Metadados('{code}')"),
            ):
                resp = client.get(url)
                resp.raise_for_status()
                files.append(RawFile(name, url, resp.content))
            (meta,) = json.loads(files[-1].content)["value"]
            versions.append(meta["SERATUALIZACAO"][:10])
        return files, max(versions)

    def normalize(
        self, snapshot: Snapshot, indicators: list[Indicator], geos: dict[str, Geography]
    ) -> pd.DataFrame:
        brazil = geos[BRAZIL]
        rows = []
        for ind in indicators:
            for r in json.loads(snapshot.read(_values_file(ind)))["value"]:
                # Empty territorial level means the national series.
                if r["VALVALOR"] is None or r.get("NIVNOME") not in ("", None, "Brasil"):
                    continue
                rows.append(row(snapshot, ind, brazil, int(r["VALDATA"][:4]), r["VALVALOR"]))
        return pd.DataFrame(rows)


def _values_file(ind: Indicator) -> str:
    return f"{ind.source_code}-valores.json"


def _metadata_file(ind: Indicator) -> str:
    return f"{ind.source_code}-metadados.json"


ipeadata = IpeadataSource()
