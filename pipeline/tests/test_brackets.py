import json

import pandas as pd
import pytest

from compilador import brackets
from compilador.brackets import (
    BracketError,
    Config,
    Share,
    distribution,
    reais_per_usd_ppp,
    share_below,
    translate,
)
from compilador.validate import ValidationError
from tests.helpers import make_indicator

LIMITS = {
    5: 300,
    10: 450,
    20: 700,
    30: 900,
    40: 1100,
    50: 1300,
    60: 1600,
    70: 2000,
    80: 2700,
    90: 4200,
    95: 6500,
    99: 15000,
}
PERCENTILES = (5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99)

config = Config(
    ppp_base_year=2021,
    thresholds_usd_ppp=[250, 500, 1000, 2000],
    percentile_indicators={p: f"ibge_sidra.rdpc_p{p:02d}_pnadc" for p in PERCENTILES},
    ppp_indicator="wdi.pa_nus_prvt_pp",
    cpi_indicator="wdi.fp_cpi_totl",
    income_indicators=["wdi.ny_gdp_pcap_kd"],
)


def _rows(year, limits, ppp, cpi_base, cpi_year):
    rows = [(config.percentile_indicators[p], year, v) for p, v in limits.items()]
    rows += [(config.ppp_indicator, 2021, ppp), (config.cpi_indicator, 2021, cpi_base)]
    if cpi_year is not None:
        rows.append((config.cpi_indicator, year, cpi_year))
    return rows


def _df(rows):
    return pd.DataFrame(
        [
            {
                "geo_code": "BRA",
                "geo_level": "country",
                "year": y,
                "indicator_id": i,
                "value": v,
                "source_id": "x",
                "source_version": "v1",
                "retrieved_at": "2026-10-26",
            }
            for i, y, v in rows
        ]
    )


@pytest.fixture
def df():
    return _df(_rows(2024, LIMITS, 2.45, 100, 120))


@pytest.fixture
def df_missing_cpi_2025(df):
    return pd.concat([df, _df(_rows(2025, LIMITS, 2.45, 100, None)[:12])], ignore_index=True)


@pytest.fixture
def real_2024_df():
    real = dict(
        zip(
            PERCENTILES,
            (276, 405, 626, 815, 1029, 1328, 1526, 1964, 2607, 4026, 6027, 13316),
            strict=True,
        )
    )
    return _df(_rows(2024, real, 2.44986319541931, 187.117425058295, 223.216054990026))


def test_share_below_interpolates():
    assert share_below(LIMITS, 1200) == Share(45.0, 45.0)


def test_share_below_above_p99_is_a_range():
    assert share_below(LIMITS, 20000) == Share(99, 100)


def test_share_below_under_p5_is_a_range():
    assert share_below(LIMITS, 100) == Share(0, 5)


def test_reais_per_usd_ppp_uses_base_ppp_and_cpi_ratio(df):
    assert reais_per_usd_ppp(df, config, 2024) == pytest.approx(2.94)


def test_reais_per_usd_ppp_missing_input_is_none(df):
    assert reais_per_usd_ppp(df, config, 2030) is None


def test_year_without_cpi_is_skipped(df_missing_cpi_2025):
    assert 2025 not in [d["year"] for d in distribution(df_missing_cpi_2025, config)]
    assert 2024 in [d["year"] for d in distribution(df_missing_cpi_2025, config)]


def test_translate_bottom_40_maps_limit_to_bracket(df):
    t = translate(df, config, 40, "bottom", 2024)
    assert t["bracket"] == "ate_500" and t["limit_usd_ppp"] == pytest.approx(1100 / 2.94)


def test_translate_year_without_data_raises(df):
    with pytest.raises(BracketError, match="2011"):
        translate(df, config, 40, "bottom", 2011)


def test_translate_unknown_cut_raises(df):
    with pytest.raises(BracketError, match="45"):
        translate(df, config, 45, "bottom", 2024)


def test_translate_top_10_uses_p90(df):
    t = translate(df, config, 90, "top", 2024)
    assert t["limit_brl"] == LIMITS[90]


def test_tied_percentiles_do_not_divide_by_zero():
    assert share_below({**LIMITS, 20: 450}, 450) == Share(10, 20)


def test_real_2024_shares(real_2024_df):
    b = distribution(real_2024_df, config)[-1]["brackets"]
    assert [x["label"] for x in b] == ["ate_250", "ate_500", "ate_1000", "ate_2000", "acima_2000"]
    assert [round(x["low"], 1) for x in b] == [25.5, 31.2, 25.5, 12.3, 5.5]
    assert all(x["low"] == x["high"] for x in b)


def _write(tmp_path, **over):
    data = {
        "ppp_base_year": 2021,
        "thresholds_usd_ppp": [250, 500, 1000, 2000],
        "percentile_indicators": {5: "wdi.p5", 10: "wdi.p10"},
        "ppp_indicator": "wdi.ppp",
        "cpi_indicator": "wdi.cpi",
        "income_indicators": ["wdi.gini"],
    } | over
    path = tmp_path / "f.yaml"
    path.write_text(json.dumps(data))
    return path


def _catalog(*ids):
    return {i: make_indicator(id=i) for i in ids}


def test_load_checks_catalog_ids(tmp_path):
    path = _write(tmp_path)
    ok = _catalog("wdi.p5", "wdi.p10", "wdi.ppp", "wdi.cpi", "wdi.gini")
    assert brackets.load(path, ok).ppp_base_year == 2021
    assert brackets.load(path).thresholds_usd_ppp == [250, 500, 1000, 2000]
    with pytest.raises(ValidationError, match="wdi.gini"):
        brackets.load(path, _catalog("wdi.p5", "wdi.p10", "wdi.ppp", "wdi.cpi"))


def test_load_rejects_unsorted_thresholds(tmp_path):
    with pytest.raises(ValueError):
        brackets.load(_write(tmp_path, thresholds_usd_ppp=[500, 250]))


def test_real_data_file_loads():
    assert brackets.load().thresholds_usd_ppp == [250, 500, 1000, 2000]
