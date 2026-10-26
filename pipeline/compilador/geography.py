"""Geographies covered by the site: Brazil plus comparison countries and aggregates."""

from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from compilador import DATA_DIR
from compilador.i18n import Text

GEOGRAPHIES_FILE = DATA_DIR / "reference" / "geografias.yaml"


class Level(StrEnum):
    COUNTRY = "country"
    AGGREGATE = "aggregate"
    STATE = "state"
    MUNICIPALITY = "municipality"


class Geography(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(pattern=r"^[A-Z0-9]+$")
    level: Level
    name: Text


def load(path: Path = GEOGRAPHIES_FILE) -> dict[str, Geography]:
    with path.open(encoding="utf-8") as f:
        geos = [Geography.model_validate(g) for g in yaml.safe_load(f)["geographies"]]
    return {g.code: g for g in geos}
