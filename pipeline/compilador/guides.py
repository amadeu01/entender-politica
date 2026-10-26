"""Indicator guides (`guides/<indicator-id>.yaml`): what an indicator measures, what
studies say about it, which policies moved it and how it reads by income bracket.

Same rules as policy briefs (ADR 0007, 0011): bilingual text with no hand-typed numbers,
every cited DOI listed in `references`, and policy results never all positive without a
documented search for contrary evidence.
"""

from pathlib import Path
from typing import Literal

import pandas as pd
import yaml
from pydantic import Field, model_validator

from compilador import REPO_ROOT, brackets, content
from compilador.analyses import (
    Direction,
    Method,
    Period,
    Renderer,
    Strict,
    _cited,
    _reference_errors,
    _references,
    _text_field_errors,
    _texts,
    evidence_level,
    needs_contrary_search,
)
from compilador.catalog import Indicator, Reference
from compilador.i18n import Text
from compilador.validate import ValidationError

GUIDES_DIR = REPO_ROOT / "guides"
FIRST_INCOME_YEAR = 2012


class IncomeGroup(Strict):
    """A group defined by a percentile cut, as in `brackets.translate`."""

    cut: int
    side: Literal["bottom", "top"]
    year: int = Field(ge=FIRST_INCOME_YEAR)


class IncomeEffect(Strict):
    text: Text
    study_period: Period
    group: IncomeGroup | None = None
    references: list[str] = Field(min_length=1)


class StudyEntry(Strict):
    """A study about the indicator: shows its design, not an evidence level."""

    text: Text
    method: Method
    references: list[str] = Field(min_length=1)


class PolicyEntry(Strict):
    name: Text
    country: str = Field(pattern=r"^[A-Z]{3}$")
    period: Period
    result: Text
    direction: Direction
    method: Method
    references: list[str] = Field(min_length=1)
    brief: str | None = None


class Guide(Strict):
    indicator: str
    understand: Text
    how_to_read: Text
    studies: list[StudyEntry] = Field(min_length=1)
    policies: list[PolicyEntry] = Field(min_length=1)
    by_income: list[IncomeEffect] = []
    purchasing_power: Text | None = None
    contrary_evidence_search: Text | None = None
    references: list[Reference] = Field(min_length=1)

    @model_validator(mode="after")
    def _neutrality(self) -> "Guide":
        if (
            needs_contrary_search(p.direction for p in self.policies)
            and self.contrary_evidence_search is None
        ):
            raise ValueError(
                f"{self.indicator}: all policy results positive; add a null/negative/mixed "
                "result or describe in contrary_evidence_search where contrary evidence "
                "was sought"
            )
        return self


def load_guides(directory: Path = GUIDES_DIR) -> list[Guide]:
    out = []
    for path in sorted(directory.glob("*.yaml")):
        guide = Guide.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        if path.stem != guide.indicator:
            raise ValueError(f"{path.name}: file name must be '{guide.indicator}.yaml'")
        out.append(guide)
    return out


def check(
    guides: list[Guide],
    indicators: dict[str, Indicator],
    policy_slugs: set[str],
    config: brackets.Config | None = None,
) -> list[str]:
    """Content rules that do not need the data: returns error messages."""
    errors = []
    for g in guides:
        where = f"guides/{g.indicator}.yaml"
        if g.indicator not in indicators:
            errors.append(f"{where}: indicator '{g.indicator}' not in catalog")
        errors += _reference_errors(where, g.references, [*g.studies, *g.policies, *g.by_income])
        errors += _text_field_errors(where, _texts(g))
        errors += [
            f"{where}: brief '{p.brief}' is not a policy brief"
            for p in g.policies
            if p.brief is not None and p.brief not in policy_slugs
        ]
        if config is not None:
            errors += [
                f"{where}: cut {e.group.cut} is not a published percentile"
                for e in g.by_income
                if e.group and e.group.cut not in config.percentile_indicators
            ]
    return errors


def cited_dois(guides: list[Guide]) -> set[str]:
    return {r.doi.lower() for g in guides for r in g.references if r.doi}


def _split_references(g: Guide) -> tuple[list[Reference], list[Reference]]:
    """References cited only by studies, and all the others."""
    in_studies = {d.lower() for s in g.studies for d in s.references}
    elsewhere = {d.lower() for entry in [*g.policies, *g.by_income] for d in entry.references}
    only_studies = in_studies - elsewhere

    def is_indicator(r: Reference) -> bool:
        return bool(r.doi) and r.doi.lower() in only_studies

    return (
        [r for r in g.references if is_indicator(r)],
        [r for r in g.references if not is_indicator(r)],
    )


def _translation(
    group: IncomeGroup | None, df: pd.DataFrame, config: brackets.Config | None, where: str
) -> dict | None:
    if group is None:
        return None
    if config is None:
        raise ValidationError(
            [f"{where}: by_income groups need the income brackets inputs in the catalog"]
        )
    try:
        return brackets.translate(df, config, group.cut, group.side, group.year)
    except brackets.BracketError as e:
        raise ValidationError([f"{where}: {e} (year {group.year}, cut {group.cut})"]) from e


def render_guide(
    g: Guide,
    lang: str,
    df: pd.DataFrame,
    indicators: dict[str, Indicator],
    registry: dict[str, dict],
    brackets_config: brackets.Config | None,
) -> dict:
    where = f"guides/{g.indicator}.yaml"
    dois = [ref.doi for ref in g.references if ref.doi]
    r = Renderer(content.Resolver(df, indicators, dois, lang))
    only_studies, others = _split_references(g)
    show_income = bool(g.by_income) or (
        brackets_config is not None and g.indicator in brackets_config.income_indicators
    )
    doc = {
        "indicator": g.indicator,
        "lang": lang,
        "understand": r.text(g.understand, block=True),
        "how_to_read": r.text(g.how_to_read, block=True),
        "studies": [
            {"text": r.text(s.text), "method": s.method.value, "references": s.references}
            for s in g.studies
        ],
        "policies": [
            {
                "name": r.text(p.name),
                "country": p.country,
                "period": p.period.model_dump(),
                "result": r.text(p.result),
                "direction": p.direction.value,
                "method": p.method.value,
                "evidence_level": evidence_level({p.method}),
                "references": p.references,
                "brief": p.brief,
            }
            for p in g.policies
        ],
        "by_income": [
            {
                "text": r.text(e.text),
                "study_period": e.study_period.model_dump(),
                "group": e.group.model_dump() if e.group else None,
                "translation": _translation(e.group, df, brackets_config, where),
                "references": e.references,
            }
            for e in g.by_income
        ],
        "show_income": show_income,
        "purchasing_power": r.text(g.purchasing_power, block=True) if g.purchasing_power else None,
        "contrary_evidence_search": (
            r.text(g.contrary_evidence_search) if g.contrary_evidence_search else None
        ),
        "references_indicator": _references(only_studies, registry),
        "references_policies": _references(others, registry),
    }
    doc["numbers"] = _cited(r.cited)
    return doc
