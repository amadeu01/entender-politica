import pytest
from pydantic import ValidationError

from compilador import catalog
from tests.helpers import make_indicator


def test_repository_catalog_loads():
    indicators = catalog.load()
    assert "wdi.si_pov_gini" in indicators
    assert all(i.references for i in indicators.values())


def test_reference_requires_doi_or_url():
    with pytest.raises(ValidationError, match="doi or url"):
        make_indicator(references=[{"citation": "Someone (2000)"}])


def test_malformed_doi_is_rejected():
    with pytest.raises(ValidationError):
        make_indicator(references=[{"citation": "x", "doi": "doi.org/10.1/x"}])


def test_id_must_be_prefixed_by_source():
    with pytest.raises(ValidationError, match="must start with source"):
        make_indicator(id="ibge.gini")


def test_indicator_needs_at_least_one_criticism():
    with pytest.raises(ValidationError):
        make_indicator(criticisms=[])


def test_file_name_must_match_id(tmp_path, gini):
    (tmp_path / "wrong.yaml").write_text(gini.model_dump_json())
    with pytest.raises(ValueError, match="file name"):
        catalog.load(tmp_path)
