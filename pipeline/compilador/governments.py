"""Reference table of Brazilian federal government periods (see ADR 0003)."""

from datetime import date, timedelta
from enum import StrEnum
from itertools import pairwise
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from compilador import DATA_DIR
from compilador.i18n import Text

GOVERNMENTS_FILE = DATA_DIR / "reference" / "governos.yaml"
# Inaugurations at the regular start of a term (January 1, or January 5 from 2027 under
# Constitutional Amendment 111/2021) do not make a year "mixed" for annual data.
TERM_START_GRACE = timedelta(days=15)


class Condition(StrEnum):
    INCUMBENT = "titular"
    ACTING = "interino"


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
    note: Text | None = None

    @model_validator(mode="after")
    def _end_after_start(self) -> "Period":
        if self.end is not None and self.end <= self.start:
            raise ValueError(f"{self.id}: end {self.end} must be after start {self.start}")
        return self


class Governments(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    sources: list[HttpUrl] = Field(min_length=1)
    verified_on: date
    periods: list[Period] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_and_contiguous(self) -> "Governments":
        ids = [p.id for p in self.periods]
        if len(ids) != len(set(ids)):
            raise ValueError("period ids must be unique")
        # Contiguity also guarantees that only the last period can be ongoing.
        for prev, cur in pairwise(self.periods):
            if prev.end != cur.start:
                raise ValueError(
                    f"gap or overlap between {prev.id} (end {prev.end}) and {cur.id} "
                    f"(start {cur.start})"
                )
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
        """True if a different person took office during `year`, after the regular
        start-of-term window. A new term of the same person does not count."""
        return any(
            prev.president != cur.president
            and cur.start.year == year
            and cur.start - date(year, 1, 1) > TERM_START_GRACE
            for prev, cur in pairwise(self.periods)
        )


def load(path: Path = GOVERNMENTS_FILE) -> Governments:
    with path.open(encoding="utf-8") as f:
        return Governments.model_validate(yaml.safe_load(f))
