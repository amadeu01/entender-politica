"""Câmara dos Deputados open data: plenary roll calls of the bills behind each law.

Not an indicator source: it produces vote records, not observations, so it has its own
snapshot (`camara_votos`) and its own CLI command (`compilador fetch-votes`). For every
bill a law lists in `camara`, the connector resolves the proposition, lists its votes
and stores, for each plenary vote, the vote detail, every deputy's vote and the party
and bench orientations. Votes without per-deputy records (symbolic votes) are kept in
not stored.

https://dadosabertos.camara.leg.br/swagger/api.html
"""

import json
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx

from compilador.snapshot import RawFile, Snapshot

SOURCE_ID = "camara_votos"
# The terms page could not be read automatically (ADR 0006/0012): verification pending.
LICENSE = "LicenseRef-Camara-open-data"
API = "https://dadosabertos.camara.leg.br/api/v2"
PLENARY = "PLEN"
HUMAN_URL = "https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={id}"


@dataclass(frozen=True)
class PropRef:
    type: str
    number: int
    year: int

    @property
    def key(self) -> str:
        return f"{self.type}-{self.number}-{self.year}"

    @property
    def label(self) -> str:
        return f"{self.type} {self.number}/{self.year}"


RETRIES = 5
RETRY_STATUS = {429, 500, 502, 503, 504}


def _get(client: httpx.Client, url: str) -> tuple[str, bytes]:
    """GET with a few retries: the API answers 5xx now and then under load."""
    for attempt in range(RETRIES):
        last = attempt == RETRIES - 1
        try:
            resp = client.get(url, headers={"Accept": "application/json"})
        except httpx.TransportError:
            if last:
                raise
        else:
            if resp.status_code not in RETRY_STATUS or last:
                resp.raise_for_status()
                return url, resp.content
        time.sleep(2**attempt)
    raise AssertionError("unreachable")


def _pages(client: httpx.Client, url: str) -> tuple[list[dict], bytes]:
    """All records of a paginated listing, and the first page's raw bytes."""
    first = None
    records: list[dict] = []
    while url:
        _, content = _get(client, url)
        first = first or content
        page = json.loads(content)
        records += page["dados"]
        url = next((link["href"] for link in page.get("links", []) if link["rel"] == "next"), "")
    return records, first or b""


def fetch(refs: list[PropRef], client: httpx.Client) -> tuple[list[RawFile], str]:
    files: dict[str, RawFile] = {}

    def keep(name: str, url: str, content: bytes) -> None:
        files.setdefault(name, RawFile(name, url, content))

    for ref in refs:
        query = urlencode({"siglaTipo": ref.type, "numero": ref.number, "ano": ref.year})
        url, content = _get(client, f"{API}/proposicoes?{query}")
        found = [
            p
            for p in json.loads(content)["dados"]
            if (p["siglaTipo"], p["numero"], p["ano"]) == (ref.type, ref.number, ref.year)
        ]
        if len(found) != 1:
            raise RuntimeError(f"{ref.label}: expected one proposition, found {len(found)}")
        prop_id = found[0]["id"]
        keep(f"proposicao-{ref.key}.json", url, content)

        list_url = f"{API}/proposicoes/{prop_id}/votacoes"
        votes, first = _pages(client, list_url)
        keep(f"votacoes-{ref.key}.json", list_url, json.dumps({"dados": votes}).encode())
        for vote in votes:
            if vote["siglaOrgao"] != PLENARY:
                continue
            vid = vote["id"]
            # Symbolic votes have no per-deputy record: keep nothing for them.
            votos_url, votos = _get(client, f"{API}/votacoes/{vid}/votos")
            if not json.loads(votos)["dados"]:
                continue
            keep(f"votos-{vid}.json", votos_url, votos)
            for kind in ("", "/orientacoes"):
                u, c = _get(client, f"{API}/votacoes/{vid}{kind}")
                keep(f"{kind.strip('/') or 'votacao'}-{vid}.json", u, c)
    return list(files.values()), datetime.now(UTC).strftime("%Y-%m-%d")


def _json(snapshot: Snapshot, name: str) -> dict:
    return json.loads(snapshot.read(name))


def normalize(snapshot: Snapshot, refs: list[PropRef]) -> dict[str, list[dict]]:
    """Nominal plenary votes per bill label (`PEC 15/2015`), oldest first."""
    out: dict[str, list[dict]] = {}
    for ref in refs:
        lookup = f"proposicao-{ref.key}.json"
        if lookup not in snapshot.files:
            raise KeyError(
                f"{ref.label} is not in the {SOURCE_ID} snapshot: run `compilador fetch-votes`"
            )
        prop_id = _json(snapshot, lookup)["dados"][0]["id"]
        votes = []
        for item in _json(snapshot, f"votacoes-{ref.key}.json")["dados"]:
            vid = item["id"]
            if f"votos-{vid}.json" not in snapshot.files:
                continue
            ballots = _json(snapshot, f"votos-{vid}.json")["dados"]
            if not ballots:
                continue
            detail = _json(snapshot, f"votacao-{vid}.json")["dados"]
            orient = _json(snapshot, f"orientacoes-{vid}.json")["dados"]
            by_party: dict[str, Counter] = defaultdict(Counter)
            for b in ballots:
                by_party[b["deputado_"]["siglaPartido"]][b["tipoVoto"]] += 1
            votes.append(
                {
                    "id": vid,
                    "chamber": "camara",
                    "proposition": ref.label,
                    "date": detail["data"],
                    "description": detail["descricao"],
                    "turn": detail.get("descUltimaAberturaVotacao"),
                    "approved": {1: True, 0: False}.get(detail.get("aprovacao")),
                    "totals": dict(Counter(b["tipoVoto"] for b in ballots)),
                    "by_party": {p: dict(c) for p, c in sorted(by_party.items())},
                    "orientations": [
                        {
                            "party_or_bloc": o["siglaPartidoBloco"],
                            "orientation": o["orientacaoVoto"],
                        }
                        for o in orient
                    ],
                    "source_url": HUMAN_URL.format(id=prop_id),
                    "retrieved_at": snapshot.retrieved_at,
                    "license": snapshot.license,
                    "ballots": [
                        {
                            "deputy_id": b["deputado_"]["id"],
                            "name": b["deputado_"]["nome"],
                            "party": b["deputado_"]["siglaPartido"],
                            "state": b["deputado_"]["siglaUf"],
                            "vote": b["tipoVoto"],
                        }
                        for b in ballots
                    ],
                }
            )
        out[ref.label] = sorted(votes, key=lambda v: (v["date"], v["id"]))
    return out
