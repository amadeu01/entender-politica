"""Content validation beyond the schema: catalog bounds, coverage and atypical jumps.

Errors stop the build. Warnings are recorded in the validation report for human review;
an atypical jump is often real (hyperinflation, a pandemic) and must not be "fixed".
"""

from dataclasses import asdict, dataclass, field

import pandas as pd

from compilador.catalog import Indicator
from compilador.geography import Geography

# A year-over-year change is atypical when its robust z-score exceeds this.
JUMP_Z = 5.0
# Robust z-scores need enough changes to estimate spread.
MIN_CHANGES_FOR_JUMPS = 8


class ValidationError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass
class Report:
    warnings: list[str] = field(default_factory=list)
    coverage: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def validate(
    df: pd.DataFrame, indicators: dict[str, Indicator], geos: dict[str, Geography] | None = None
) -> Report:
    errors: list[str] = []
    report = Report()

    # Missing values at the series level: a catalog indicator with no data for a geography.
    present = set(zip(df["indicator_id"], df["geo_code"], strict=True))
    for ind_id in sorted(indicators):
        for geo in sorted(geos or {}):
            if (ind_id, geo) not in present:
                report.warnings.append(f"{ind_id} {geo}: no observations")

    unknown = sorted(set(df["indicator_id"]) - set(indicators))
    if unknown:
        errors.append(f"indicators missing from catalog: {unknown}")

    for (ind_id, geo), series in df.groupby(["indicator_id", "geo_code"], sort=True):
        ind = indicators.get(ind_id)
        if ind is None:
            continue
        series = series.sort_values("year")
        errors += _bounds(ind, geo, series)
        report.coverage.append(_coverage(ind_id, geo, series))
        report.warnings += _jumps(ind_id, geo, series)

    if errors:
        raise ValidationError(errors)
    return report


def _bounds(ind: Indicator, geo: str, series: pd.DataFrame) -> list[str]:
    out = []
    if ind.min is not None:
        below = series[series["value"] < ind.min]
        out += [f"{ind.id} {geo} {r.year}: {r.value} < min {ind.min}" for r in below.itertuples()]
    if ind.max is not None:
        above = series[series["value"] > ind.max]
        out += [f"{ind.id} {geo} {r.year}: {r.value} > max {ind.max}" for r in above.itertuples()]
    return out


def _coverage(ind_id: str, geo: str, series: pd.DataFrame) -> dict:
    years = series["year"].tolist()
    first, last = min(years), max(years)
    missing = sorted(set(range(first, last + 1)) - set(years))
    return {
        "indicator_id": ind_id,
        "geo_code": geo,
        "first_year": first,
        "last_year": last,
        "observations": len(years),
        "missing_years": missing,
    }


def _jumps(ind_id: str, geo: str, series: pd.DataFrame) -> list[str]:
    # Only consecutive years: a change across a gap is not a year-over-year change.
    consecutive = series["year"].diff() == 1
    changes = series["value"].diff()[consecutive]
    if len(changes) < MIN_CHANGES_FOR_JUMPS:
        return []
    median = changes.median()
    mad = (changes - median).abs().median() * 1.4826
    if mad == 0:
        return []
    z = (changes - median) / mad
    flagged = series.loc[z[z.abs() > JUMP_Z].index]
    return [
        f"{ind_id} {geo} {r.year}: atypical year-over-year change "
        f"(robust z={z[i]:.1f}, value={r.value})"
        for i, r in zip(flagged.index, flagged.itertuples(), strict=True)
    ]
