import datetime as dt

import pandas as pd
import pytest
import yaml
from pydantic import ValidationError

from compilador import education
from compilador.education import Law, Module
from compilador.schema import COLUMNS
from tests.helpers import make_indicator

T = {"pt": "t", "en": "t"}


def _sub(id_="ensino-medio", **over):
    return {"id": id_, "name": T, "summary": T} | over


def _event(**over):
    return {"year": 2020, "type": "enacted", "description": T} | over


def _law(**over):
    base = {
        "slug": "lei-x",
        "designation": "Lei 1/2020",
        "kind": "law",
        "year": 2020,
        "title": T,
        "summary": T,
        "submodules": ["ensino-medio"],
        "events": [_event()],
    }
    return Law.model_validate(base | over)


def _module(**over):
    return Module.model_validate({"submodules": [_sub()]} | over)


def _df(rows):
    frame = pd.DataFrame(rows, columns=["indicator_id", "geo_code", "year", "value"])
    return frame.reindex(columns=COLUMNS)


def test_law_needs_exactly_one_enacted_event_in_its_year():
    with pytest.raises(ValidationError, match="exactly one 'enacted'"):
        _law(events=[_event(type="proposed")])
    with pytest.raises(ValidationError, match="differs from law year"):
        _law(events=[_event(year=2019)])


def test_vote_events_need_a_chamber_and_only_votes_have_a_form():
    with pytest.raises(ValidationError, match="needs a chamber"):
        _law(events=[_event(), _event(type="plenary_vote", year=2019)])
    with pytest.raises(ValidationError, match="only vote events have a form"):
        _law(events=[_event(form="nominal")])
    ok = _law(
        events=[_event(), _event(type="plenary_vote", year=2019, chamber="senado", form="nominal")]
    )
    assert ok.events[1].chamber == education.Chamber.SENADO


def test_amendments_must_name_the_amending_norm():
    with pytest.raises(ValidationError, match="must name the norm"):
        _law(events=[_event(), _event(type="amended", year=2021)])


def test_event_date_must_fall_in_event_year():
    with pytest.raises(ValidationError, match="not in year"):
        _law(events=[_event(date="2019-05-01")])


def test_check_reports_unknown_references_and_duplicates():
    module = _module(overview_indicators=["wdi.nope"])
    laws = [_law(submodules=["missing"]), _law(slug="lei-y")]
    errors = education.check(module, laws, {})
    assert "unknown indicator in education module: wdi.nope" in errors
    assert "lei-x: unknown sub-module 'missing'" in errors
    assert "duplicate designation: Lei 1/2020" in errors


def test_check_rejects_hand_typed_numbers_in_prose_but_not_years():
    bad = _law(
        summary={"pt": "Eleva o piso em 12% ao ano.", "en": "Raises the floor by 12% a year."}
    )
    errors = education.check(_module(), [bad], {})
    assert any("hand-typed numbers" in e and "lei-x summary (pt)" in e for e in errors)
    fine = _law(summary={"pt": "Reforma de 2017.", "en": "2017 reform."})
    assert education.check(_module(), [fine], {}) == []


def test_render_lays_system_wide_values_beside_each_event():
    gini = make_indicator()
    module = _module(overview_indicators=[gini.id])
    laws = [
        _law(
            events=[
                _event(),
                _event(type="amended", year=2023, by="Lei 2/2023"),
            ]
        ),
        _law(slug="lei-2023", designation="Lei 2/2023", year=2023, events=[_event(year=2023)]),
    ]
    df = _df([[gini.id, "BRA", 2020, 51.0], [gini.id, "ARG", 2023, 40.0]])
    doc = education.render(module, laws, df)

    sub = doc["submodules"][0]
    assert sub["laws"] == ["lei-x", "lei-2023"]
    values = {(m["designation"], m["year"]): m["values"][gini.id] for m in sub["events"]}
    # Brazil only: the 2023 value exists for Argentina, not for Brazil.
    assert values == {
        ("Lei 1/2020", 2020): 51.0,
        ("Lei 1/2020", 2023): None,
        ("Lei 2/2023", 2023): None,
    }
    amended = [m for m in sub["events"] if m["type"] == "amended"][0]
    assert amended["by_slug"] == "lei-2023"
    assert [law["designation"] for law in doc["laws"]] == ["Lei 1/2020", "Lei 2/2023"]


def test_load_module_is_optional_and_laws_must_match_file_names(tmp_path):
    assert education.load_module(tmp_path) is None
    (tmp_path / "normas").mkdir()
    (tmp_path / "normas" / "other.yaml").write_text(yaml.safe_dump(_law().model_dump(mode="json")))
    with pytest.raises(ValueError, match="file name must be 'lei-x.yaml'"):
        education.load_laws(tmp_path)


def test_repository_content_is_valid():
    """The committed education content passes its own checks against the real catalog."""
    from compilador import catalog

    module = education.load_module()
    laws = education.load_laws()
    assert module is not None and laws
    assert education.check(module, laws, catalog.load()) == []
    assert all(isinstance(law.verified, (dt.date, type(None))) for law in laws)
