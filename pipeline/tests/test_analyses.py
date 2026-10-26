import copy

import pytest
import yaml
from pydantic import ValidationError

from compilador import analyses, catalog, geography
from compilador.analyses import Analysis, Policy

REPO_ANALYSIS = yaml.safe_load(
    (analyses.ANALYSES_DIR / "desigualdade-de-renda" / "analise.yaml").read_text()
)
REPO_POLICY = yaml.safe_load((analyses.POLICIES_DIR / "progresa-oportunidades.yaml").read_text())


def test_repository_content_passes_checks():
    errors = analyses.check(
        analyses.load_analyses(),
        analyses.load_policies(),
        catalog.load(),
        set(geography.load()),
    )
    assert errors == []


def test_causal_claims_need_causal_design():
    data = REPO_ANALYSIS | {"causal_claims": True, "method": "descriptive"}
    with pytest.raises(ValidationError, match="causal design"):
        Analysis.model_validate(data)
    Analysis.model_validate(data | {"method": "difference_in_differences"})


def test_analysis_needs_contrary_evidence():
    with pytest.raises(ValidationError):
        Analysis.model_validate(REPO_ANALYSIS | {"evidence_against": []})


def test_policy_with_only_positive_findings_must_document_contrary_search():
    data = copy.deepcopy(REPO_POLICY)
    for f in data["findings"]:
        f["direction"] = "positive"
    with pytest.raises(ValidationError, match="contrary"):
        Policy.model_validate(data)
    data["contrary_evidence_search"] = {"pt": "busca", "en": "search"}
    Policy.model_validate(data)


def test_evidence_level_follows_strongest_design():
    p = Policy.model_validate(REPO_POLICY)
    assert p.evidence_level == "high"


def _write(tmp_path, pt_body, en_body, data=REPO_ANALYSIS):
    folder = tmp_path / data["slug"]
    folder.mkdir()
    (folder / "analise.yaml").write_text(yaml.safe_dump(data, allow_unicode=True))
    (folder / "texto.pt.md").write_text(pt_body)
    if en_body is not None:
        (folder / "texto.en.md").write_text(en_body)
    return analyses.load_analyses(tmp_path)


def _check(docs):
    return analyses.check(docs, analyses.load_policies(), catalog.load(), set(geography.load()))


def test_missing_translation_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="texto.en.md"):
        _write(tmp_path, "texto", None)


def test_translations_must_cite_the_same_data(tmp_path):
    docs = _write(
        tmp_path,
        '{{ v("wdi.si_pov_gini", "BRA", 2001) }}',
        '{{ v("wdi.si_pov_gini", "BRA", 2002) }}',
    )
    assert any("cite different data" in e for e in _check(docs))


def test_hand_typed_number_in_body_is_rejected(tmp_path):
    docs = _write(tmp_path, "caiu 10 pontos", "fell 10 points")
    errors = _check(docs)
    assert any("texto.pt.md line 1: '10'" in e for e in errors)
    assert any("texto.en.md line 1: '10'" in e for e in errors)


def test_evidence_must_cite_a_listed_reference(tmp_path):
    data = copy.deepcopy(REPO_ANALYSIS)
    data["evidence_for"][0]["references"] = ["10.9999/unknown"]
    docs = _write(tmp_path, "texto", "text", data)
    assert any("not in references" in e for e in _check(docs))
