"""Raw data snapshots: downloaded files plus a manifest with provenance (ADR 0002)."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from compilador import DATA_DIR

RAW_DIR = DATA_DIR / "raw"
MANIFEST = "manifest.json"


@dataclass(frozen=True)
class RawFile:
    name: str
    url: str
    content: bytes


@dataclass(frozen=True)
class Snapshot:
    """A verified raw snapshot on disk."""

    source_id: str
    path: Path
    retrieved_at: str
    source_version: str
    license: str
    files: dict[str, str]  # name -> url

    def read(self, name: str) -> bytes:
        return (self.path / name).read_bytes()


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write(
    source_id: str,
    files: list[RawFile],
    *,
    source_version: str,
    license: str,
    raw_dir: Path = RAW_DIR,
    now: datetime | None = None,
) -> Snapshot:
    """Store `files` under raw/<source>/<UTC date>/ and write their manifest."""
    now = now or datetime.now(UTC)
    path = raw_dir / source_id / now.strftime("%Y-%m-%d")
    path.mkdir(parents=True, exist_ok=True)
    for f in files:
        (path / f.name).write_bytes(f.content)
    manifest = {
        "source_id": source_id,
        "retrieved_at": now.isoformat(timespec="seconds"),
        "source_version": source_version,
        "license": license,
        "files": [
            {"name": f.name, "url": f.url, "sha256": _sha256(f.content), "bytes": len(f.content)}
            for f in sorted(files, key=lambda f: f.name)
        ],
    }
    (path / MANIFEST).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return load(path)


def load(path: Path) -> Snapshot:
    """Load a snapshot and verify every file against its recorded hash."""
    manifest = json.loads((path / MANIFEST).read_text())
    for f in manifest["files"]:
        actual = _sha256((path / f["name"]).read_bytes())
        if actual != f["sha256"]:
            raise ValueError(f"{path / f['name']}: sha256 {actual} does not match manifest")
    return Snapshot(
        source_id=manifest["source_id"],
        path=path,
        retrieved_at=manifest["retrieved_at"],
        source_version=manifest["source_version"],
        license=manifest["license"],
        files={f["name"]: f["url"] for f in manifest["files"]},
    )


def latest(source_id: str, raw_dir: Path = RAW_DIR) -> Snapshot | None:
    """Most recent snapshot of a source, or None if it was never fetched."""
    dirs = sorted(p for p in (raw_dir / source_id).glob("*") if (p / MANIFEST).exists())
    return load(dirs[-1]) if dirs else None
