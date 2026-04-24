from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def run_cli(
    *,
    input_path: Path,
    output_dir: Path,
    run_id: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "bank_statements_parsing",
            "run",
            "--input",
            str(input_path),
            "--output",
            str(output_dir),
            "--run-id",
            run_id,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_first_run_is_new_and_second_run_of_same_content_is_duplicate(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "statement.txt"
    output_dir = tmp_path / "out"
    input_file.write_text("same statement\n", encoding="utf-8")

    first = run_cli(input_path=input_file, output_dir=output_dir, run_id="run-1")
    assert first.returncode == 0, first.stderr

    manifest_path = output_dir / "state" / "files_manifest.jsonl"
    first_event_path = output_dir / "runs" / "run-1" / "files.jsonl"
    first_report_path = output_dir / "runs" / "run-1" / "report.json"

    assert manifest_path.exists()
    assert first_event_path.exists()
    assert first_report_path.exists()

    manifest_entries = read_jsonl(manifest_path)
    assert len(manifest_entries) == 1

    first_event = read_jsonl(first_event_path)[0]
    assert first_event["status"] == "new"
    assert first_event["duplicate_of_run_id"] is None
    assert first_event["duplicate_of_input_path"] is None

    duplicate_input = tmp_path / "copy.txt"
    shutil.copyfile(input_file, duplicate_input)
    second = run_cli(input_path=duplicate_input, output_dir=output_dir, run_id="run-2")
    assert second.returncode == 0, second.stderr

    second_event_path = output_dir / "runs" / "run-2" / "files.jsonl"
    second_event = read_jsonl(second_event_path)[0]
    assert second_event["status"] == "duplicate"
    assert second_event["duplicate_of_run_id"] == "run-1"
    assert second_event["duplicate_of_input_path"] == str(input_file.resolve())

    manifest_entries = read_jsonl(manifest_path)
    assert len(manifest_entries) == 1


def test_same_name_with_different_content_is_new_and_non_txt_input_fails(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "out"
    input_file = tmp_path / "statement.txt"
    input_file.write_text("first version\n", encoding="utf-8")

    first = run_cli(input_path=input_file, output_dir=output_dir, run_id="run-1")
    assert first.returncode == 0, first.stderr

    input_file.write_text("second version\n", encoding="utf-8")
    second = run_cli(input_path=input_file, output_dir=output_dir, run_id="run-2")
    assert second.returncode == 0, second.stderr

    manifest_path = output_dir / "state" / "files_manifest.jsonl"
    manifest_entries = read_jsonl(manifest_path)
    assert len(manifest_entries) == 2

    second_event_path = output_dir / "runs" / "run-2" / "files.jsonl"
    second_event = read_jsonl(second_event_path)[0]
    assert second_event["status"] == "new"

    bad_input = tmp_path / "bad.csv"
    bad_input.write_text("bad\n", encoding="utf-8")
    bad_output = tmp_path / "bad-out"
    failed = run_cli(input_path=bad_input, output_dir=bad_output, run_id="run-bad")
    assert failed.returncode != 0
    assert not (bad_output / "state").exists()
    assert not (bad_output / "runs").exists()
