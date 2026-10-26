from datetime import UTC, datetime

import pytest

from compilador import snapshot
from compilador.snapshot import RawFile

NOW = datetime(2026, 10, 25, 12, 0, tzinfo=UTC)


def test_write_then_latest_round_trips_with_provenance(tmp_path):
    snapshot.write(
        "wdi",
        [RawFile("a.json", "https://x/a", b"{}")],
        source_version="v1",
        license="CC-BY-4.0",
        raw_dir=tmp_path,
        now=NOW,
    )
    snap = snapshot.latest("wdi", tmp_path)
    assert snap.path == tmp_path / "wdi" / "2026-10-25"
    assert snap.source_version == "v1"
    assert snap.retrieved_at == "2026-10-25T12:00:00+00:00"
    assert snap.files == {"a.json": "https://x/a"}
    assert snap.read("a.json") == b"{}"


def test_latest_picks_most_recent_date(tmp_path):
    for day in (24, 25):
        snapshot.write(
            "wdi",
            [RawFile("a.json", "u", str(day).encode())],
            source_version=str(day),
            license="l",
            raw_dir=tmp_path,
            now=NOW.replace(day=day),
        )
    assert snapshot.latest("wdi", tmp_path).source_version == "25"


def test_latest_without_snapshot_is_none(tmp_path):
    assert snapshot.latest("wdi", tmp_path) is None


def test_tampered_file_is_rejected(tmp_path):
    snap = snapshot.write(
        "wdi", [RawFile("a.json", "u", b"{}")], source_version="v", license="l", raw_dir=tmp_path
    )
    (snap.path / "a.json").write_bytes(b"{changed}")
    with pytest.raises(ValueError, match="sha256"):
        snapshot.load(snap.path)
