"""Change of each indicator during each presidency period (ADR 0003).

A year belongs to the period in office on July 1. A period's change runs from the year
before its first year to its last year, optionally shifted by a lag of 0–2 years, since
policy effects show up later. This is descriptive: it does not attribute causation.
"""

import pandas as pd

from compilador.governments import Governments

LAGS = (0, 1, 2)
# Indicators with a level that grows over time are compared in relative terms.
RELATIVE_UNITS = {"usd_2015"}
TABLE_INDICATORS = [
    "wdi.ny_gdp_pcap_kd",
    "wdi.sp_dyn_imrt_in",
    "wdi.sp_dyn_le00_in",
    "wdi.si_pov_gini",
    "wdi.si_pov_dday",
]
TABLE_GEOGRAPHIES = ["BRA", "LCN"]


def years_by_period(govs: Governments, first: int, last: int) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for year in range(first, last + 1):
        out.setdefault(govs.for_year(year).id, []).append(year)
    return out


def changes(
    observations: pd.DataFrame, govs: Governments, units: dict[str, str], last_year: int
) -> list[dict]:
    values = observations.set_index(["indicator_id", "geo_code", "year"])["value"]
    first_year = govs.periods[0].start.year + 1
    rows = []
    for period_id, years in years_by_period(govs, first_year, last_year).items():
        for ind in TABLE_INDICATORS:
            for geo in TABLE_GEOGRAPHIES:
                for lag in LAGS:
                    start, end = years[0] - 1 + lag, years[-1] + lag
                    a, b = values.get((ind, geo, start)), values.get((ind, geo, end))
                    relative = units[ind] in RELATIVE_UNITS
                    change = None
                    if a is not None and b is not None:
                        change = (b / a - 1) * 100 if relative else b - a
                    rows.append(
                        {
                            "period_id": period_id,
                            "indicator_id": ind,
                            "geo_code": geo,
                            "lag": lag,
                            "start_year": start,
                            "end_year": end,
                            "change": change,
                            "relative": relative,
                            "mixed_years": [y for y in years if govs.changes_in_year(y)],
                        }
                    )
    return rows
