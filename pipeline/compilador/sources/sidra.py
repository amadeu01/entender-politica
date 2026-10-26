"""IBGE — SIDRA (Sistema IBGE de Recuperação Automática), national level.

Catalog entries set `source_params`: `table`, `variable` and, when IBGE publishes it,
`cv_variable` (coefficient of variation, in %), turned into a 95% interval.
https://apisidra.ibge.gov.br/
"""

import json
from dataclasses import dataclass
from datetime import datetime

import httpx
import pandas as pd

from compilador.catalog import Indicator
from compilador.geography import Geography
from compilador.schema import row
from compilador.snapshot import RawFile, Snapshot

VALUES_API = "https://apisidra.ibge.gov.br/values"
METADATA_API = "https://servicodados.ibge.gov.br/api/v3/agregados"
Z_95 = 1.96
BRAZIL = "BRA"


@dataclass(frozen=True)
class SidraSource:
    source_id: str = "ibge_sidra"
    # IBGE allows reuse with attribution; no SPDX identifier exists (ADR 0006).
    license: str = "LicenseRef-IBGE-reuse-with-attribution"

    def fetch(
        self, indicators: list[Indicator], geos: dict[str, Geography], client: httpx.Client
    ) -> tuple[list[RawFile], str]:
        files, versions = [], []
        for ind in indicators:
            p = ind.source_params
            variables = ",".join(v for v in (p["variable"], p.get("cv_variable")) if v)
            url = f"{VALUES_API}/t/{p['table']}/n1/all/v/{variables}/p/all?formato=json"
            files.append(RawFile(_values_file(ind), url, _get(client, url)))

            periods_url = f"{METADATA_API}/{p['table']}/periodos"
            periods = _get(client, periods_url)
            files.append(RawFile(f"{p['table']}-periodos.json", periods_url, periods))
            versions += [
                datetime.strptime(x["modificacao"], "%d/%m/%Y").date().isoformat()
                for x in json.loads(periods)
            ]
        return _dedupe(files), max(versions)

    def normalize(
        self, snapshot: Snapshot, indicators: list[Indicator], geos: dict[str, Geography]
    ) -> pd.DataFrame:
        brazil = geos[BRAZIL]
        rows = []
        for ind in indicators:
            p = ind.source_params
            # First record is the header row.
            records = json.loads(snapshot.read(_values_file(ind)))[1:]
            values = _by_year(records, p["variable"])
            cvs = _by_year(records, p["cv_variable"]) if "cv_variable" in p else {}
            for year, value in values.items():
                cv = cvs.get(year)
                if cv is None:
                    rows.append(row(snapshot, ind, brazil, year, value))
                else:
                    half = Z_95 * value * cv / 100
                    rows.append(row(snapshot, ind, brazil, year, value, value - half, value + half))
        return pd.DataFrame(rows)


def _values_file(ind: Indicator) -> str:
    return f"{ind.source_params['table']}-{ind.source_params['variable']}.json"


def _get(client: httpx.Client, url: str) -> bytes:
    resp = client.get(url)
    resp.raise_for_status()
    return resp.content


def _dedupe(files: list[RawFile]) -> list[RawFile]:
    """Several indicators may share a table, and so its period metadata file."""
    return list({f.name: f for f in files}.values())


def _by_year(records: list[dict], variable: str) -> dict[int, float]:
    # SIDRA marks missing or suppressed values with symbols such as "-", "..", "...", "X".
    out = {}
    for r in records:
        if r["D2C"] != variable:
            continue
        try:
            out[int(r["D3C"])] = float(r["V"])
        except ValueError:
            continue
    return out


sidra = SidraSource()
