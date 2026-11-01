"""Education module: sub-modules, the laws that shape them, and the metrics beside them.

Content lives in `education/`:

- `education/submodulos.yaml`: the sub-modules (early childhood, primary, ...), the
  indicators each one shows, and metrics that are planned but not collected yet;
- `education/normas/<slug>.yaml`: one file per constitutional amendment, law or bill,
  with the events that matter (proposal, committee and plenary votes, enactment,
  amendments by later laws, replacement).

Like analyses (ADR 0007), prose carries no hand-typed numbers: years, decades and
ordinals only. Law identifiers (`Lei 9.394/1996`) are structured fields, not prose.
Vote tallies and party orientations are *not* typed here; they are meant to come from a
fetched snapshot of the Câmara and Senado open data (ADR 0012), so a vote event records
only that a vote happened, in which chamber and in what form.
"""

import datetime as dt
from collections.abc import Iterable
from enum import StrEnum
from pathlib import Path

import pandas as pd
import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from compilador import REPO_ROOT, content
from compilador.catalog import Indicator
from compilador.i18n import Text

EDUCATION_DIR = REPO_ROOT / "education"
SUBMODULES_FILE = "submodulos.yaml"
LAWS_SUBDIR = "normas"
# Brazil is the geography the legal events are laid beside.
FOCUS_GEO = "BRA"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Kind(StrEnum):
    CONSTITUTIONAL_AMENDMENT = "constitutional_amendment"
    COMPLEMENTARY_LAW = "complementary_law"
    LAW = "law"


class EventType(StrEnum):
    PROPOSED = "proposed"
    COMMITTEE_VOTE = "committee_vote"
    PLENARY_VOTE = "plenary_vote"
    ENACTED = "enacted"
    AMENDED = "amended"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


VOTE_TYPES = {EventType.COMMITTEE_VOTE, EventType.PLENARY_VOTE}
# Events that a later norm causes: they must name it.
BY_TYPES = {EventType.AMENDED, EventType.REVOKED}


class Chamber(StrEnum):
    CAMARA = "camara"
    SENADO = "senado"
    CONGRESSO = "congresso"


class VoteForm(StrEnum):
    NOMINAL = "nominal"
    SYMBOLIC = "symbolic"
    CONCLUSIVE = "conclusive"
    UNKNOWN = "unknown"


class Event(Strict):
    year: int = Field(ge=1900, le=2100)
    date: dt.date | None = None
    type: EventType
    chamber: Chamber | None = None
    form: VoteForm | None = None
    # Designation of the norm that amended or revoked this one (`Lei 14.723/2023`).
    by: str | None = None
    description: Text

    @model_validator(mode="after")
    def _consistent(self) -> "Event":
        if self.date is not None and self.date.year != self.year:
            raise ValueError(f"event date {self.date} is not in year {self.year}")
        if self.type in VOTE_TYPES and self.chamber is None:
            raise ValueError(f"{self.type} event ({self.year}) needs a chamber")
        if self.type not in VOTE_TYPES and self.form is not None:
            raise ValueError(f"only vote events have a form ({self.type}, {self.year})")
        if self.type in BY_TYPES and not self.by:
            raise ValueError(f"{self.type} event ({self.year}) must name the norm in `by`")
        return self


class Law(Strict):
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    designation: str = Field(min_length=3)
    kind: Kind
    year: int = Field(ge=1900, le=2100)
    # Bill number while it was a bill (`PL 2614/2024`), when it differs from the law's.
    bill: str | None = None
    title: Text
    summary: Text
    submodules: list[str] = Field(min_length=1)
    events: list[Event] = Field(min_length=1)
    # Date someone matched this record against the official text. Empty means the record
    # was not checked yet, and the site says so.
    verified: dt.date | None = None

    @model_validator(mode="after")
    def _enacted(self) -> "Law":
        enacted = [e for e in self.events if e.type == EventType.ENACTED]
        if len(enacted) != 1:
            raise ValueError(f"{self.slug}: exactly one 'enacted' event required")
        if enacted[0].year != self.year:
            raise ValueError(f"{self.slug}: enacted event year differs from law year")
        return self


class PlannedMetric(Strict):
    name: Text
    source: str
    # Series code at the source, when known. Confirm it against the API before adding it
    # to the catalog.
    code: str | None = None
    note: Text


class SubModule(Strict):
    id: str = Field(pattern=r"^[a-z0-9-]+$")
    name: Text
    summary: Text
    indicators: list[str] = []
    planned_metrics: list[PlannedMetric] = []


class Module(Strict):
    # Metrics that cover the whole system and sit above the sub-module navigation.
    overview_indicators: list[str] = []
    submodules: list[SubModule] = Field(min_length=1)


def load_module(directory: Path = EDUCATION_DIR) -> Module | None:
    """The module definition, or None when the directory has none (the module is optional)."""
    if not (directory / SUBMODULES_FILE).exists():
        return None
    with (directory / SUBMODULES_FILE).open(encoding="utf-8") as f:
        return Module.model_validate(yaml.safe_load(f))


def load_laws(directory: Path = EDUCATION_DIR) -> list[Law]:
    laws = []
    for path in sorted((directory / LAWS_SUBDIR).glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            law = Law.model_validate(yaml.safe_load(f))
        if path.stem != law.slug:
            raise ValueError(f"{path.name}: file name must be '{law.slug}.yaml'")
        laws.append(law)
    return laws


def _texts(law: Law) -> Iterable[tuple[str, Text]]:
    yield f"{law.slug} title", law.title
    yield f"{law.slug} summary", law.summary
    for e in law.events:
        yield f"{law.slug} event {e.year}", e.description


def check(module: Module, laws: list[Law], indicators: dict[str, Indicator]) -> list[str]:
    errors: list[str] = []
    sub_ids = [s.id for s in module.submodules]
    errors += [
        f"duplicate sub-module id: {i}"
        for i in sorted({i for i in sub_ids if sub_ids.count(i) > 1})
    ]
    slugs = [law.slug for law in laws]
    errors += [f"duplicate law slug: {s}" for s in sorted({s for s in slugs if slugs.count(s) > 1})]
    designations = [law.designation for law in laws]
    errors += [
        f"duplicate designation: {d}"
        for d in sorted({d for d in designations if designations.count(d) > 1})
    ]

    wanted = set(module.overview_indicators) | {i for s in module.submodules for i in s.indicators}
    errors += [
        f"unknown indicator in education module: {i}" for i in sorted(wanted - set(indicators))
    ]

    for law in laws:
        errors += [
            f"{law.slug}: unknown sub-module '{s}'" for s in law.submodules if s not in sub_ids
        ]
    prose = [(f"sub-module {s.id} summary", s.summary) for s in module.submodules]
    prose += [(f"sub-module {s.id} name", s.name) for s in module.submodules]
    prose += [
        (f"sub-module {s.id} planned metric note", m.note)
        for s in module.submodules
        for m in s.planned_metrics
    ]
    prose += [item for law in laws for item in _texts(law)]
    for where, text in prose:
        for lang in ("pt", "en"):
            numbers = content.bare_numbers(getattr(text, lang))
            if numbers:
                errors.append(f"{where} ({lang}): hand-typed numbers {numbers}")
    return errors


def _value_at(df: pd.DataFrame, indicator_id: str, year: int) -> float | None:
    rows = df[
        (df["indicator_id"] == indicator_id) & (df["geo_code"] == FOCUS_GEO) & (df["year"] == year)
    ]
    return None if rows.empty else float(rows["value"].iloc[0])


def render(module: Module, laws: list[Law], df: pd.DataFrame) -> dict[str, object]:
    """The JSON document the education page reads."""
    by_designation = {law.designation: law.slug for law in laws}
    law_docs = []
    for law in laws:
        events = sorted(law.events, key=lambda e: (e.year, e.date or dt.date(e.year, 1, 1)))
        law_docs.append(
            law.model_dump(mode="json", exclude={"events"})
            | {
                "events": [
                    e.model_dump(mode="json") | {"by_slug": by_designation.get(e.by or "")}
                    for e in events
                ]
            }
        )
    law_docs.sort(key=lambda d: (d["year"], d["designation"]))

    submodules = []
    for sub in module.submodules:
        # System-wide series sit beside every sub-module's legal events; the sub-module's
        # own series follow them.
        shown = list(dict.fromkeys([*module.overview_indicators, *sub.indicators]))
        member = [law for law in laws if sub.id in law.submodules]
        marks = sorted(
            (
                {
                    "year": e.year,
                    "law": law.slug,
                    "designation": law.designation,
                    "type": e.type.value,
                    "chamber": e.chamber.value if e.chamber else None,
                    "form": e.form.value if e.form else None,
                    "by": e.by,
                    "by_slug": by_designation.get(e.by or ""),
                    "description": e.description.model_dump(),
                    "values": {i: _value_at(df, i, e.year) for i in shown},
                }
                for law in member
                for e in law.events
            ),
            key=lambda m: (m["year"], m["designation"]),
        )
        submodules.append(
            sub.model_dump(mode="json")
            | {"laws": [law.slug for law in member], "shown_indicators": shown, "events": marks}
        )
    return {
        "geography": FOCUS_GEO,
        "overview_indicators": module.overview_indicators,
        "submodules": submodules,
        "laws": law_docs,
    }
