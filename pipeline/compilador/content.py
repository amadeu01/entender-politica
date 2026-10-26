"""Traceable numbers in written content (analyses and policy briefs).

Text never contains a hand-typed number. Numbers enter through placeholders:

- `{{ v("indicator", "GEO", year) }}`: a value from the repository's data;
- `{{ diff("indicator", "GEO", y0, y1) }}`: signed change between two years;
- `{{ pct("indicator", "GEO", y0, y1) }}`: signed relative change, in percent;
- `{{ cite("text", "doi", "location") }}`: a number quoted from a peer-reviewed paper,
  e.g. `cite("21%", "10.24201/ee.v0i0.387", "abstract")`;
- `{{ lit("text", "reason") }}`: anything else, with a written justification.

Years, decades and ordinals may be written directly. Everything else is rejected.
"""

import ast
import html
import re
from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd

from compilador.catalog import Indicator

PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\((.*?)\)\s*\}\}")
DATA_FUNCTIONS = {"v", "diff", "pct"}
FUNCTIONS = DATA_FUNCTIONS | {"cite", "lit"}

# Allowed bare numbers: years 1900–2099 (also "1980s"), and ordinals ("5ª", "1º", "3rd").
# Known gaps (ADR 0007): spelled-out numbers and quantities between 1900 and 2099.
_ALLOWED = re.compile(r"^(?:(?:19|20)\d{2}s?|\d+(?:º|ª|st|nd|rd|th))$")
# A number token runs to the end of the word, so "5thousand" is not an ordinal. Digits
# glued to a word, or to a word and a hyphen ("G20", "COVID-19"), are names; a hyphen
# after a space or digit is a minus sign or a range, so "-5" and "10-20" are checked.
_NUMBER = re.compile(r"(?<!\w)(?<![^\W\d_]-)\d[\d.,]*\w*")
# Link targets are not prose. Inline code is: numbers there are still checked.
_LINK_TARGET = re.compile(r"\]\([^)\n]*\)")
# Markdown ordered-list markers ("1. item") are structure, not quantities.
_LIST_MARKER = re.compile(r"^\s*\d+\.\s", re.M)

UNIT_DECIMALS = {
    "index_0_1": 3,
    "index_0_100": 1,
    "percent": 1,
    "usd_2015": 0,
    "years": 1,
    "per_1000_live_births": 1,
    "wgi_estimate": 2,
}
MINUS = "−"


class ContentError(Exception):
    pass


@dataclass(frozen=True)
class Placeholder:
    function: str
    args: tuple

    @property
    def source(self) -> str:
        return f"{self.function}{self.args!r}"


def placeholders(text: str) -> list[Placeholder]:
    out = []
    for m in PLACEHOLDER.finditer(text):
        name, raw = m.group(1), m.group(2)
        if name not in FUNCTIONS:
            raise ContentError(f"unknown placeholder function '{name}' in {m.group(0)}")
        try:
            args = ast.literal_eval(f"({raw},)") if raw.strip() else ()
        except (ValueError, SyntaxError) as e:
            raise ContentError(f"malformed placeholder {m.group(0)}: {e}") from e
        out.append(Placeholder(name, args))
    return out


def bare_numbers(text: str) -> list[str]:
    """Numbers written directly in prose that are not years or ordinals, and leftover
    braces from malformed placeholders."""
    prose = _LIST_MARKER.sub(" ", _LINK_TARGET.sub(" ", PLACEHOLDER.sub(" ", text)))
    found = []
    for line_no, line in enumerate(prose.splitlines(), start=1):
        if "{{" in line or "}}" in line:
            found.append(f"line {line_no}: malformed placeholder")
        for m in _NUMBER.finditer(line):
            token = m.group(0).rstrip(".,")
            # Year ranges such as "1995–2012" split into allowed years on the dash.
            if not _ALLOWED.match(token):
                found.append(f"line {line_no}: '{token}'")
    return found


def data_keys(text: str) -> list[tuple]:
    """Data placeholders in order, used to check both translations cite the same data."""
    return [(p.function, p.args) for p in placeholders(text) if p.function in DATA_FUNCTIONS]


@dataclass(frozen=True)
class Cited:
    """A number shown on the site, with where it comes from."""

    ref: int
    text: str
    function: str
    args: tuple
    indicator_id: str | None = None
    source_id: str | None = None
    source_version: str | None = None
    retrieved_at: str | None = None
    doi: str | None = None
    note: str | None = None


def format_number(value: float, decimals: int, lang: str, signed: bool = False) -> str:
    text = f"{abs(value):,.{decimals}f}"
    if lang == "pt":
        text = text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    if value < 0 and round(abs(value), decimals) != 0:
        text = MINUS + text
    elif signed and round(value, decimals) != 0:
        text = "+" + text
    return text


class Resolver:
    """Resolves placeholders against the processed observations for one language."""

    def __init__(
        self,
        observations: pd.DataFrame,
        indicators: dict[str, Indicator],
        dois: Iterable[str],
        lang: str,
    ):
        self._obs = observations.set_index(["indicator_id", "geo_code", "year"])
        self._indicators = indicators
        self._dois = {d.lower() for d in dois}
        self.lang = lang

    def _value(self, ind_id: str, geo: str, year: int) -> pd.Series:
        try:
            return self._obs.loc[(ind_id, geo, year)]
        except KeyError:
            raise ContentError(f"no observation for {ind_id} {geo} {year}") from None

    def _data(self, p: Placeholder, ref: int) -> Cited:
        expected = 3 if p.function == "v" else 4
        if len(p.args) != expected:
            raise ContentError(f"{p.source}: expected {expected} arguments")
        ind_id, geo, *years = p.args
        if not (isinstance(ind_id, str) and isinstance(geo, str)) or not all(
            isinstance(y, int) for y in years
        ):
            raise ContentError(f"{p.source}: expected (indicator, geography, year...)")
        if ind_id not in self._indicators:
            raise ContentError(f"{p.source}: indicator '{ind_id}' is not in the catalog")
        decimals = UNIT_DECIMALS.get(self._indicators[ind_id].unit, 2)
        rows = [self._value(ind_id, geo, y) for y in years]
        if p.function == "v":
            (r,) = rows
            text = format_number(r["value"], decimals, self.lang)
        elif p.function == "diff":
            text = format_number(rows[1]["value"] - rows[0]["value"], decimals, self.lang, True)
        else:
            if rows[0]["value"] == 0:
                raise ContentError(f"{p.source}: percent change from a zero base")
            change = (rows[1]["value"] / rows[0]["value"] - 1) * 100
            text = format_number(change, 1, self.lang, signed=True) + "%"
        last = rows[-1]
        return Cited(
            ref,
            text,
            p.function,
            p.args,
            indicator_id=ind_id,
            source_id=last["source_id"],
            source_version=last["source_version"],
            retrieved_at=last["retrieved_at"],
        )

    def resolve(self, p: Placeholder, ref: int) -> Cited:
        if p.function in DATA_FUNCTIONS:
            return self._data(p, ref)
        if p.function == "cite":
            if len(p.args) != 3:
                raise ContentError(f"{p.source}: expected cite(text, doi, location)")
            text, doi, location = p.args
            if not all(isinstance(a, str) for a in p.args):
                raise ContentError(f"{p.source}: cite arguments must be strings")
            if doi.lower() not in self._dois:
                raise ContentError(f"{p.source}: DOI {doi} is not among this text's references")
            return Cited(ref, text, "cite", p.args, doi=doi, note=location)
        if len(p.args) != 2 or not all(isinstance(a, str) for a in p.args) or not p.args[1].strip():
            raise ContentError(f"{p.source}: expected lit(text, reason) with a reason")
        return Cited(ref, p.args[0], "lit", p.args, note=p.args[1])

    def render(self, text: str, start: int = 1) -> tuple[str, list[Cited]]:
        """Replace placeholders with linked numbers; return the text and what was cited.

        Everything outside placeholders is HTML-escaped first, so contributed text cannot
        inject markup into the site; Markdown syntax still works."""
        cited: list[Cited] = []
        out: list[str] = []
        last = 0
        for m, p in zip(PLACEHOLDER.finditer(text), placeholders(text), strict=True):
            out.append(html.escape(text[last : m.start()], quote=False))
            c = self.resolve(p, start + len(cited))
            cited.append(c)
            out.append(
                f'<a class="dado" href="#dado-{c.ref}" id="ref-{c.ref}">{html.escape(c.text)}</a>'
            )
            last = m.end()
        out.append(html.escape(text[last:], quote=False))
        return "".join(out), cited
