from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []

FORBIDDEN_TRACKED_PREFIXES = (
    "data/",
    ".venv/",
    "venv/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "htmlcov/",
    ".idea/",
    ".vscode/",
    ".codex/agents/",
)

FORBIDDEN_TRACKED_PARTS = ("/__pycache__/",)

FORBIDDEN_TRACKED_FILES = {
    ".coverage",
    ".DS_Store",
}

REQUIRED_GITIGNORE_PATTERNS = [
    "__pycache__/",
    "*.py[cod]",
    ".venv/",
    "venv/",
    ".pytest_cache/",
    ".coverage",
    ".coverage.*",
    "htmlcov/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".idea/",
    ".vscode/",
    ".DS_Store",
    "data/",
    ".uv-cache/",
]

FORBIDDEN_CODEX_CONFIG_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*model\s*=", re.MULTILINE), "model"),
    (re.compile(r"^\s*approval_policy\s*=", re.MULTILINE), "approval_policy"),
    (re.compile(r"^\s*sandbox_mode\s*=", re.MULTILINE), "sandbox_mode"),
    (re.compile(r"^\s*\[profiles(?:\.|])", re.MULTILINE), "[profiles]"),
    (re.compile(r"^\s*\[mcp_servers(?:\.|])", re.MULTILINE), "[mcp_servers]"),
    (re.compile(r"^\s*mcp_servers\.", re.MULTILINE), "mcp_servers.*"),
    (re.compile(r"^\s*\[history(?:\.|])", re.MULTILINE), "[history]"),
    (re.compile(r"^\s*history\.", re.MULTILINE), "history.*"),
    (re.compile(r"^\s*\[analytics(?:\.|])", re.MULTILINE), "[analytics]"),
    (re.compile(r"^\s*analytics\.", re.MULTILINE), "analytics.*"),
    (
        re.compile(r"^\s*developer_instructions\s*=", re.MULTILINE),
        "developer_instructions",
    ),
]


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


def check_tracked_files(files: list[str]) -> None:
    for file in files:
        if (
            file in FORBIDDEN_TRACKED_FILES
            or Path(file).name in FORBIDDEN_TRACKED_FILES
        ):
            fail(f"tracked generated/local file is not allowed: {file}")
        if file == ".env" or (file.startswith(".env.") and file != ".env.example"):
            fail(f"tracked env file is not allowed: {file}")
        if file.startswith(FORBIDDEN_TRACKED_PREFIXES):
            fail(f"tracked local/generated path is not allowed: {file}")
        if any(part in f"/{file}/" for part in FORBIDDEN_TRACKED_PARTS):
            fail(f"tracked __pycache__ file is not allowed: {file}")


def check_gitignore() -> None:
    gitignore_path = REPO_ROOT / ".gitignore"
    if not gitignore_path.exists():
        fail("missing .gitignore")
        return

    lines = {
        line.strip()
        for line in gitignore_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    for pattern in REQUIRED_GITIGNORE_PATTERNS:
        if pattern not in lines:
            fail(f".gitignore: missing {pattern}")


def check_codex_config() -> None:
    config_path = REPO_ROOT / ".codex" / "config.toml"
    if not config_path.exists():
        fail(".codex/config.toml: missing file")
        return

    source = config_path.read_text(encoding="utf-8")
    if "#:schema https://developers.openai.com/codex/config-schema.json" not in source:
        fail(".codex/config.toml: missing schema header")
    if not re.search(r"^\s*\[agents]\s*$", source, flags=re.MULTILINE):
        fail(".codex/config.toml: missing [agents] section")
    if not re.search(r"^\s*max_depth\s*=\s*1\s*$", source, flags=re.MULTILINE):
        fail(".codex/config.toml: max_depth must be 1")
    if not re.search(r"^\s*max_threads\s*=\s*4\s*$", source, flags=re.MULTILINE):
        fail(".codex/config.toml: max_threads must be 4")

    for pattern, label in FORBIDDEN_CODEX_CONFIG_PATTERNS:
        if pattern.search(source):
            fail(f".codex/config.toml: forbidden repo-level key {label}")


def main() -> int:
    files = workspace_files()
    check_tracked_files(files)
    check_gitignore()
    check_codex_config()

    if ERRORS:
        print("repo hygiene check failed", file=sys.stderr)
        for error in ERRORS:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("repo hygiene check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
