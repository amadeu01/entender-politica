"""Source connectors. Each source object exposes:

- `source_id` and `license`;
- `fetch(indicators, geos, client) -> (raw files, source version)`: network access;
- `normalize(snapshot, indicators, geos) -> DataFrame` in the common format: offline.
"""

from compilador.sources.sidra import sidra
from compilador.sources.worldbank import wdi, wgi

SOURCES = {s.source_id: s for s in (wdi, wgi, sidra)}
