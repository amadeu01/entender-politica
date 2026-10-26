"""Source connectors. Each module exposes:

- `SOURCE_ID` and `LICENSE`;
- `fetch(indicators, geos, client) -> (raw files, source version)`: network access;
- `normalize(snapshot, indicators, geos) -> DataFrame` in the common format: offline.
"""

from compilador.sources import wdi

SOURCES = {m.SOURCE_ID: m for m in (wdi,)}
