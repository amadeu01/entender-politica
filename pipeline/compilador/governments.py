"""Reference table of Brazilian federal government periods (see ADR 0003)."""

from datetime import date
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from compilador import DATA_DIR
from compilador.i18n import Text

GOVERNMENTS_FILE = DATA_DIR / "reference" / "governos.yaml"


class Condition(StrEnum):
    TITULAR = "titular"
    INTERINO = "interino"


class Period(BaseModel):
    """A continuous stretch in which one person exercised the presidency.

    `end` is exclusive and is the `start` of the next period; `None` means ongoing.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[a-z0-9-]+$")
    president: str
    # Name used on chart bands, as commonly known (e.g. "FHC", "Lula").
    short_name: str
    condition: Condition
    term: Text
    start: date
    end: date | None
    regime: Text
    note: Text | None = None

    @model_validator(mode="after")
    def _end_after_start(self) -> "Period":
        if self.end is not None and self.end <= self.start:
            raise ValueError(f"{self.id}: end {self.end} must be after start {self.start}")
        return self


class Governments(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sources: list[HttpUrl] = Field(min_length=1)
    periods: list[Period] = Field(min_length=1)

    @model_validator(mode="after")
    def _contiguous(self) -> "Governments":
        ids = [p.id for p in self.periods]
        if len(ids) != len(set(ids)):
            raise ValueError("period ids must be unique")
        for prev, cur in zip(self.periods, self.periods[1:], strict=False):
            if prev.end != cur.start:
                raise ValueError(
                    f"gap or overlap between {prev.id} (end {prev.end}) and {cur.id} "
                    f"(start {cur.start})"
                )
        if any(p.end is None for p in self.periods[:-1]):
            raise ValueError("only the last period may be ongoing")
        return self

    def at(self, day: date) -> Period:
        """Return the period in force on `day`."""
        for p in self.periods:
            if p.start <= day and (p.end is None or day < p.end):
                return p
        raise LookupError(f"no government period covers {day}")

    def for_year(self, year: int) -> Period:
        """Period an annual observation is attributed to: the one in office on July 1."""
        return self.at(date(year, 7, 1))

    def changes_in_year(self, year: int) -> bool:
        """True if the presidency changed hands during `year` (excluding January 1)."""
        return any(p.start.year == year and p.start != date(year, 1, 1) for p in self.periods)


def load(path: Path = GOVERNMENTS_FILE) -> Governments:
    with path.open(encoding="utf-8") as f:
        return Governments.model_validate(yaml.safe_load(f))
