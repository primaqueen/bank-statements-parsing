# Разработка

## Стек

- Python 3.11+
- `uv`
- `pytest`
- `coverage.py`
- `ruff`
- `pyright`

## Локальная разработка

- Установить dev-зависимости: `uv sync --group dev`.
- Запускать CLI через `uv run python -m bank_statements_parsing ...`.
- Runtime-only dependencies сейчас не нужны beyond stdlib.
- Packaging для проекта отключен через `[tool.uv] package = false`.

## Структура кода

- `bank_statements_parsing/cli.py` - CLI parsing и user-facing validation.
- `bank_statements_parsing/runner.py` - orchestration текущего run.
- `bank_statements_parsing/hashing.py` - streaming SHA-256 по raw bytes.
- `bank_statements_parsing/state.py` - JSONL manifest state.
- `bank_statements_parsing/models.py` - dataclass records для manifest/run/report.
- `tests/` - synthetic temporary tests, без зависимости от локального `data/`.
- `docs/` - stable docs, active change-packets и reference notes.

## Правила кода

- Сначала сохранять простой stdlib-first дизайн; внешние зависимости добавлять только при явной пользе.
- I/O boundaries держать явными: CLI validation, source reading, hashing, state write и report write не смешивать без причины.
- Хэши считать по bytes потоково, без загрузки больших файлов целиком в память.
- Output JSON/JSONL писать детерминированно, с UTF-8 и стабильными keys, если это не ломает контракт.
- Тесты должны использовать `tmp_path` и synthetic files; локальный `data/` corpus использовать только для manual/corpus smoke.
- Комментарии объясняют причину нетривиального поведения, а не пересказывают код.

## Документация изменений

- Stable знания обновляются в `docs/`.
- Medium+ work оформляется в `docs/changes/active/<slug>/`.
- Повторяемый workflow оформляется skill'ом в `.agents/skills/`, а не новым длинным prompt-файлом в корне.
- Root `AGENTS.md` остаётся ссылочным entrypoint.

## Язык документации

- Проектную документацию, change-packets, планы, критерии приемки и статусы писать на русском языке.
- Английский оставлять для точных имён API, типов, функций, enum values, библиотек, команд, путей и verbatim output.

## Git workflow

- Git commit выполнять только по явному запросу пользователя.
- В commit должны попадать только файлы текущей задачи.
- Unrelated или pre-existing изменения в worktree не подмешивать.
