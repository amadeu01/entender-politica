"""Indicator catalog: one YAML file per indicator in /indicators.

The catalog is both documentation (rendered on the site) and configuration: connectors
fetch exactly the indicators listed here for their source.
"""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from compilador import REPO_ROOT
from compilador.i18n import Text

INDICATORS_DIR = REPO_ROOT / "indicators"


class Reference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    citation: str
    doi: str | None = Field(default=None, pattern=r"^10\.\d{4,9}/\S+$")
    url: HttpUrl | None = None

    @model_validator(mode="after")
    def _locatable(self) -> "Reference":
        if self.doi is None and self.url is None:
            raise ValueError(f"reference needs a doi or url: {self.citation}")
        return self


class SeriesBreak(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    year: int
    note: Text


class Indicator(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[a-z0-9_]+\.[a-z0-9_]+$")
    source: str
    source_code: str
    # Connector-specific parameters (e.g. SIDRA table and variables).
    source_params: dict[str, str] = {}
    name: Text
    unit: str
    definition: Text
    formula: Text
    criticisms: list[Text] = Field(min_length=1)
    references: list[Reference] = Field(min_length=1)
    # How `lower`/`upper` are derived when the source publishes uncertainty.
    uncertainty: Text | None = None
    min: float | None = None
    max: float | None = None
    series_breaks: list[SeriesBreak] = []

    @model_validator(mode="after")
    def _id_matches_source(self) -> "Indicator":
        if not self.id.startswith(f"{self.source}."):
            raise ValueError(f"{self.id}: id must start with source '{self.source}.'")
        return self


def load(directory: Path = INDICATORS_DIR) -> dict[str, Indicator]:
    indicators: dict[str, Indicator] = {}
    for path in sorted(directory.glob("*.yaml")):
        with path.open(encoding="utf-8") as f:
            ind = Indicator.model_validate(yaml.safe_load(f))
        if path.stem != ind.id:
            raise ValueError(f"{path.name}: file name must be '{ind.id}.yaml'")
        indicators[ind.id] = ind
    return indicators


def for_source(indicators: dict[str, Indicator], source_id: str) -> list[Indicator]:
    return [i for i in indicators.values() if i.source == source_id]
