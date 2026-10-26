import pandas as pd
import pytest

from compilador import governments, periods
from tests.test_validate import obs


@pytest.fixture(scope="module")
def govs():
    return governments.load()


def test_years_follow_july_first_rule(govs):
    by_period = periods.years_by_period(govs, 2014, 2019)
    assert by_period == {
        "dilma-1": [2014],
        "dilma-2": [2015],
        "temer-interino": [2016],
        "temer": [2017, 2018],
        "bolsonaro": [2019],
    }


def test_change_runs_from_year_before_period_with_lag(govs):
    data = pd.concat(
        [obs({2002: 58.1, 2006: 55.0, 2007: 54.0}, indicator=i) for i in periods.TABLE_INDICATORS]
    )
    units = dict.fromkeys(periods.TABLE_INDICATORS, "index_0_100") | {
        "wdi.ny_gdp_pcap_kd": "usd_2015"
    }
    rows = periods.changes(data, govs, units, last_year=2010)
    pick = {
        (r["indicator_id"], r["lag"]): r
        for r in rows
        if r["period_id"] == "lula-1" and r["geo_code"] == "BRA"
    }
    gini0 = pick[("wdi.si_pov_gini", 0)]
    assert (gini0["start_year"], gini0["end_year"]) == (2002, 2006)
    assert gini0["change"] == pytest.approx(55.0 - 58.1)
    gdp0 = pick[("wdi.ny_gdp_pcap_kd", 0)]
    assert gdp0["relative"] is True
    assert gdp0["change"] == pytest.approx((55.0 / 58.1 - 1) * 100)
    assert pick[("wdi.si_pov_gini", 1)]["change"] is None  # no 2003 observation


def test_years_with_two_presidents_are_flagged(govs):
    data = obs({2015: 1.0}, indicator="wdi.si_pov_gini")
    units = dict.fromkeys(periods.TABLE_INDICATORS, "index_0_100")
    rows = periods.changes(data, govs, units, last_year=2016)
    temer = next(r for r in rows if r["period_id"] == "temer-interino")
    assert temer["mixed_years"] == [2016]
