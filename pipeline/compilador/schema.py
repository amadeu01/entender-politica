"""Common observation format (ADR 0002)."""

import pandas as pd
import pandera.pandas as pa

from compilador.catalog import Indicator
from compilador.geography import Geography, Level
from compilador.snapshot import Snapshot

COLUMNS = [
    "geo_code",
    "geo_level",
    "year",
    "indicator_id",
    "value",
    "lower",
    "upper",
    "unit",
    "source_id",
    "source_version",
    "retrieved_at",
    "license",
    "series_break",
]
KEY = ["indicator_id", "geo_code", "year"]


def _interval_contains_value(df: pd.DataFrame) -> pd.Series:
    lower_ok = df["lower"].isna() | (df["lower"] <= df["value"])
    upper_ok = df["upper"].isna() | (df["value"] <= df["upper"])
    return lower_ok & upper_ok


OBSERVATIONS = pa.DataFrameSchema(
    {
        "geo_code": pa.Column(str, pa.Check.str_matches(r"^[A-Z0-9]+$")),
        "geo_level": pa.Column(str, pa.Check.isin([lvl.value for lvl in Level])),
        "year": pa.Column(int, pa.Check.in_range(1900, 2100)),
        "indicator_id": pa.Column(str),
        "value": pa.Column(float),
        "lower": pa.Column(float, nullable=True),
        "upper": pa.Column(float, nullable=True),
        "unit": pa.Column(str),
        "source_id": pa.Column(str),
        "source_version": pa.Column(str),
        "retrieved_at": pa.Column(str),
        "license": pa.Column(str),
        "series_break": pa.Column(bool),
    },
    checks=pa.Check(_interval_contains_value, error="lower <= value <= upper"),
    unique=KEY,
    strict=True,
    ordered=True,
    coerce=True,
)


def empty() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype=object) for c in COLUMNS})


def tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce to the schema and sort deterministically so outputs diff cleanly."""
    df = OBSERVATIONS.validate(df[COLUMNS], lazy=True)
    return df.sort_values(KEY, ignore_index=True)


def row(
    snapshot: Snapshot,
    ind: Indicator,
    geo: Geography,
    year: int,
    value: float,
    lower: float | None = None,
    upper: float | None = None,
) -> dict:
    """One observation in the common format, with provenance taken from the snapshot."""
    return {
        "geo_code": geo.code,
        "geo_level": geo.level.value,
        "year": year,
        "indicator_id": ind.id,
        "value": value,
        "lower": lower,
        "upper": upper,
        "unit": ind.unit,
        "source_id": snapshot.source_id,
        "source_version": snapshot.source_version,
        "retrieved_at": snapshot.retrieved_at,
        "license": snapshot.license,
        "series_break": False,
    }
