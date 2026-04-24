# Bank Statements Parsing

Python MVP для локальной проверки pipeline обработки банковских выписок. Текущий реализованный срез - duplicate control для одного standalone `.txt` файла между запусками.

## Current Status

Сейчас реализован только первый vertical slice:

- один запуск обрабатывает один standalone `.txt`;
- duplicate detection основан только на `file_hash`;
- одинаковое содержимое считается duplicate независимо от имени и пути файла;
- `.zip`, document-level parsing, нормализация выписок и запись в БД пока не реализованы.

Следующий medium+ срез описан в [docs/changes/active/zip-source-units](docs/changes/active/zip-source-units/status.md).

## Quick Start

Установить dev-зависимости:

```bash
uv sync --group dev
```

Запустить MVP:

```bash
uv run python -m bank_statements_parsing run --input <path-to-txt> --output <output-dir> [--run-id <id>]
```

Прогнать baseline:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run python scripts/check_docs_consistency.py
uv run python scripts/check_repo_hygiene.py
```

Полный каталог команд и troubleshooting notes живут в [docs/build-pipeline.md](docs/build-pipeline.md).

## Repository Layout

- [AGENTS.md](AGENTS.md) - короткие repo-level инструкции для Codex.
- [docs/STATUS.md](docs/STATUS.md) - текущий project-level snapshot.
- [docs/WORKPLAN.md](docs/WORKPLAN.md) - план развития harness и MVP slices.
- [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) - текущие boundaries и инварианты.
- [docs/operations/runbook.md](docs/operations/runbook.md) - repeatable operational сценарии.
- [docs/reference/dataset-classification-stats.md](docs/reference/dataset-classification-stats.md) - наблюдения по локальному corpus.
- `bank_statements_parsing/` - текущий Python CLI-код.
- `tests/` - `pytest` suite для CLI, hashing и state/manifest поведения.
- `data/` - локальный ignored corpus, не часть deterministic tests.
