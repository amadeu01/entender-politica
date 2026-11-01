"""SICONFI / Tesouro Nacional: federal spending by function (DCA, Annex I-E), deflated by IPCA.

The DCA (Declaração de Contas Anuais) is the Union's accounting close, so a year's figures
are not revised later. The API only holds 2014 onward. Real values divide each year's
nominal amount by the year's average IPCA index (BCB SGS 433) and multiply by the average
index of the base year, the last year with twelve months in the snapshot (ADR 0014).

https://apidatalake.tesouro.gov.br/docs/siconfi/
"""

import json
from dataclasses import dataclass
from datetime import date

import httpx
import pandas as pd

from compilador.catalog import Indicator
from compilador.geography import Geography
from compilador.schema import row
from compilador.snapshot import RawFile, Snapshot

DCA_API = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
IPCA_API = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
ANNEX = "DCA-Anexo I-E"
UNION_ID = "1"
FIRST_YEAR = 2014
IPCA_FILE = "ipca-sgs433.json"
BRAZIL = "BRA"
BILLION = 1e9


@dataclass(frozen=True)
class SiconfiSource:
    source_id: str = "siconfi"
    # Tesouro Nacional open data: Open Database License per the portal (ADR 0006).
    license: str = "ODbL-1.0"

    def fetch(
        self, indicators: list[Indicator], geos: dict[str, Geography], client: httpx.Client
    ) -> tuple[list[RawFile], str]:
        files = []
        last = date.today().year - 1
        for year in range(FIRST_YEAR, last + 1):
            items, offset = [], 0
            while True:
                resp = client.get(
                    DCA_API,
                    params={
                        "an_exercicio": year,
                        "no_anexo": ANNEX,
                        "id_ente": UNION_ID,
                        "offset": offset,
                    },
                )
                resp.raise_for_status()
                page = resp.json()
                items += page["items"]
                if not page["hasMore"]:
                    break
                offset += page["limit"]
            if items:
                body = json.dumps(items, ensure_ascii=False, sort_keys=True).encode()
                files.append(RawFile(f"dca-{year}.json", f"{DCA_API}?an_exercicio={year}", body))
        if not files:
            raise RuntimeError("SICONFI returned no DCA data")
        resp = client.get(
            IPCA_API,
            params={
                "formato": "json",
                "dataInicial": f"01/01/{FIRST_YEAR - 1}",
                "dataFinal": f"31/12/{last}",
            },
        )
        resp.raise_for_status()
        files.append(RawFile(IPCA_FILE, str(resp.url), resp.content))
        return files, f"DCA {files[0].name[4:8]}-{files[-2].name[4:8]}; IPCA SGS 433"

    def normalize(
        self, snapshot: Snapshot, indicators: list[Indicator], geos: dict[str, Geography]
    ) -> pd.DataFrame:
        brazil = geos[BRAZIL]
        index = _annual_index(json.loads(snapshot.read(IPCA_FILE)))
        base_year = max(index)
        rows = []
        for name in sorted(n for n in snapshot.files if n.startswith("dca-")):
            year = int(name[4:8])
            items = json.loads(snapshot.read(name))
            for ind in indicators:
                p = ind.source_params
                match = [
                    x["valor"]
                    for x in items
                    if x["coluna"] == p["coluna"] and x["conta"] == p["conta"]
                ]
                if len(match) != 1:
                    raise RuntimeError(
                        f"SICONFI {year}: {len(match)} rows for {p['coluna']!r} / {p['conta']!r}"
                        f" (indicator {ind.id}); the account may have been renamed"
                    )
                value = match[0]
                if p.get("real") == "true":
                    if year not in index:
                        continue
                    value = value * index[base_year] / index[year]
                rows.append(row(snapshot, ind, brazil, year, value / BILLION))
        return pd.DataFrame(rows)


def _annual_index(records: list[dict]) -> dict[int, float]:
    """Average price index of each year that has all twelve months, from monthly % changes."""
    level, by_year = 1.0, {}
    for r in sorted(records, key=lambda r: (r["data"][6:], r["data"][3:5])):
        level *= 1 + float(r["valor"]) / 100
        by_year.setdefault(int(r["data"][6:]), []).append(level)
    return {y: sum(v) / len(v) for y, v in by_year.items() if len(v) == 12}


siconfi = SiconfiSource()
