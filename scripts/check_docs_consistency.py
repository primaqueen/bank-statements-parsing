from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []

CANONICAL_FILES = [
    "README.md",
    "AGENTS.md",
    ".gitignore",
    ".codex/config.toml",
    "pyproject.toml",
    "pyrightconfig.json",
    "uv.lock",
    "docs/STATUS.md",
    "docs/WORKPLAN.md",
    "docs/build-pipeline.md",
    "docs/development.md",
    "docs/architecture/ARCHITECTURE.md",
    "docs/quality/test-strategy.md",
    "docs/quality/code-review.md",
    "docs/operations/runbook.md",
    "docs/reference/dataset-classification-stats.md",
]

ROOT_MARKDOWN_ALLOWLIST = {"README.md", "AGENTS.md"}
REQUIRED_PACKET_FILES = {"brief.md", "plan.md", "acceptance.md", "status.md"}
ROOT_AGENTS_MAX_BYTES = 6000
LINK_PATTERN = re.compile(r"!?\[[^\]]*]\(([^)]+)\)")


def fail(message: str) -> None:
    ERRORS.append(message)


def workspace_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    files = [line for line in result.stdout.splitlines() if line]
    return [file for file in files if (REPO_ROOT / file).exists()]


def normalize_link_target(raw_target: str) -> str | None:
    target = raw_target.strip().strip("<>")
    if not target or target.startswith("#"):
        return None
    if re.match(r"^[a-z][a-z0-9+.-]*:", target, flags=re.IGNORECASE):
        return None
    path_part = target.split("#", 1)[0]
    return path_part or None


def is_local_corpus_path(path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return False
    return rel.parts[:1] == ("data",)


def check_markdown_links(files: list[str]) -> None:
    markdown_files = [file for file in files if file.endswith(".md")]

    for file in markdown_files:
        abs_path = REPO_ROOT / file
        source = abs_path.read_text(encoding="utf-8")
        if "/Users/" in source:
            fail(f"{file}: absolute /Users/... path is not allowed")

        for match in LINK_PATTERN.finditer(source):
            raw_target = match.group(1)
            target = normalize_link_target(raw_target)
            if target is None:
                continue
            if target.startswith("/"):
                fail(f"{file}: absolute markdown link target '{raw_target}'")
                continue

            resolved = (abs_path.parent / target).resolve()
            if is_local_corpus_path(resolved):
                continue
            if not resolved.exists():
                fail(f"{file}: broken markdown link target '{raw_target}'")


def check_root_markdown(files: list[str]) -> None:
    root_markdown = {file for file in files if "/" not in file and file.endswith(".md")}
    extra = sorted(root_markdown - ROOT_MARKDOWN_ALLOWLIST)
    if extra:
        joined = ", ".join(extra)
        fail(f"root markdown files must be only README.md and AGENTS.md, got: {joined}")


def check_packets() -> None:
    active_root = REPO_ROOT / "docs" / "changes" / "active"
    if not active_root.exists():
        fail("docs/changes/active: missing directory")
        return

    for packet in sorted(path for path in active_root.iterdir() if path.is_dir()):
        existing = {child.name for child in packet.iterdir() if child.is_file()}
        missing = sorted(REQUIRED_PACKET_FILES - existing)
        if missing:
            fail(f"docs/changes/active/{packet.name}: missing {', '.join(missing)}")
        if (packet / "agents").exists():
            fail(
                f"docs/changes/active/{packet.name}: "
                "packet-local agents/ is not allowed"
            )


def check_canonical_files() -> None:
    for file in CANONICAL_FILES:
        if not (REPO_ROOT / file).exists():
            fail(f"missing canonical file: {file}")

    agents_path = REPO_ROOT / "AGENTS.md"
    if agents_path.exists() and len(agents_path.read_bytes()) > ROOT_AGENTS_MAX_BYTES:
        fail(f"AGENTS.md exceeds {ROOT_AGENTS_MAX_BYTES} bytes")


def main() -> int:
    files = workspace_files()
    check_canonical_files()
    check_root_markdown(files)
    check_markdown_links(files)
    check_packets()

    if ERRORS:
        print("docs consistency check failed", file=sys.stderr)
        for error in ERRORS:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("docs consistency check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
