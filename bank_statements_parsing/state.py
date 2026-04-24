from __future__ import annotations

import json
from pathlib import Path

from .models import ManifestEntry

STATE_DIRNAME = "state"
MANIFEST_FILENAME = "files_manifest.jsonl"


def manifest_path(output_dir: Path) -> Path:
    return output_dir / STATE_DIRNAME / MANIFEST_FILENAME


def load_manifest(output_dir: Path) -> dict[str, ManifestEntry]:
    path = manifest_path(output_dir)
    if not path.exists():
        return {}

    entries: dict[str, ManifestEntry] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            entry = ManifestEntry(**payload)
            entries.setdefault(entry.file_hash, entry)
    return entries


def append_manifest_entry(output_dir: Path, entry: ManifestEntry) -> None:
    path = manifest_path(output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry.to_dict(), ensure_ascii=False, sort_keys=True))
        handle.write("\n")
