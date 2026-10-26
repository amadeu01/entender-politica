"""Data changelog: what changed between the previous and the new processed data."""

from dataclasses import dataclass, field

import pandas as pd

from compilador.schema import KEY

# Values closer than this are treated as unchanged (float noise from upstream formatting).
TOLERANCE = 1e-9
# Revisions listed individually in the changelog before summarizing the rest.
MAX_LISTED = 20


@dataclass
class Changes:
    new_series: list[str] = field(default_factory=list)
    removed_series: list[str] = field(default_factory=list)
    added: int = 0
    removed: int = 0
    revised: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(
            self.new_series or self.removed_series or self.added or self.removed or self.revised
        )


def _series(df: pd.DataFrame) -> set[str]:
    return set(df["indicator_id"] + " " + df["geo_code"])


def diff(old: pd.DataFrame, new: pd.DataFrame) -> Changes:
    changes = Changes(
        new_series=sorted(_series(new) - _series(old)),
        removed_series=sorted(_series(old) - _series(new)),
    )
    merged = old[[*KEY, "value"]].merge(
        new[[*KEY, "value"]], on=KEY, how="outer", suffixes=("_old", "_new"), indicator=True
    )
    changes.added = int((merged["_merge"] == "right_only").sum())
    changes.removed = int((merged["_merge"] == "left_only").sum())
    both = merged[merged["_merge"] == "both"]
    revised = both[(both["value_old"] - both["value_new"]).abs() > TOLERANCE]
    changes.revised = [
        f"{r.indicator_id} {r.geo_code} {r.year}: {r.value_old} → {r.value_new}"
        for r in revised.itertuples()
    ]
    return changes


def render(changes: Changes, date: str, versions: dict[str, str]) -> str:
    lines = [f"## {date}", ""]
    lines += [
        f"- Fonte / Source `{s}`: versão / version `{v}`" for s, v in sorted(versions.items())
    ]
    if changes.new_series:
        lines.append(f"- Séries novas / New series: {len(changes.new_series)}")
        lines += [f"  - `{s}`" for s in changes.new_series]
    if changes.removed_series:
        lines.append(f"- Séries removidas / Removed series: {len(changes.removed_series)}")
        lines += [f"  - `{s}`" for s in changes.removed_series]
    lines.append(f"- Observações adicionadas / Observations added: {changes.added}")
    lines.append(f"- Observações removidas / Observations removed: {changes.removed}")
    lines.append(
        f"- Valores revisados pela fonte / Values revised upstream: {len(changes.revised)}"
    )
    lines += [f"  - {r}" for r in changes.revised[:MAX_LISTED]]
    if len(changes.revised) > MAX_LISTED:
        lines.append(f"  - … +{len(changes.revised) - MAX_LISTED}")
    return "\n".join(lines) + "\n"
