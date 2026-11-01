"""Command line: `compilador fetch [source ...]` and `compilador build`."""

import argparse
import sys

import httpx

from compilador import build, catalog, dois, education, geography, snapshot
from compilador.sources import SOURCES, camara_votes, senado_votes
from compilador.validate import ValidationError

USER_AGENT = "entender-politica/0.1 (+https://github.com/amadeu01/entender-politica)"


def fetch(source_ids: list[str]) -> None:
    indicators = catalog.load()
    geos = geography.load()
    with httpx.Client(timeout=60, headers={"User-Agent": USER_AGENT}) as client:
        for source_id in source_ids:
            wanted = catalog.for_source(indicators, source_id)
            if not wanted:
                print(f"{source_id}: no indicators in catalog, skipped")
                continue
            files, version = SOURCES[source_id].fetch(wanted, geos, client)
            snap = snapshot.write(
                source_id, files, source_version=version, license=SOURCES[source_id].license
            )
            print(f"{source_id}: {len(files)} files, version {version} -> {snap.path}")


def fetch_votes() -> None:
    laws = education.load_laws()
    jobs = (
        (camara_votes, education.camara_refs(laws)),
        (senado_votes, education.senado_refs(laws)),
    )
    with httpx.Client(timeout=60, headers={"User-Agent": USER_AGENT}) as client:
        for module, refs in jobs:
            if not refs:
                print(f"{module.SOURCE_ID}: no bills listed in education/normas, skipped")
                continue
            files, version = module.fetch(refs, client)
            snap = snapshot.write(
                module.SOURCE_ID, files, source_version=version, license=module.LICENSE
            )
            print(f"{module.SOURCE_ID}: {len(files)} files, version {version} -> {snap.path}")


def verify_dois() -> None:
    with httpx.Client(timeout=60, headers={"User-Agent": USER_AGENT}) as client:
        added = dois.verify(build.all_dois(build.Paths()), client)
    print(f"{len(added)} DOIs verified and added: {added}" if added else "all DOIs verified")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="compilador")
    sub = parser.add_subparsers(dest="command", required=True)
    p_fetch = sub.add_parser("fetch", help="download raw snapshots (network)")
    p_fetch.add_argument("sources", nargs="*", choices=list(SOURCES))
    sub.add_parser(
        "fetch-votes", help="download Câmara and Senado roll calls for education bills (network)"
    )
    sub.add_parser("build", help="raw snapshots -> processed data and site artifacts (offline)")
    sub.add_parser("verify-dois", help="look up new DOIs on Crossref (network)")
    args = parser.parse_args(argv)

    if args.command == "fetch":
        fetch(args.sources or list(SOURCES))
        return 0
    if args.command == "fetch-votes":
        fetch_votes()
        return 0
    if args.command == "verify-dois":
        verify_dois()
        return 0

    try:
        result = build.build()
    except ValidationError as e:
        print("validation failed:", *e.errors, sep="\n  ", file=sys.stderr)
        return 1
    print(
        f"{len(result.observations)} observations, {len(result.report.warnings)} warnings "
        f"for review in {build.PROCESSED_DIR / 'validation.json'}"
    )
    print("data changed" if result.changes else "no data changes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
