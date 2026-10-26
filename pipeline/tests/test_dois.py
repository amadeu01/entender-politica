import json

import httpx
import pytest

from compilador import dois


def handler(request: httpx.Request) -> httpx.Response:
    if "10.9999" in request.url.path:
        return httpx.Response(404)
    if request.url.path.endswith("x-bibtex"):
        return httpx.Response(200, text="@article{a, title={T}}\n")
    return httpx.Response(
        200,
        json={
            "message": {
                "DOI": "10.1257/AER.1",
                "title": ["T"],
                "container-title": ["AER"],
                "issued": {"date-parts": [[2022, 12]]},
                "author": [{"family": "Engbom"}, {"name": "Consortium"}],
            }
        },
    )


def test_verify_adds_only_missing_dois_with_bibtex(tmp_path):
    path = tmp_path / "dois.json"
    path.write_text(json.dumps({"10.1/known": {"year": 2000}}))
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        added = dois.verify({"10.1/known", "10.1257/AER.1"}, client, path)
    assert added == ["10.1257/AER.1"]
    registry = dois.load(path)
    assert registry["10.1257/aer.1"]["year"] == 2022
    assert registry["10.1257/aer.1"]["authors"] == ["Engbom", "Consortium"]
    assert registry["10.1257/aer.1"]["bibtex"].startswith("@article")


def test_unknown_doi_fails_verification(tmp_path):
    with (
        httpx.Client(transport=httpx.MockTransport(handler)) as client,
        pytest.raises(LookupError, match="not found"),
    ):
        dois.verify({"10.9999/invented"}, client, tmp_path / "dois.json")


def test_missing_is_case_insensitive():
    assert dois.missing({"10.1/ABC", "10.1/new"}, {"10.1/abc": {}}) == ["10.1/new"]


def test_bibtex_ampersand_is_escaped():
    assert dois._bibtex("@article{a, journal={PS: Political Science &amp; Politics}}") == (
        "@article{a, journal={PS: Political Science \\& Politics}}"
    )
