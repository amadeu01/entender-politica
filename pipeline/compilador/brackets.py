"""Income brackets in PPP dollars from IBGE per capita income percentiles (ADR 0011).

A share is an estimate: IBGE publishes only some percentiles, and between them the
distribution is interpolated linearly. A point estimate (`low == high`) is therefore not
an exact value.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from compilador import DATA_DIR
from compilador.catalog import Indicator
from compilador.validate import ValidationError

BRACKETS_FILE = DATA_DIR / "reference" / "faixas-de-renda.yaml"
GEO = "BRA"


class BracketError(ValueError):
    """The requested translation cannot be computed from the data."""


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ppp_base_year: int
    thresholds_usd_ppp: list[int] = Field(min_length=1)
    percentile_indicators: dict[int, str] = Field(min_length=2)
    ppp_indicator: str
    cpi_indicator: str
    income_indicators: list[str]

    @field_validator("thresholds_usd_ppp")
    @classmethod
    def _increasing(cls, v: list[int]) -> list[int]:
        if v != sorted(set(v)) or v[0] <= 0:
            raise ValueError("thresholds_usd_ppp must be positive and strictly increasing")
        return v

    @property
    def labels(self) -> list[str]:
        return [f"ate_{t}" for t in self.thresholds_usd_ppp] + [
            f"acima_{self.thresholds_usd_ppp[-1]}"
        ]

    @property
    def input_indicators(self) -> list[str]:
        return [*self.percentile_indicators.values(), self.ppp_indicator, self.cpi_indicator]


@dataclass(frozen=True)
class Share:
    """Percent of people. `low == high` is a linear-interpolation point estimate."""

    low: float
    high: float


def load(path: Path = BRACKETS_FILE, indicators: dict[str, Indicator] | None = None) -> Config:
    config = Config.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if indicators is not None:
        ids = [*config.input_indicators, *config.income_indicators]
        missing = [i for i in ids if i not in indicators]
        if missing:
            raise ValidationError([f"{path.name}: indicator not in catalog: {i}" for i in missing])
    return config


def _value(df: pd.DataFrame, indicator_id: str, year: int) -> float | None:
    rows = df[
        (df["geo_code"] == GEO) & (df["indicator_id"] == indicator_id) & (df["year"] == year)
    ]["value"].dropna()
    return float(rows.iloc[0]) if len(rows) else None


def reais_per_usd_ppp(df: pd.DataFrame, config: Config, year: int) -> float | None:
    """Reais per base-year PPP dollar in `year` prices: PPP[base] * CPI[year] / CPI[base]."""
    ppp = _value(df, config.ppp_indicator, config.ppp_base_year)
    cpi_base = _value(df, config.cpi_indicator, config.ppp_base_year)
    cpi_year = _value(df, config.cpi_indicator, year)
    if ppp is None or not cpi_base or cpi_year is None:
        return None
    return ppp * cpi_year / cpi_base


def share_below(limits: dict[int, float], value: float) -> Share:
    """Percent of people with income below `value`, given percentile -> income limit."""
    points = sorted(limits.items())
    (first_p, first_v), (last_p, last_v) = points[0], points[-1]
    if value < first_v:
        return Share(0, first_p)
    if value > last_v:
        return Share(last_p, 100)
    pairs = list(zip(points, points[1:], strict=False))
    for (p0, v0), (p1, v1) in pairs:
        if v0 == v1 == value:
            return Share(p0, p1)
    for (p0, v0), (p1, v1) in pairs:
        if v0 <= value <= v1:
            p = p0 + (p1 - p0) * (value - v0) / (v1 - v0)
            return Share(p, p)
    raise AssertionError("unreachable")  # pragma: no cover


def _limits(df: pd.DataFrame, config: Config, year: int) -> dict[int, float] | None:
    out = {p: _value(df, ind, year) for p, ind in config.percentile_indicators.items()}
    return None if any(v is None for v in out.values()) else out  # type: ignore[return-value]


def _years(df: pd.DataFrame, config: Config) -> list[int]:
    ids = list(config.percentile_indicators.values())
    return sorted(int(y) for y in df[df["indicator_id"].isin(ids)]["year"].unique())


def distribution(df: pd.DataFrame, config: Config) -> list[dict]:
    out = []
    for year in _years(df, config):
        rate = reais_per_usd_ppp(df, config, year)
        limits = _limits(df, config, year)
        if rate is None or limits is None:
            continue
        cdf = [Share(0, 0)]
        cdf += [share_below(limits, t * rate) for t in config.thresholds_usd_ppp]
        cdf.append(Share(100, 100))
        brackets = [
            {
                "label": label,
                "low": max(0.0, hi.low - lo.high),
                "high": max(0.0, hi.high - lo.low),
            }
            for label, lo, hi in zip(config.labels, cdf[:-1], cdf[1:], strict=True)
        ]
        out.append(
            {
                "year": year,
                "reais_per_usd_ppp": rate,
                "thresholds_brl": [t * rate for t in config.thresholds_usd_ppp],
                "brackets": brackets,
            }
        )
    return out


def translate(
    df: pd.DataFrame,
    config: Config,
    cut: int,
    side: Literal["bottom", "top"],
    year: int,
) -> dict:
    """Bracket of the income limit at percentile `cut` ("bottom 40%": 40; "top 10%": 90).

    For `bottom` it is the bracket holding the group's upper limit; for `top`, the one
    where the group starts. Both are the bracket of the percentile limit itself.
    """
    if cut not in config.percentile_indicators:
        raise BracketError(f"cut {cut} is not a published percentile")
    rate = reais_per_usd_ppp(df, config, year)
    limit = _value(df, config.percentile_indicators[cut], year)
    if rate is None or limit is None:
        raise BracketError(f"no income data for {year}")
    usd = limit / rate
    label = next(
        (f"ate_{t}" for t in config.thresholds_usd_ppp if usd <= t),
        config.labels[-1],
    )
    return {
        "cut": cut,
        "side": side,
        "year": year,
        "limit_brl": limit,
        "limit_usd_ppp": usd,
        "bracket": label,
    }


def sources(df: pd.DataFrame, config: Config) -> list[dict]:
    """Provenance of each input indicator, from the observations."""
    out = []
    for ind in config.input_indicators:
        rows = df[df["indicator_id"] == ind]
        if len(rows):
            first = rows.iloc[0]
            out.append(
                {
                    "indicator_id": ind,
                    "source_id": first["source_id"],
                    "source_version": first["source_version"],
                    "retrieved_at": first["retrieved_at"],
                }
            )
    return out
