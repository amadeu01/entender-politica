from datetime import date

import pytest
from pydantic import ValidationError

from compilador import governments


@pytest.fixture(scope="module")
def govs() -> governments.Governments:
    return governments.load()


def test_reference_file_is_valid_and_starts_before_1980(govs):
    assert govs.periods[0].start <= date(1980, 1, 1)
    assert govs.periods[-1].end is None


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(1980, 6, 1), "figueiredo"),
        (date(1985, 3, 15), "sarney-interino"),
        (date(1992, 11, 1), "itamar-interino"),
        (date(1994, 7, 1), "itamar"),
        (date(2016, 6, 1), "temer-interino"),
        (date(2016, 8, 31), "temer"),
        (date(2024, 1, 1), "lula-3"),
    ],
)
def test_at_resolves_period_in_force(govs, day, expected):
    assert govs.at(day).id == expected


def test_at_before_coverage_raises(govs):
    with pytest.raises(LookupError):
        govs.at(date(1970, 1, 1))


def _period(id_, start, end):
    return {
        "id": id_,
        "president": "X",
        "short_name": "X",
        "condition": "titular",
        "term": {"pt": "t", "en": "t"},
        "start": start,
        "end": end,
    }


def test_gap_between_periods_is_rejected():
    with pytest.raises(ValidationError, match="gap or overlap"):
        governments.Governments.model_validate(
            {
                "sources": ["https://example.org"],
                "verified_on": "2026-10-25",
                "periods": [
                    _period("a", "2000-01-01", "2001-01-01"),
                    _period("b", "2001-01-02", None),
                ],
            }
        )


def test_missing_translation_is_rejected():
    bad = _period("a", "2000-01-01", None)
    bad["term"] = {"pt": "t", "en": ""}
    with pytest.raises(ValidationError):
        governments.Governments.model_validate(
            {"sources": ["https://example.org"], "verified_on": "2026-10-25", "periods": [bad]}
        )


@pytest.mark.parametrize(
    ("year", "expected"),
    [(1985, "sarney"), (1992, "collor"), (2016, "temer-interino"), (2003, "lula-1")],
)
def test_for_year_uses_july_first(govs, year, expected):
    assert govs.for_year(year).id == expected


@pytest.mark.parametrize(
    ("year", "changed"),
    [
        (1985, True),
        (1990, True),
        (1992, True),
        (2016, True),
        (2003, False),
        (2010, False),
        (1999, False),
    ],
)
def test_changes_in_year_ignores_regular_inaugurations_and_same_person(govs, year, changed):
    assert govs.changes_in_year(year) is changed


def test_inauguration_on_january_fifth_is_not_mid_year():
    def period(id_, president, start, end):
        return {
            "id": id_,
            "president": president,
            "short_name": president,
            "condition": "titular",
            "term": {"pt": "t", "en": "t"},
            "start": start,
            "end": end,
        }

    govs = governments.Governments.model_validate(
        {
            "sources": ["https://example.org"],
            "verified_on": "2026-10-25",
            "periods": [
                period("a", "A", "2023-01-01", "2027-01-05"),
                period("b", "B", "2027-01-05", None),
            ],
        }
    )
    assert govs.changes_in_year(2027) is False
