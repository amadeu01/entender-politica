import pandas as pd
import pytest

from compilador.schema import tidy
from compilador.validate import ValidationError, validate


def obs(values: dict[int, float], indicator="wdi.si_pov_gini", geo="BRA") -> pd.DataFrame:
    return pd.DataFrame(
        {
            "geo_code": geo,
            "geo_level": "country",
            "year": list(values),
            "indicator_id": indicator,
            "value": list(values.values()),
            "lower": None,
            "upper": None,
            "unit": "index_0_100",
            "source_id": "wdi",
            "source_version": "v",
            "retrieved_at": "t",
            "license": "CC-BY-4.0",
            "series_break": False,
        }
    )


def test_value_outside_catalog_bounds_is_an_error(gini):
    with pytest.raises(ValidationError, match="> max 100"):
        validate(tidy(obs({2000: 101.0})), {gini.id: gini})


def test_indicator_missing_from_catalog_is_an_error(gini):
    with pytest.raises(ValidationError, match="missing from catalog"):
        validate(tidy(obs({2000: 50.0}, indicator="wdi.unknown")), {gini.id: gini})


def test_coverage_lists_missing_years(gini):
    report = validate(tidy(obs({1990: 60.0, 1992: 59.0, 1993: 58.0})), {gini.id: gini})
    assert report.coverage == [
        {
            "indicator_id": "wdi.si_pov_gini",
            "geo_code": "BRA",
            "first_year": 1990,
            "last_year": 1993,
            "observations": 3,
            "missing_years": [1991],
        }
    ]


def test_atypical_jump_is_a_warning_not_an_error(gini):
    values = {1990 + i: 60.0 - 0.1 * i + (0.02 if i % 2 else 0) for i in range(12)}
    values[2001] = 40.0
    report = validate(tidy(obs(values)), {gini.id: gini})
    assert any("2001" in w and "atypical" in w for w in report.warnings)


def test_schema_rejects_duplicate_keys():
    df = pd.concat([obs({2000: 50.0}), obs({2000: 51.0})])
    with pytest.raises(Exception, match="duplicate|unique"):
        tidy(df)


def test_schema_rejects_value_outside_interval():
    df = obs({2000: 50.0})
    df["lower"], df["upper"] = 51.0, 52.0
    with pytest.raises(Exception, match="lower <= value <= upper"):
        tidy(df)


def test_indicator_without_data_for_a_geography_is_a_warning(gini):
    from compilador import geography

    geos = {g: v for g, v in geography.load().items() if g in ("BRA", "MEX")}
    report = validate(tidy(obs({2000: 50.0})), {gini.id: gini}, geos)
    assert report.warnings == ["wdi.si_pov_gini MEX: no observations"]
