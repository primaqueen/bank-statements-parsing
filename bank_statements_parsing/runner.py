from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from .hashing import sha256_file
from .models import ManifestEntry, RunEvent, RunReport
from .state import append_manifest_entry, load_manifest


def generate_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def validate_input_path(input_path: Path) -> Path:
    resolved = input_path.expanduser().resolve()
    if not resolved.exists():
        raise ValueError(f"Input path does not exist: {input_path}")
    if not resolved.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")
    if resolved.suffix.lower() != ".txt":
        raise ValueError(f"Input path must point to a .txt file: {input_path}")
    return resolved


def run_duplicate_control(
    *,
    input_path: Path,
    output_dir: Path,
    run_id: str | None = None,
) -> RunReport:
    validated_input = validate_input_path(input_path)
    resolved_output = output_dir.expanduser().resolve()
    started = perf_counter()

    actual_run_id = run_id or generate_run_id()
    processed_at = utc_now_iso()
    file_hash = sha256_file(validated_input)
    logical_size_bytes = validated_input.stat().st_size

    manifest = load_manifest(resolved_output)
    existing = manifest.get(file_hash)

    if existing is None:
        entry = ManifestEntry(
            file_hash=file_hash,
            source_kind="plain_txt",
            first_seen_run_id=actual_run_id,
            first_seen_at=processed_at,
            first_seen_input_path=str(validated_input),
            logical_size_bytes=logical_size_bytes,
        )
        append_manifest_entry(resolved_output, entry)
        status = "new"
        duplicate_of_run_id = None
        duplicate_of_input_path = None
        new_files_count = 1
        duplicate_files_count = 0
    else:
        status = "duplicate"
        duplicate_of_run_id = existing.first_seen_run_id
        duplicate_of_input_path = existing.first_seen_input_path
        new_files_count = 0
        duplicate_files_count = 1

    event = RunEvent(
        run_id=actual_run_id,
        processed_at=processed_at,
        input_path=str(validated_input),
        source_kind="plain_txt",
        file_hash=file_hash,
        logical_size_bytes=logical_size_bytes,
        status=status,
        duplicate_of_run_id=duplicate_of_run_id,
        duplicate_of_input_path=duplicate_of_input_path,
    )

    report = RunReport(
        run_id=actual_run_id,
        inputs_total=1,
        new_files_count=new_files_count,
        duplicate_files_count=duplicate_files_count,
        bytes_total=logical_size_bytes,
        wall_clock_seconds=round(perf_counter() - started, 6),
    )

    run_dir = resolved_output / "runs" / actual_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(run_dir / "files.jsonl", event.to_dict())
    write_json(run_dir / "report.json", report.to_dict())

    return report


def write_jsonl(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        handle.write("\n")


def write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
