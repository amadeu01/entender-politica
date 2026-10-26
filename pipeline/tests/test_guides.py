import pandas as pd
import pytest
import yaml
from pydantic import ValidationError as PydanticError

from compilador import analyses, guides
from compilador.guides import Guide
from compilador.validate import ValidationError
from tests.helpers import make_indicator
from tests.test_brackets import LIMITS, _df, _rows, config

DOI_A = "10.1000/study"
DOI_B = "10.1000/policy"
V = '{{ v("wdi.si_pov_gini", "BRA", 2024) }}'
INDICATORS = {
    "wdi.si_pov_gini": make_indicator(),
    "wdi.ny_gdp_pcap_kd": make_indicator(id="wdi.ny_gdp_pcap_kd", source_code="NY.GDP.PCAP.KD"),
}
REGISTRY = {DOI_A: {"bibtex": "@a"}, DOI_B: {"bibtex": "@b"}}


def text(s="texto"):
    return {"pt": s, "en": s}


def base() -> dict:
    return {
        "indicator": "wdi.si_pov_gini",
        "understand": {"pt": f"valor {V}", "en": f"value {V}"},
        "how_to_read": text(),
        "studies": [
            {"text": text(), "method": "descriptive", "references": [DOI_A]},
        ],
        "policies": [
            {
                "name": text("Programa"),
                "country": "BRA",
                "period": {"start": 2003, "end": 2010},
                "result": text(),
                "direction": "null",
                "method": "difference_in_differences",
                "references": [DOI_B],
                "brief": None,
            }
        ],
        "references": [
            {"citation": "A (2020)", "doi": DOI_A},
            {"citation": "B (2021)", "doi": DOI_B},
        ],
    }


def income(group=None, refs=None) -> dict:
    out = {
        "text": text(),
        "study_period": {"start": 2012, "end": 2020},
        "references": refs or [DOI_B],
    }
    if group:
        out["group"] = group
    return out


@pytest.fixture
def df():
    gini = _df([("wdi.si_pov_gini", 2024, 50.0)])
    return pd.concat([_df(_rows(2024, LIMITS, 2.45, 100, 120)), gini], ignore_index=True)


def write(tmp_path, data, name=None):
    (tmp_path / f"{name or data['indicator']}.yaml").write_text(
        yaml.safe_dump(data, allow_unicode=True)
    )
    return guides.load_guides(tmp_path)


def check(gs, slugs=("prog",)):
    return guides.check(gs, INDICATORS, set(slugs))


def render(data, df, lang="pt", cfg=config):
    g = Guide.model_validate(data)
    return guides.render_guide(g, lang, df, INDICATORS, REGISTRY, cfg)


def test_guide_for_unknown_indicator_is_rejected(tmp_path):
    data = base() | {"indicator": "wdi.nope"}
    assert any("not in catalog" in e for e in check(write(tmp_path, data)))


def test_guide_file_name_must_match_indicator(tmp_path):
    with pytest.raises(ValueError, match="wdi.si_pov_gini.yaml"):
        write(tmp_path, base(), name="other")


def test_bare_number_in_guide_text_is_rejected(tmp_path):
    data = base() | {"how_to_read": text("subiu 10 pontos")}
    errors = check(write(tmp_path, data))
    assert any("guides/wdi.si_pov_gini.yaml" in e and "'10'" in e for e in errors)


def test_guide_translations_must_cite_same_data(tmp_path):
    data = base() | {"understand": {"pt": V, "en": V.replace("2024", "2023")}}
    assert any("cite different data" in e for e in check(write(tmp_path, data)))


def test_only_positive_policies_need_contrary_search():
    data = base()
    data["policies"][0]["direction"] = "positive"
    with pytest.raises(PydanticError, match="contrary"):
        Guide.model_validate(data)
    Guide.model_validate(data | {"contrary_evidence_search": text()})


def test_policy_entry_brief_must_exist(tmp_path):
    data = base()
    data["policies"][0]["brief"] = "missing"
    assert any("brief 'missing'" in e for e in check(write(tmp_path, data)))
    data["policies"][0]["brief"] = "prog"
    assert check(write(tmp_path, data)) == []


def test_entry_cites_reference_not_listed_is_rejected(tmp_path):
    data = base()
    data["studies"][0]["references"] = ["10.9999/unknown"]
    assert any("not in references" in e for e in check(write(tmp_path, data)))


def test_by_income_cites_reference_not_listed_is_rejected(tmp_path):
    data = base() | {"by_income": [income(refs=["10.9999/unknown"])]}
    assert any("not in references" in e for e in check(write(tmp_path, data)))


def test_unknown_cut_is_rejected(tmp_path):
    data = base() | {"by_income": [income({"cut": 33, "side": "bottom", "year": 2024})]}
    assert any("cut 33" in e for e in check_with_cfg(write(tmp_path, data)))


def test_purchasing_power_without_income_section_is_rejected(tmp_path):
    data = base() | {"purchasing_power": text()}
    assert any("purchasing_power" in e for e in check_with_cfg(write(tmp_path, data)))
    ok = data | {"indicator": "wdi.ny_gdp_pcap_kd"}
    other = tmp_path / "ok"
    other.mkdir()
    assert not any("purchasing_power" in e for e in check_with_cfg(write(other, ok)))


def check_with_cfg(gs):
    return guides.check(gs, INDICATORS, {"prog"}, config)


def test_group_side_and_year_are_validated():
    bad_side = base() | {"by_income": [income({"cut": 40, "side": "middle", "year": 2024})]}
    with pytest.raises(PydanticError):
        Guide.model_validate(bad_side)
    old = base() | {"by_income": [income({"cut": 40, "side": "bottom", "year": 2011})]}
    with pytest.raises(PydanticError):
        Guide.model_validate(old)


def test_show_income_false_for_non_income_indicator_without_effects(df):
    doc = render(base(), df)
    assert doc["show_income"] is False
    assert doc["by_income"] == []


def test_show_income_true_for_income_indicator(df):
    doc = render(base() | {"indicator": "wdi.ny_gdp_pcap_kd"}, df)
    assert doc["show_income"] is True


def test_by_income_translation_is_computed(df):
    data = base() | {"by_income": [income({"cut": 40, "side": "bottom", "year": 2024})]}
    doc = render(data, df)
    assert doc["show_income"] is True
    tr = doc["by_income"][0]["translation"]
    assert tr["bracket"] == "ate_500"
    assert tr["cut"] == 40


def test_by_income_year_without_data_fails_build(df):
    data = base() | {"by_income": [income({"cut": 40, "side": "bottom", "year": 2020})]}
    with pytest.raises(ValidationError, match="2020"):
        render(data, df)


def test_by_income_group_without_config_fails_clearly(df):
    data = base() | {"by_income": [income({"cut": 40, "side": "bottom", "year": 2024})]}
    with pytest.raises(ValidationError, match="income brackets"):
        render(data, df, cfg=None)


def test_guide_without_groups_renders_without_config(df):
    data = base() | {"by_income": [income()]}
    doc = render(data, df, cfg=None)
    assert doc["show_income"] is True
    assert doc["by_income"][0]["translation"] is None
    assert doc["by_income"][0]["study_period"] == {"start": 2012, "end": 2020}


def test_by_income_without_group_renders_null_translation(df):
    doc = render(base() | {"by_income": [income()]}, df)
    assert doc["by_income"][0]["translation"] is None


def test_top_10_group_translates_with_p90(df):
    data = base() | {"by_income": [income({"cut": 90, "side": "top", "year": 2024})]}
    tr = render(data, df)["by_income"][0]["translation"]
    assert (tr["cut"], tr["side"]) == (90, "top")
    assert tr["limit_brl"] == LIMITS[90]


def test_references_split_by_where_cited(df):
    data = base()
    data["references"].append({"citation": "C (2022)", "doi": "10.1000/uncited"})
    doc = render(data, df)
    assert [r["doi"] for r in doc["references_indicator"]] == [DOI_A]
    assert [r["doi"] for r in doc["references_policies"]] == [DOI_B, "10.1000/uncited"]


def test_reference_cited_by_study_and_policy_goes_to_policies(df):
    data = base()
    data["policies"][0]["references"] = [DOI_A]
    doc = render(data, df)
    assert doc["references_indicator"] == []


def test_render_shape(df):
    doc = render(base(), df, lang="en")
    assert doc["lang"] == "en"
    assert doc["policies"][0]["evidence_level"] == "moderate"
    assert doc["policies"][0]["brief"] is None
    assert doc["studies"][0]["method"] == "descriptive"
    assert "evidence_level" not in doc["studies"][0]
    assert doc["numbers"][0]["indicator_id"] == "wdi.si_pov_gini"


def test_policy_evidence_level_unchanged_after_refactor():
    assert analyses.evidence_level({analyses.Method.RCT}) == "high"
    assert analyses.evidence_level({analyses.Method.SYNTHETIC_CONTROL}) == "moderate"
    assert analyses.evidence_level({analyses.Method.OBSERVATIONAL}) == "low"
    assert analyses.needs_contrary_search([analyses.Direction.POSITIVE])
    assert not analyses.needs_contrary_search([analyses.Direction.MIXED])


def test_repository_guides_pass_checks():
    from compilador import catalog

    gs = guides.load_guides()
    slugs = {p.slug for p in analyses.load_policies()}
    assert guides.check(gs, catalog.load(), slugs) == []
