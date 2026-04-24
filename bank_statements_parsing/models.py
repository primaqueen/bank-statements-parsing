from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class ManifestEntry:
    file_hash: str
    source_kind: str
    first_seen_run_id: str
    first_seen_at: str
    first_seen_input_path: str
    logical_size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RunEvent:
    run_id: str
    processed_at: str
    input_path: str
    source_kind: str
    file_hash: str
    logical_size_bytes: int
    status: str
    duplicate_of_run_id: str | None
    duplicate_of_input_path: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class RunReport:
    run_id: str
    inputs_total: int
    new_files_count: int
    duplicate_files_count: int
    bytes_total: int
    wall_clock_seconds: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
