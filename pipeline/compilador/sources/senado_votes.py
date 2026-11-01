"""Senado Federal open data: plenary roll calls of the bills behind each law.

Like `camara_votes`, not an indicator source: it has its own snapshot (`senado_votos`)
and is run by `compilador fetch-votes`. A bill is named by the Senado's own numbering
(the Câmara's PEC 15/2015 is the Senado's PEC 26/2020), so each law lists its Senado
bill separately in `senado`. One request per bill returns every vote with each senator's
vote inline.

https://legis.senado.leg.br/dadosabertos/docs/
"""

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx

from compilador.snapshot import RawFile, Snapshot
from compilador.sources.camara_votes import PropRef, _get

SOURCE_ID = "senado_votos"
# The terms page could not be read automatically (ADR 0006/0012): verification pending.
LICENSE = "LicenseRef-Senado-open-data"
API = "https://legis.senado.leg.br/dadosabertos"
HUMAN_URL = "https://www25.senado.leg.br/web/atividade/materias/-/materia/{id}"


def fetch(refs: list[PropRef], client: httpx.Client) -> tuple[list[RawFile], str]:
    files = []
    for ref in refs:
        query = urlencode({"sigla": ref.type, "numero": ref.number, "ano": ref.year})
        url, content = _get(client, f"{API}/votacao?{query}")
        files.append(RawFile(f"votacoes-{ref.key}.json", url, content))
    return files, datetime.now(UTC).strftime("%Y-%m-%d")


def normalize(snapshot: Snapshot, refs: list[PropRef]) -> dict[str, list[dict]]:
    """Plenary votes with senator-level records per bill label, oldest first."""
    out: dict[str, list[dict]] = {}
    for ref in refs:
        name = f"votacoes-{ref.key}.json"
        if name not in snapshot.files:
            raise KeyError(
                f"{ref.label} is not in the {SOURCE_ID} snapshot: run `compilador fetch-votes`"
            )
        votes = []
        for item in json.loads(snapshot.read(name)):
            ballots = item.get("votos") or []
            if not ballots:
                continue
            by_party: dict[str, Counter] = defaultdict(Counter)
            for b in ballots:
                by_party[b["siglaPartidoParlamentar"]][b["siglaVotoParlamentar"]] += 1
            votes.append(
                {
                    "id": f"SF-{item['codigoSessaoVotacao']}",
                    "chamber": "senado",
                    "proposition": ref.label,
                    "date": item["dataSessao"],
                    "description": item["descricaoVotacao"],
                    "turn": None,
                    "approved": {"A": True, "R": False}.get(item.get("resultadoVotacao")),
                    "totals": dict(Counter(b["siglaVotoParlamentar"] for b in ballots)),
                    "by_party": {p: dict(c) for p, c in sorted(by_party.items())},
                    "orientations": [],
                    "source_url": HUMAN_URL.format(id=item["codigoMateria"]),
                    "retrieved_at": snapshot.retrieved_at,
                    "license": snapshot.license,
                    "ballots": [
                        {
                            "deputy_id": b["codigoParlamentar"],
                            "name": b["nomeParlamentar"],
                            "party": b["siglaPartidoParlamentar"],
                            "state": b["siglaUFParlamentar"],
                            "vote": b["siglaVotoParlamentar"],
                        }
                        for b in ballots
                    ],
                }
            )
        out[ref.label] = sorted(votes, key=lambda v: (v["date"], v["id"]))
    return out
