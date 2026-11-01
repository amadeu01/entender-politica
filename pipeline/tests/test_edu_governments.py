import datetime as dt

import pandas as pd
import pytest
from pydantic import ValidationError

from compilador import edu_governments as eg
from compilador import education, governments
from compilador.education import Module
from compilador.schema import COLUMNS
from tests.helpers import make_indicator

T = {"pt": "t", "en": "t"}
URL = "https://www.planalto.gov.br/x"
IND = "wdi.se_sec_enrr"


def _module():
    sub = {"id": "ensino-medio", "name": T, "summary": T}
    return Module.model_validate({"submodules": [sub]})


def _law():
    return education.Law.model_validate(
        {
            "slug": "lei-x",
            "designation": "Lei 1/2012",
            "kind": "law",
            "year": 2012,
            "title": T,
            "summary": T,
            "submodules": ["ensino-medio"],
            "events": [{"year": 2012, "type": "enacted", "description": T}],
        }
    )


def _started(**over):
    base = {"title": T, "year": 2012, "submodules": ["ensino-medio"], "description": T}
    return base | {"source": URL} | over


def _cut(**over):
    base = {"kind": "withheld", "title": T, "year": 2014, "submodules": ["ensino-medio"]}
    return base | {"description": T, "source": URL} | over


def _doc(**over):
    base = {
        "period": "dilma-1",
        "summary": T,
        "context": T,
        "started": [_started()],
        "indicators": [IND],
        "limitations": [T],
        "references": [{"citation": "c", "url": URL}],
    }
    return eg.GovernmentEducation.model_validate(base | over)


def _inds():
    return {IND: make_indicator(id=IND, source_code="X", unit="percent")}


def _check(doc, **kw):
    govs = governments.load()
    return eg.check([doc], govs, _module(), [_law()], kw.get("indicators", _inds()), {})


def _df(rows):
    return pd.DataFrame(rows, columns=["indicator_id", "geo_code", "year", "value"]).reindex(
        columns=COLUMNS
    )


def test_a_period_needs_a_start_or_a_cut():
    with pytest.raises(ValidationError, match="at least one start or one cut"):
        _doc(started=[], cuts=[])
    assert _doc(started=[], cuts=[_cut()]).cuts


def test_dates_must_fall_in_the_stated_year():
    with pytest.raises(ValidationError, match="not in year"):
        eg.Started.model_validate(_started(date=dt.date(2013, 1, 1)))


def test_check_accepts_a_consistent_record():
    assert _check(_doc(cuts=[_cut()])) == []


def test_check_flags_unknown_period_indicator_submodule_and_norm():
    doc = _doc(
        period="dilma-1",
        includes=["nobody"],
        indicators=["nope.x"],
        started=[_started(submodules=["ghost"], norm="lei-y")],
    )
    errors = "\n".join(_check(doc))
    assert "unknown period 'nobody'" in errors
    assert "unknown indicator 'nope.x'" in errors
    assert "unknown sub-module 'ghost'" in errors
    assert "norm 'lei-y'" in errors


def test_norm_instrument_must_match_the_normas_record():
    bad = _doc(started=[_started(norm="lei-x", instrument="Lei 2/2012")])
    assert "instrument differs" in "\n".join(_check(bad))
    ok = _doc(started=[_started(norm="lei-x", instrument="Lei 1/2012")])
    assert _check(ok) == []


def test_check_rejects_typed_numbers_cite_and_mismatched_data():
    typed = _doc(summary={"pt": "subiu 12 pontos", "en": "rose by 12 points"})
    assert "'12'" in "\n".join(_check(typed))
    cite = '{{ cite("1%", "10.1/x", "abstract") }}'
    assert "needs a verified DOI" in "\n".join(_check(_doc(summary={"pt": cite, "en": cite})))
    v = '{{ v("wdi.se_sec_enrr", "BRA", 2012) }}'
    mismatch = _doc(summary={"pt": v, "en": "no number"})
    assert "different data" in "\n".join(_check(mismatch))


def test_a_period_cannot_be_described_twice():
    govs = governments.load()
    a, b = _doc(), _doc(includes=["dilma-1"])
    errors = eg.check([a, b], govs, _module(), [_law()], _inds(), {})
    assert any("described twice" in e for e in errors)


def test_references_need_a_url_and_a_verified_doi():
    doc = _doc(references=[{"citation": "c", "doi": "10.1000/x", "url": URL}])
    assert "not verified" in "\n".join(_check(doc))


def test_window_attributes_years_by_july_first():
    govs = governments.load()
    assert eg.window(govs, ["dilma-1"], 2030) == [2011, 2012, 2013, 2014]
    # Dilma's second term ends in May 2016: July 2016 belongs to Temer's interim period.
    assert eg.window(govs, ["dilma-2"], 2030) == [2015]
    assert eg.window(govs, ["temer-interino", "temer"], 2030) == [2016, 2017, 2018]


def test_render_resolves_numbers_and_tabulates_changes():
    govs = governments.load()
    df = _df(
        [(IND, "BRA", y, 50.0 + y - 2010) for y in range(2010, 2019)]
        + [(IND, "LCN", y, 60.0) for y in range(2010, 2019)]
    )
    v = '{{ v("wdi.se_sec_enrr", "BRA", 2014) }}'
    doc = _doc(
        summary={"pt": f"No fim, {v}.", "en": f"At the end, {v}."},
        started=[_started(year=2012)],
        cuts=[_cut(year=2014)],
    )
    out = eg.render(doc, "pt", df, _inds(), govs, [_law()])
    assert out["years"] == [2011, 2014]
    assert out["numbers"][0]["indicator_id"] == IND
    assert "54,0" in out["summary"]
    row = next(c for c in out["changes"] if c["geo_code"] == "BRA" and c["lag"] == 0)
    assert (row["start_year"], row["end_year"]) == (2010, 2014)
    assert row["change"] == pytest.approx(4.0)
    lcn = next(c for c in out["changes"] if c["geo_code"] == "LCN" and c["lag"] == 0)
    assert lcn["change"] == pytest.approx(0.0)
    assert out["started"][0]["values"][IND] == 52.0
    assert out["cuts"][0]["values"][IND] == 55.0


def test_items_must_fall_inside_the_period_years():
    doc = _doc(started=[_started(year=2003)])
    assert "outside the period" in "\n".join(_check(doc))
    assert _check(_doc(started=[_started(year=2014)])) == []
    # Dilma's first term ends on 2014-12-31: the end date is exclusive.
    assert "outside the period" in "\n".join(_check(_doc(started=[_started(year=2015)])))
