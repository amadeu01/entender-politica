"""Education by government period: what each government started, what was cut, and the
metrics beside both (ADR 0013).

One file per period in `education/governos/<period-id>.yaml`. Like analyses (ADR 0007):
numbers in prose enter only through `v`, `diff`, `pct` and `lit` placeholders. Sources are
official records or institutional reports given by URL; peer-reviewed literature enters
only once its DOI is in the verified registry (`compilador verify-dois`), which is
why there is no `cite` here. The view is descriptive (ADR 0003): a series that moves
during a government does not show that the government caused it.
"""

import datetime as dt
from enum import StrEnum
from pathlib import Path

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from compilador import REPO_ROOT, content
from compilador.analyses import LANGS, Renderer
from compilador.catalog import Indicator, Reference
from compilador.education import FOCUS_GEO, Law, Module
from compilador.governments import Governments, Period
from compilador.i18n import Text
from compilador.periods import LAGS, RELATIVE_UNITS, TABLE_GEOGRAPHIES

GOVERNMENTS_SUBDIR = "governos"
EDUCATION_DIR = REPO_ROOT / "education"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CutKind(StrEnum):
    # Planned or executed spending was reduced.
    CUT = "cut"
    # Funds were authorized but withheld during the year (contingenciamento, bloqueio).
    WITHHELD = "withheld"
    # A spending ceiling or fiscal rule limited growth.
    FISCAL_RULE = "fiscal_rule"
    # An earmark or minimum was changed (vinculação, DRU).
    EARMARK = "earmark"
    # Funding provisions were vetoed.
    VETO = "veto"


class LaterStatus(StrEnum):
    MAINTAINED = "maintained"
    EXPANDED = "expanded"
    REDUCED = "reduced"
    AMENDED = "amended"
    REPLACED = "replaced"
    ENDED = "ended"


class Later(Strict):
    """What happened to a policy after it started, in a later year and often a later government."""

    year: int = Field(ge=1900, le=2100)
    status: LaterStatus
    # Designation of the norm that did it (`Decreto 11.556/2023`), when there is one.
    by: str | None = None
    note: Text


class Started(Strict):
    title: Text
    year: int = Field(ge=1900, le=2100)
    date: dt.date | None = None
    # Designation of the instrument (`Lei 9.424/1996`), when it has one.
    instrument: str | None = None
    # Slug in `education/normas` when the instrument is a record there.
    norm: str | None = None
    submodules: list[str] = Field(min_length=1)
    description: Text
    source: HttpUrl
    # Date someone matched this item against the official record. Empty means not checked,
    # and the site says so.
    checked: dt.date | None = None
    later: list[Later] = []

    @model_validator(mode="after")
    def _date_in_year(self) -> "Started":
        for step in self.later:
            if step.year < self.year:
                raise ValueError(
                    f"{self.title.en}: a later step in {step.year} precedes {self.year}"
                )
        if self.date is not None and self.date.year != self.year:
            raise ValueError(f"{self.title.en}: date {self.date} is not in year {self.year}")
        return self


class Cut(Strict):
    kind: CutKind
    title: Text
    year: int = Field(ge=1900, le=2100)
    date: dt.date | None = None
    # Designation of the decree or amendment behind the cut, when there is one.
    instrument: str | None = None
    submodules: list[str] = Field(min_length=1)
    description: Text
    source: HttpUrl
    checked: dt.date | None = None

    @model_validator(mode="after")
    def _date_in_year(self) -> "Cut":
        if self.date is not None and self.date.year != self.year:
            raise ValueError(f"{self.title.en}: date {self.date} is not in year {self.year}")
        return self


class GovernmentEducation(Strict):
    # Period in `data/reference/governos.yaml` this file is about, and the acting periods
    # folded into it (e.g. Temer's interim months into his term).
    period: str
    includes: list[str] = []
    summary: Text
    # Other factors that moved the same series (external shocks, other actors).
    context: Text
    started: list[Started] = []
    cuts: list[Cut] = []
    # Series shown beside both lists, for Brazil and the reference geographies.
    indicators: list[str] = Field(min_length=1)
    limitations: list[Text] = Field(min_length=1)
    references: list[Reference] = Field(min_length=1)

    @model_validator(mode="after")
    def _has_content(self) -> "GovernmentEducation":
        if not self.started and not self.cuts:
            raise ValueError(f"{self.period}: needs at least one start or one cut")
        return self


def load(directory: Path = EDUCATION_DIR) -> list[GovernmentEducation]:
    out = []
    for path in sorted((directory / GOVERNMENTS_SUBDIR).glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"{path.name}: empty or not a mapping")
        doc = GovernmentEducation.model_validate(raw)
        if path.stem != doc.period:
            raise ValueError(f"{path.name}: file name must be '{doc.period}.yaml'")
        out.append(doc)
    return out


def _texts(doc: GovernmentEducation) -> list[tuple[str, Text]]:
    found = [("summary", doc.summary), ("context", doc.context)]
    found += [(f"limitation {i}", t) for i, t in enumerate(doc.limitations)]
    for s in doc.started:
        found += [(f"started '{s.title.en}'", s.title), (f"started '{s.title.en}'", s.description)]
        found += [(f"later '{s.title.en}' {x.year}", x.note) for x in s.later]
    for c in doc.cuts:
        found += [(f"cut '{c.title.en}'", c.title), (f"cut '{c.title.en}'", c.description)]
    return found


def check(
    docs: list[GovernmentEducation],
    govs: Governments,
    module: Module,
    laws: list[Law],
    indicators: dict[str, Indicator],
    registry: dict[str, dict],
) -> list[str]:
    errors: list[str] = []
    period_ids = {p.id for p in govs.periods}
    sub_ids = {s.id for s in module.submodules}
    law_slugs = {law.slug for law in laws}
    designations = {law.slug: law.designation for law in laws}
    seen: set[str] = set()
    for doc in docs:
        where = f"education/governos/{doc.period}"
        claimed = [doc.period, *doc.includes]
        errors += [f"{where}: unknown period '{p}'" for p in claimed if p not in period_ids]
        errors += [f"{where}: period '{p}' is described twice" for p in claimed if p in seen]
        seen.update(claimed)
        errors += [
            f"{where}: unknown indicator '{i}'" for i in doc.indicators if i not in indicators
        ]
        window_years = _period_years(govs, claimed)
        for item in [*doc.started, *doc.cuts]:
            if window_years and item.year not in window_years:
                errors.append(
                    f"{where}: '{item.title.en}' is in {item.year}, outside the period "
                    f"({window_years[0]}–{window_years[-1]})"
                )
            errors += [
                f"{where}: unknown sub-module '{s}' in '{item.title.en}'"
                for s in item.submodules
                if s not in sub_ids
            ]
        for s in doc.started:
            if s.norm and s.norm not in law_slugs:
                errors.append(f"{where}: '{s.title.en}' names norm '{s.norm}', not in normas")
            elif s.norm and s.instrument and designations[s.norm] != s.instrument:
                errors.append(f"{where}: '{s.title.en}' instrument differs from norm '{s.norm}'")
        for label, text in _texts(doc):
            for lang in LANGS:
                errors += [
                    f"{where} {label} ({lang}): {n}"
                    for n in content.bare_numbers(getattr(text, lang))
                ]
            if content.data_keys(text.pt) != content.data_keys(text.en):
                errors.append(f"{where} {label}: pt and en cite different data (ADR 0004)")
            for lang in LANGS:
                if any(p.function == "cite" for p in content.placeholders(getattr(text, lang))):
                    errors.append(f"{where} {label} ({lang}): `cite` needs a verified DOI")
        errors += [
            f"{where}: a reference without a URL ({r.citation[:40]}…)"
            for r in doc.references
            if r.url is None
        ]
        errors += [
            f"{where}: DOI {r.doi} is not verified (run `compilador verify-dois`)"
            for r in doc.references
            if r.doi and r.doi.lower() not in registry
        ]
    return errors


def _period_years(govs: Governments, ids: list[str]) -> list[int]:
    """Calendar years touched by the periods, inclusive (the end date is exclusive)."""
    by_id = {p.id: p for p in govs.periods}
    spans = [by_id[i] for i in ids if i in by_id]
    if not spans:
        return []
    first = min(p.start.year for p in spans)
    ends = [p.end - dt.timedelta(days=1) if p.end else dt.date.max for p in spans]
    last = min(max(ends).year, dt.date.today().year + 1)
    return list(range(first, last + 1))


def window(govs: Governments, ids: list[str], last_year: int) -> list[int]:
    """Years attributed to any of the periods (the one in office on July 1)."""
    first = govs.periods[0].start.year + 1
    return [y for y in range(first, last_year + 1) if govs.for_year(y).id in ids]


def _changes(
    df: pd.DataFrame,
    govs: Governments,
    years: list[int],
    indicators: dict[str, Indicator],
    ids: list[str],
) -> list[dict]:
    values = df.set_index(["indicator_id", "geo_code", "year"])["value"]
    rows = []
    for lag in LAGS:
        start, end = years[0] - 1 + lag, years[-1] + lag
        mixed = [y for y in range(start, end + 1) if govs.changes_in_year(y)]
        for ind in ids:
            relative = indicators[ind].unit in RELATIVE_UNITS
            for geo in TABLE_GEOGRAPHIES:
                a, b = values.get((ind, geo, start)), values.get((ind, geo, end))
                change = None
                if a is not None and b is not None:
                    change = float((b / a - 1) * 100 if relative else b - a)
                rows.append(
                    {
                        "indicator_id": ind,
                        "geo_code": geo,
                        "lag": lag,
                        "start_year": start,
                        "end_year": end,
                        "start_value": None if a is None else float(a),
                        "end_value": None if b is None else float(b),
                        "change": change,
                        "relative": relative,
                        "mixed_years": mixed,
                    }
                )
    return rows


def _trend(
    df: pd.DataFrame,
    years: list[int],
    ids: list[str],
    indicators: dict[str, Indicator],
    geos: tuple[str, ...] = ("BRA", "LCN"),
) -> list[dict]:
    """Yearly rate of change in the window against the same-length window just before it.

    Descriptive: it asks whether the pace changed, not why (ADR 0013). Rows exist only when
    the series has all three end points. Series in a relative unit (the same ones the change
    table shows in %) get a percent-per-year rate, as in the table; the others, the unit per year.
    """
    values = df.set_index(["indicator_id", "geo_code", "year"])["value"]
    start, end = years[0] - 1, years[-1]
    length = end - start
    rows = []
    for ind in ids:
        relative = indicators[ind].unit in RELATIVE_UNITS
        for geo in geos:
            pts = [values.get((ind, geo, y)) for y in (start - length, start, end)]
            if any(p is None or pd.isna(p) for p in pts):
                continue
            before, baseline, after = (float(p) for p in pts)
            if relative:
                if before <= 0 or baseline <= 0:
                    continue
                before_rate = (baseline / before - 1) * 100 / length
                during_rate = (after / baseline - 1) * 100 / length
            else:
                before_rate = (baseline - before) / length
                during_rate = (after - baseline) / length
            rows.append(
                {
                    "indicator_id": ind,
                    "geo_code": geo,
                    "before_from": start - length,
                    "from": start,
                    "to": end,
                    "before_rate": before_rate,
                    "during_rate": during_rate,
                    "relative": relative,
                }
            )
    return rows


def _value_at(df: pd.DataFrame, indicator_id: str, year: int) -> float | None:
    rows = df[
        (df["indicator_id"] == indicator_id) & (df["geo_code"] == FOCUS_GEO) & (df["year"] == year)
    ]
    return None if rows.empty else float(rows["value"].iloc[0])


def render(
    doc: GovernmentEducation,
    lang: str,
    df: pd.DataFrame,
    indicators: dict[str, Indicator],
    govs: Governments,
    laws: list[Law],
) -> dict:
    """The JSON document of one period in one language."""
    r = Renderer(content.Resolver(df, indicators, [], lang))
    ids = [doc.period, *doc.includes]
    by_id: dict[str, Period] = {p.id: p for p in govs.periods}
    periods_ = [by_id[i] for i in ids]
    last_year = int(df["year"].max())
    years = window(govs, ids, last_year)
    norm_designation = {law.slug: law.designation for law in laws}

    def values(year: int) -> dict[str, float | None]:
        return {i: _value_at(df, i, year) for i in doc.indicators}

    def later(step: Later) -> dict:
        return {
            "year": step.year,
            "status": step.status.value,
            "by": step.by,
            "note": r.text(step.note),
        }

    def item(x: Started | Cut) -> dict:
        return {
            "title": r.text(x.title),
            "description": r.text(x.description, block=True),
            "year": x.year,
            "date": x.date.isoformat() if x.date else None,
            "submodules": x.submodules,
            "source": str(x.source),
            "checked": x.checked.isoformat() if x.checked else None,
            "values": values(x.year),
        }

    started = [
        item(s)
        | {"instrument": s.instrument, "norm": s.norm, "later": [later(x) for x in s.later]}
        | {"norm_designation": norm_designation.get(s.norm or "")}
        for s in doc.started
    ]
    cuts = [item(c) | {"kind": c.kind.value, "instrument": c.instrument} for c in doc.cuts]
    key = lambda e: (e["date"] or f"{e['year']}", e["title"])  # noqa: E731
    out = {
        "id": doc.period,
        "lang": lang,
        "periods": [p.model_dump(mode="json") for p in periods_],
        "years": [years[0], years[-1]] if years else [],
        "summary": r.text(doc.summary, block=True),
        "context": r.text(doc.context, block=True),
        "started": sorted(started, key=key),
        "cuts": sorted(cuts, key=key),
        "indicators": doc.indicators,
        "changes": _changes(df, govs, years, indicators, doc.indicators) if years else [],
        "trend": _trend(df, years, doc.indicators, indicators) if years else [],
        "limitations": [r.text(t, block=True) for t in doc.limitations],
        "references": [
            {"citation": ref.citation, "doi": ref.doi, "url": str(ref.url)}
            for ref in doc.references
        ],
    }
    out["numbers"] = [
        {k: (list(v) if isinstance(v, tuple) else v) for k, v in c.__dict__.items()}
        for c in r.cited
    ]
    return out
