from __future__ import annotations

from pathlib import Path

from bank_statements_parsing.models import ManifestEntry
from bank_statements_parsing.state import (
    append_manifest_entry,
    load_manifest,
    manifest_path,
)


def test_load_manifest_returns_empty_when_file_missing(tmp_path: Path) -> None:
    entries = load_manifest(tmp_path)
    assert entries == {}


def test_append_and_reload_manifest(tmp_path: Path) -> None:
    entry = ManifestEntry(
        file_hash="abc123",
        source_kind="plain_txt",
        first_seen_run_id="run-1",
        first_seen_at="2026-01-01T00:00:00Z",
        first_seen_input_path="/tmp/file.txt",
        logical_size_bytes=10,
    )

    append_manifest_entry(tmp_path, entry)
    reloaded = load_manifest(tmp_path)

    assert manifest_path(tmp_path).exists()
    assert "abc123" in reloaded
    assert reloaded["abc123"].first_seen_run_id == "run-1"
