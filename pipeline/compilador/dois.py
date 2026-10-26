"""Verified DOI registry.

`compilador verify-dois` looks up new DOIs on Crossref (network) and stores their
metadata and BibTeX in `data/reference/dois.json`. The offline build then requires every
DOI cited anywhere to be in that file, so a mistyped or invented DOI fails CI.
"""

import json
from pathlib import Path
from urllib.parse import quote

import httpx

from compilador import DATA_DIR

DOIS_FILE = DATA_DIR / "reference" / "dois.json"
CROSSREF = "https://api.crossref.org/works"


def load(path: Path = DOIS_FILE) -> dict[str, dict]:
    return json.loads(path.read_text()) if path.exists() else {}


def missing(dois: set[str], registry: dict[str, dict]) -> list[str]:
    return sorted(d for d in dois if d.lower() not in registry)


def _lookup(doi: str, client: httpx.Client) -> dict:
    url = f"{CROSSREF}/{quote(doi, safe='/:()')}"
    resp = client.get(url)
    if resp.status_code == 404:
        raise LookupError(f"DOI not found on Crossref: {doi}")
    resp.raise_for_status()
    m = resp.json()["message"]
    bibtex = client.get(f"{url}/transform/application/x-bibtex")
    bibtex.raise_for_status()
    return {
        "doi": m["DOI"].lower(),
        "title": (m.get("title") or [""])[0],
        "container": (m.get("container-title") or [""])[0],
        "year": _year(m),
        "authors": [a.get("family", a.get("name", "")) for a in m.get("author", [])],
        "bibtex": bibtex.text.strip(),
    }


def _year(message: dict) -> int | None:
    for key in ("issued", "published-print", "published-online"):
        parts = (message.get(key) or {}).get("date-parts") or [[None]]
        if parts[0] and parts[0][0]:
            return parts[0][0]
    return None


def verify(dois: set[str], client: httpx.Client, path: Path = DOIS_FILE) -> list[str]:
    """Add unverified DOIs to the registry. Returns the DOIs added."""
    registry = load(path)
    added = []
    for doi in missing(dois, registry):
        registry[doi.lower()] = _lookup(doi, client)
        added.append(doi)
    if added:
        text = json.dumps(dict(sorted(registry.items())), indent=1, ensure_ascii=False)
        path.write_text(text + "\n")
    return added
