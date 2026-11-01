"""Câmara and Senado vote connectors, against synthetic responses in the sources' format."""

import json
from datetime import UTC, datetime

import httpx
import pytest

from compilador import education, snapshot
from compilador.sources import camara_votes, senado_votes
from compilador.sources.camara_votes import PropRef

FUNDEB = PropRef("PEC", 15, 2015)


def _deputy(i, party, name="Dep"):
    return {"id": i, "nome": f"{name} {i}", "siglaPartido": party, "siglaUf": "SP"}


def _camara_handler(seen=None, fail_first=False):
    state = {"failed": False}

    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(request.url.path)
        path = request.url.path
        if fail_first and not state["failed"]:
            state["failed"] = True
            return httpx.Response(504)
        if path.endswith("/proposicoes"):
            return httpx.Response(
                200,
                json={
                    "dados": [
                        {"id": 7, "siglaTipo": "PEC", "numero": 15, "ano": 2015},
                        {"id": 8, "siglaTipo": "PEC", "numero": 15, "ano": 2016},
                    ]
                },
            )
        if path.endswith("/proposicoes/7/votacoes"):
            return httpx.Response(
                200,
                json={
                    "dados": [
                        {"id": "7-1", "siglaOrgao": "PLEN"},  # nominal
                        {"id": "7-2", "siglaOrgao": "PLEN"},  # symbolic: no ballots
                        {"id": "7-3", "siglaOrgao": "CE"},  # committee: never fetched
                    ],
                    "links": [],
                },
            )
        if path.endswith("/votacoes/7-1/votos"):
            return httpx.Response(
                200,
                json={
                    "dados": [
                        {"tipoVoto": "Sim", "deputado_": _deputy(1, "AAA")},
                        {"tipoVoto": "Sim", "deputado_": _deputy(2, "BBB")},
                        {"tipoVoto": "Não", "deputado_": _deputy(3, "AAA")},
                    ]
                },
            )
        if path.endswith("/votacoes/7-2/votos"):
            return httpx.Response(200, json={"dados": []})
        if path.endswith("/votacoes/7-1/orientacoes"):
            return httpx.Response(
                200,
                json={"dados": [{"siglaPartidoBloco": "AAA", "orientacaoVoto": "Sim"}]},
            )
        if path.endswith("/votacoes/7-1"):
            return httpx.Response(
                200,
                json={
                    "dados": {
                        "data": "2020-07-21",
                        "descricao": "Aprovado em primeiro turno",
                        "descUltimaAberturaVotacao": "Votação em primeiro turno.",
                        "aprovacao": 1,
                    }
                },
            )
        return httpx.Response(404)

    return handler


def _snapshot(tmp_path, files, source_id):
    return snapshot.write(
        source_id,
        files,
        source_version="v",
        license="L",
        raw_dir=tmp_path,
        now=datetime(2026, 11, 1, tzinfo=UTC),
    )


def test_camara_fetch_stores_only_nominal_plenary_votes_and_normalizes(tmp_path, monkeypatch):
    monkeypatch.setattr(camara_votes.time, "sleep", lambda _: None)
    seen: list[str] = []
    client = httpx.Client(transport=httpx.MockTransport(_camara_handler(seen, fail_first=True)))
    files, version = camara_votes.fetch([FUNDEB], client)

    names = {f.name for f in files}
    assert names == {
        "proposicao-PEC-15-2015.json",
        "votacoes-PEC-15-2015.json",
        "votos-7-1.json",
        "votacao-7-1.json",
        "orientacoes-7-1.json",
    }
    assert not any("7-3" in p for p in seen), "committee votes are not fetched"
    assert len(version) == 10

    snap = _snapshot(tmp_path, files, camara_votes.SOURCE_ID)
    votes = camara_votes.normalize(snap, [FUNDEB])["PEC 15/2015"]
    assert len(votes) == 1
    vote = votes[0]
    assert vote["chamber"] == "camara"
    assert vote["approved"] is True
    assert vote["totals"] == {"Sim": 2, "Não": 1}
    assert vote["by_party"] == {"AAA": {"Sim": 1, "Não": 1}, "BBB": {"Sim": 1}}
    assert vote["orientations"] == [{"party_or_bloc": "AAA", "orientation": "Sim"}]
    assert [b["deputy_id"] for b in vote["ballots"]] == [1, 2, 3]
    assert "idProposicao=7" in vote["source_url"]


def test_camara_fetch_rejects_an_ambiguous_or_missing_proposition():
    def handler(request):
        return httpx.Response(200, json={"dados": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(RuntimeError, match=r"PEC 15/2015: expected one proposition"):
        camara_votes.fetch([FUNDEB], client)


def test_normalize_asks_for_a_fetch_when_a_bill_is_missing(tmp_path):
    snap = _snapshot(tmp_path, [camara_votes.RawFile("x.json", "u", b"{}")], "camara_votos")
    with pytest.raises(KeyError, match="run `compilador fetch-votes`"):
        camara_votes.normalize(snap, [FUNDEB])


def test_retries_give_up_after_the_last_attempt(monkeypatch):
    monkeypatch.setattr(camara_votes.time, "sleep", lambda _: None)
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(503)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(httpx.HTTPStatusError):
        camara_votes._get(client, "https://example.org/x")
    assert len(calls) == camara_votes.RETRIES


def _senator(code, party, vote):
    return {
        "codigoParlamentar": code,
        "nomeParlamentar": f"Sen {code}",
        "siglaPartidoParlamentar": party,
        "siglaUFParlamentar": "RO",
        "siglaVotoParlamentar": vote,
    }


def test_senado_normalize_counts_votes_and_skips_votes_without_ballots(tmp_path):
    ref = PropRef("PEC", 26, 2020)
    payload = [
        {
            "codigoSessaoVotacao": 6167,
            "codigoMateria": 143611,
            "dataSessao": "2020-08-25",
            "descricaoVotacao": "1º Turno",
            "resultadoVotacao": "A",
            "votos": [
                _senator(1, "AA", "Sim"),
                _senator(2, "BB", "Sim"),
                _senator(3, "AA", "P-NRV"),
            ],
        },
        {
            "codigoSessaoVotacao": 6168,
            "codigoMateria": 143611,
            "dataSessao": "2020-08-25",
            "descricaoVotacao": "x",
            "resultadoVotacao": "A",
            "votos": [],
        },
    ]
    snap = _snapshot(
        tmp_path,
        [camara_votes.RawFile("votacoes-PEC-26-2020.json", "u", json.dumps(payload).encode())],
        "senado_votos",
    )
    votes = senado_votes.normalize(snap, [ref])["PEC 26/2020"]
    assert [v["id"] for v in votes] == ["SF-6167"]
    assert votes[0]["totals"] == {"Sim": 2, "P-NRV": 1}
    assert votes[0]["chamber"] == "senado" and votes[0]["approved"] is True


def test_vote_files_quote_names_and_render_attaches_votes_to_laws():
    import pandas as pd

    from tests.test_education import _law, _module

    law = _law(camara=[{"type": "PEC", "number": 15, "year": 2015}])
    vote = {
        "id": "7-1",
        "date": "2020-07-21",
        "ballots": [
            {"deputy_id": 1, "name": 'Ana "Doc" Silva', "party": "AA", "state": "SP", "vote": "Sim"}
        ],
    }
    votes = {"camara:PEC 15/2015": [vote]}
    assert education.vote_files(votes) == {
        "7-1.csv": 'deputy_id,name,party,state,vote\n1,"Ana ""Doc"" Silva",AA,SP,Sim\n'
    }
    doc = education.render(
        _module(), [law], pd.DataFrame(columns=["indicator_id", "geo_code", "year", "value"]), votes
    )
    assert [v["id"] for v in doc["laws"][0]["votes"]] == ["7-1"]
    assert "ballots" not in doc["laws"][0]["votes"][0]
    assert doc["submodules"][0]["votes"][0]["designation"] == law.designation


@pytest.mark.parametrize(
    ("description", "main"),
    [
        ("Aprovada, em segundo turno, a Proposta de Emenda à Constituição nº 15, de 2015", True),
        ("Aprovado o Substitutivo do Senado Federal ao Projeto de Lei nº 4.372", True),
        (
            "Aprovada a Medida Provisória nº 746 de 2016, na forma do Projeto de Lei de Conversão",
            True,
        ),
        ("Aprovada a Redação Final.", True),
        (
            "Aprovada a Proposta de Emenda à Constituição nº 241, ressalvados os destaques.",
            True,
        ),
        (
            "Aprovado o Substitutivo do Senado ao Projeto de Lei, ressalvados os destaques",
            True,
        ),
        ("Aprovada a Emenda de Plenário nº 40 ao Projeto de Lei nº 4.372", False),
        ("Aprovado o Requerimento de urgência para o Projeto de Lei nº 5.230", False),
        ("Aprovado o Requerimento. Sim: 264; Não: 41", False),
        ("Aprovada a Emenda n° 6. Sim: 212; não: 205", False),
        ("Rejeitada a Emenda Aglutinativa n° 5.", False),
        ("Mantido o texto. Sim: 399; não: 19", False),
        ("Rejeitado o Recurso 18/2024, contra apreciação terminativa do Projeto de Lei", False),
        ("Inadmitidos, em globo, os destaques simples", False),
    ],
)
def test_is_main_separates_the_decision_from_procedural_votes(description, main):
    assert camara_votes.is_main(description) is main
