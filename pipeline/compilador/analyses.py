"""Analyses (`analyses/<slug>/`) and policy briefs (`policies/<slug>.yaml`).

Both are validated against the catalog, the data and the DOI registry, and rendered to
JSON for the site with every number resolved and traceable (see `content`).
"""

from enum import StrEnum
from pathlib import Path

import markdown
import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from compilador import REPO_ROOT, content
from compilador.catalog import Indicator, Reference
from compilador.i18n import Text

ANALYSES_DIR = REPO_ROOT / "analyses"
POLICIES_DIR = REPO_ROOT / "policies"
LANGS = ("pt", "en")


class Method(StrEnum):
    DESCRIPTIVE = "descriptive"
    DECOMPOSITION = "decomposition"
    REVIEW = "review"
    RCT = "rct"
    DIFFERENCE_IN_DIFFERENCES = "difference_in_differences"
    REGRESSION_DISCONTINUITY = "regression_discontinuity"
    SYNTHETIC_CONTROL = "synthetic_control"
    INSTRUMENTAL_VARIABLES = "instrumental_variables"
    OBSERVATIONAL = "observational"


CAUSAL_METHODS = {
    Method.RCT,
    Method.DIFFERENCE_IN_DIFFERENCES,
    Method.REGRESSION_DISCONTINUITY,
    Method.SYNTHETIC_CONTROL,
    Method.INSTRUMENTAL_VARIABLES,
}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Period(Strict):
    start: int
    end: int


class Evidence(Strict):
    text: Text
    references: list[str] = Field(min_length=1)


class Chart(Strict):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    title: Text
    alt: Text
    indicators: list[str] = Field(min_length=1)
    geographies: list[str] = Field(min_length=1)
    log_scale: bool = False


class Analysis(Strict):
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    title: Text
    question: Text
    hypothesis: Text
    indicators: list[str] = Field(min_length=1)
    geographies: list[str] = Field(min_length=1)
    period: Period
    method: Method
    method_description: Text
    causal_claims: bool
    evidence_for: list[Evidence] = Field(min_length=1)
    evidence_against: list[Evidence] = Field(min_length=1)
    limitations: list[Text] = Field(min_length=1)
    references: list[Reference] = Field(min_length=1)
    charts: list[Chart] = []
    related_policies: list[str] = []

    @model_validator(mode="after")
    def _causality_needs_design(self) -> "Analysis":
        if self.causal_claims and self.method not in CAUSAL_METHODS:
            raise ValueError(f"{self.slug}: causal claims need a causal design, not {self.method}")
        return self


class Direction(StrEnum):
    POSITIVE = "positive"
    NULL = "null"
    NEGATIVE = "negative"
    MIXED = "mixed"


class Finding(Strict):
    outcome: Text
    result: Text
    direction: Direction
    method: Method
    references: list[str] = Field(min_length=1)


class Policy(Strict):
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    name: Text
    country: str = Field(pattern=r"^[A-Z]{3}$")
    period: Period
    summary: Text
    mechanism: Text
    findings: list[Finding] = Field(min_length=1)
    external_validity: Text
    limitations: list[Text] = Field(min_length=1)
    references: list[Reference] = Field(min_length=1)
    # Required when every finding is positive: say where contrary evidence was sought.
    contrary_evidence_search: Text | None = None

    @model_validator(mode="after")
    def _neutrality(self) -> "Policy":
        only_positive = all(f.direction == Direction.POSITIVE for f in self.findings)
        if only_positive and self.contrary_evidence_search is None:
            raise ValueError(
                f"{self.slug}: all findings positive; add a null/negative/mixed finding or "
                "describe in contrary_evidence_search where contrary evidence was sought"
            )
        return self

    @property
    def evidence_level(self) -> str:
        methods = {f.method for f in self.findings}
        if methods & {Method.RCT, Method.REVIEW}:
            return "high"
        if methods & CAUSAL_METHODS:
            return "moderate"
        return "low"


def load_analyses(directory: Path = ANALYSES_DIR) -> list[tuple[Analysis, dict[str, str]]]:
    out = []
    for meta in sorted(directory.glob("*/analise.yaml")):
        analysis = Analysis.model_validate(yaml.safe_load(meta.read_text(encoding="utf-8")))
        if meta.parent.name != analysis.slug:
            raise ValueError(f"{meta}: folder name must be the slug '{analysis.slug}'")
        bodies = {}
        for lang in LANGS:
            body = meta.parent / f"texto.{lang}.md"
            if not body.exists():
                raise ValueError(f"{analysis.slug}: missing {body.name} (ADR 0004)")
            bodies[lang] = body.read_text(encoding="utf-8")
        out.append((analysis, bodies))
    return out


def load_policies(directory: Path = POLICIES_DIR) -> list[Policy]:
    out = []
    for path in sorted(directory.glob("*.yaml")):
        policy = Policy.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        if path.stem != policy.slug:
            raise ValueError(f"{path.name}: file name must be '{policy.slug}.yaml'")
        out.append(policy)
    return out


def cited_dois(analyses: list[tuple[Analysis, dict]], policies: list[Policy]) -> set[str]:
    refs = [r for a, _ in analyses for r in a.references] + [
        r for p in policies for r in p.references
    ]
    return {r.doi.lower() for r in refs if r.doi}


def _texts(model: BaseModel) -> list[Text]:
    """Every bilingual text field in a model, recursively."""
    found = []
    for value in model.__dict__.values():
        items = value if isinstance(value, list) else [value]
        for item in items:
            if isinstance(item, Text):
                found.append(item)
            elif isinstance(item, BaseModel):
                found += _texts(item)
    return found


def check(
    analyses: list[tuple[Analysis, dict[str, str]]],
    policies: list[Policy],
    indicators: dict[str, Indicator],
    geographies: set[str],
) -> list[str]:
    """Content rules that do not need the data: returns error messages."""
    errors = []
    policy_slugs = {p.slug for p in policies}
    for a, bodies in analyses:
        where = f"analyses/{a.slug}"
        chart_indicators = {i for c in a.charts for i in c.indicators}
        for ind in sorted(set(a.indicators) | chart_indicators):
            if ind not in indicators:
                errors.append(f"{where}: indicator '{ind}' not in catalog")
        for geo in sorted(set(a.geographies) | {g for c in a.charts for g in c.geographies}):
            if geo not in geographies:
                errors.append(f"{where}: geography '{geo}' not covered")
        for slug in a.related_policies:
            if slug not in policy_slugs:
                errors.append(f"{where}: related policy '{slug}' does not exist")
        errors += _reference_errors(where, a.references, [*a.evidence_for, *a.evidence_against])
        for lang, body in bodies.items():
            errors += [f"{where}/texto.{lang}.md {n}" for n in content.bare_numbers(body)]
        if content.data_keys(bodies["pt"]) != content.data_keys(bodies["en"]):
            errors.append(f"{where}: pt and en texts cite different data (ADR 0004)")
        errors += _text_field_errors(where, _texts(a))
    for p in policies:
        where = f"policies/{p.slug}.yaml"
        errors += _reference_errors(where, p.references, p.findings)
        errors += _text_field_errors(where, _texts(p))
    return errors


def _reference_errors(where: str, references: list[Reference], items: list) -> list[str]:
    known = {r.doi.lower() for r in references if r.doi}
    return [
        f"{where}: evidence cites {doi}, which is not in references"
        for item in items
        for doi in item.references
        if doi.lower() not in known
    ]


def _text_field_errors(where: str, texts: list[Text]) -> list[str]:
    errors = []
    for t in texts:
        for lang in LANGS:
            errors += [
                f"{where} ({lang}) {n}: '{getattr(t, lang)[:60]}…'"
                for n in content.bare_numbers(getattr(t, lang))
            ]
        if content.data_keys(t.pt) != content.data_keys(t.en):
            errors.append(f"{where}: pt and en cite different data in '{t.pt[:60]}…'")
    return errors


class Renderer:
    """Renders one document in one language, numbering cited values in reading order."""

    def __init__(self, resolver: content.Resolver):
        self._resolver = resolver
        self.cited: list[content.Cited] = []

    def html(self, text: str, block: bool = True) -> str:
        rendered, cited = self._resolver.render(text, start=len(self.cited) + 1)
        self.cited += cited
        out = markdown.markdown(rendered)
        if not block:
            out = out.removeprefix("<p>").removesuffix("</p>")
        return out

    def text(self, t: Text, block: bool = False) -> str:
        return self.html(getattr(t, self._resolver.lang), block)


def _references(refs: list[Reference], registry: dict[str, dict]) -> list[dict]:
    return [
        {
            "citation": r.citation,
            "doi": r.doi,
            "url": str(r.url) if r.url else None,
            "bibtex": registry.get(r.doi.lower(), {}).get("bibtex") if r.doi else None,
        }
        for r in refs
    ]


def _cited(cited: list[content.Cited]) -> list[dict]:
    return [
        {k: (list(v) if isinstance(v, tuple) else v) for k, v in c.__dict__.items()} for c in cited
    ]


def render_analysis(
    a: Analysis,
    body: str,
    lang: str,
    observations: pd.DataFrame,
    indicators: dict[str, Indicator],
    registry: dict[str, dict],
) -> dict:
    dois = [r.doi for r in a.references if r.doi]
    r = Renderer(content.Resolver(observations, indicators, dois, lang))

    def evidence(items: list[Evidence]) -> list[dict]:
        return [{"text": r.text(e.text), "references": e.references} for e in items]

    doc = {
        "slug": a.slug,
        "lang": lang,
        "title": r.text(a.title),
        "question": r.text(a.question),
        "hypothesis": r.text(a.hypothesis),
        "indicators": a.indicators,
        "geographies": a.geographies,
        "period": a.period.model_dump(),
        "method": a.method.value,
        "method_description": r.text(a.method_description),
        "causal_claims": a.causal_claims,
        "body": r.html(body),
        "evidence_for": evidence(a.evidence_for),
        "evidence_against": evidence(a.evidence_against),
        "limitations": [r.text(t) for t in a.limitations],
        "charts": [
            c.model_dump(mode="json") | {"title": r.text(c.title), "alt": getattr(c.alt, lang)}
            for c in a.charts
        ],
        "related_policies": a.related_policies,
        "references": _references(a.references, registry),
    }
    doc["numbers"] = _cited(r.cited)
    return doc


def render_policy(
    p: Policy,
    lang: str,
    observations: pd.DataFrame,
    indicators: dict[str, Indicator],
    registry: dict[str, dict],
) -> dict:
    dois = [ref.doi for ref in p.references if ref.doi]
    r = Renderer(content.Resolver(observations, indicators, dois, lang))
    doc = {
        "slug": p.slug,
        "lang": lang,
        "name": r.text(p.name),
        "country": p.country,
        "period": p.period.model_dump(),
        "evidence_level": p.evidence_level,
        "summary": r.text(p.summary),
        "mechanism": r.text(p.mechanism),
        "findings": [
            {
                "outcome": r.text(f.outcome),
                "result": r.text(f.result),
                "direction": f.direction.value,
                "method": f.method.value,
                "references": f.references,
            }
            for f in p.findings
        ],
        "external_validity": r.text(p.external_validity),
        "limitations": [r.text(t) for t in p.limitations],
        "contrary_evidence_search": (
            r.text(p.contrary_evidence_search) if p.contrary_evidence_search else None
        ),
        "references": _references(p.references, registry),
    }
    doc["numbers"] = _cited(r.cited)
    return doc
