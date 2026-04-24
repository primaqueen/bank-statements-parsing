# AGENTS - bank-statements-parsing

Короткий repo-level entrypoint. Долговечные правила, контракты и verification contours живут в `docs/`, а не в этом файле.

## Что читать сначала

- [README.md](README.md)
- [docs/STATUS.md](docs/STATUS.md)
- [docs/WORKPLAN.md](docs/WORKPLAN.md)
- [docs/build-pipeline.md](docs/build-pipeline.md)
- [docs/development.md](docs/development.md)
- [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
- [docs/quality/test-strategy.md](docs/quality/test-strategy.md)
- [docs/operations/runbook.md](docs/operations/runbook.md)

Если задача относится к текущей medium+ инициативе, сначала открой соответствующий `docs/changes/active/<slug>/status.md`, затем `brief.md`, `plan.md` и `acceptance.md` в той же папке.

## Current implemented behavior

- Реализован Task 1: duplicate control для одного standalone `.txt` между запусками.
- CLI entrypoint: `python -m bank_statements_parsing run --input <path-to-txt> --output <output-dir> [--run-id <id>]`.
- Текущая реализация отвергает non-`.txt` inputs; `.zip` source units запланированы в active packet [zip-source-units](docs/changes/active/zip-source-units/status.md).
- Output contract: `<output>/state/files_manifest.jsonl`, `<output>/runs/<run_id>/files.jsonl`, `<output>/runs/<run_id>/report.json`.

## Repo-level правила

- `AGENTS.md` должен оставаться коротким и ссылочным; stable knowledge хранится в `docs/`.
- Medium+ задачи оформляются в `docs/changes/active/<slug>/` с `brief.md`, `plan.md`, `acceptance.md`, `status.md`.
- Small fixes идут без change-packet, но contract/architecture/verification changes обновляют профильные stable docs.
- `data/` - локальный ignored corpus. Не менять и не привязывать тесты к нему без явного scope.
- Секреты, локальные `.env`, IDE/MCP configs, `.venv`, caches и generated outputs не коммитить.
- Git commit выполнять только по явному запросу пользователя; текущий baseline репозитория может быть полностью untracked.

## Проверки

Канонический источник команд: [docs/build-pipeline.md](docs/build-pipeline.md).

Минимальный deterministic baseline:

- `uv run pytest -q`
- `uv run coverage run -m pytest -q`
- `uv run coverage report`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run python scripts/check_docs_consistency.py`
- `uv run python scripts/check_repo_hygiene.py`

## Shared Skills

Repo-local skills лежат в [`.agents/skills/`](.agents/skills/).

- [`feature-slice`](.agents/skills/feature-slice/SKILL.md) - medium+ feature/improvement packet.
- [`bugfix-regression`](.agents/skills/bugfix-regression/SKILL.md) - bugfix с repro, analysis и regression checks.
- [`docs-sync`](.agents/skills/docs-sync/SKILL.md) - синхронизация stable docs, active packet и verification instructions.
- [`git-commit`](.agents/skills/git-commit/SKILL.md) - безопасный commit workflow по явному запросу.
