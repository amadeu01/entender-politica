"""Bilingual text. Every user-facing string in the project exists in pt-BR and English."""

from pydantic import BaseModel, ConfigDict, Field


class Text(BaseModel):
    """A string in both site languages. Neither may be empty (see ADR 0004)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    pt: str = Field(min_length=1)
    en: str = Field(min_length=1)
