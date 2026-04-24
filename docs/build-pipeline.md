# Build Pipeline

Канонический human-readable каталог команд и verification contours для репозитория.

## Setup

- `uv sync --group dev` - установить dev-зависимости.
- `uv run python -m bank_statements_parsing run --input <path-to-txt> --output <output-dir> [--run-id <id>]` - ручной запуск текущего CLI.

## Deterministic baseline

Запускать для change sets, которые меняют код, docs topology, skills или repo-level harness:

- `uv run pytest -q`
- `uv run coverage run -m pytest -q`
- `uv run coverage report`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run python scripts/check_docs_consistency.py`
- `uv run python scripts/check_repo_hygiene.py`

## Focused checks

- `uv run pytest tests/test_cli_integration.py -q` - CLI и output contract.
- `uv run pytest tests/test_hashing.py tests/test_state.py -q` - hashing и manifest state.
- `uv run ruff check . --fix` и `uv run ruff format .` - локальное автоисправление перед финальной проверкой.

## Smoke run

Текущий smoke path использует один standalone `.txt`:

```bash
uv run python -m bank_statements_parsing run \
  --input data/<company>/<file>.txt \
  --output /tmp/bsp-smoke-run \
  --run-id smoke-run
```

Если локальный `data/` corpus недоступен, smoke можно выполнить на временном synthetic `.txt`, но это не заменяет corpus smoke для parser/source-IO changes.

## Coverage

Coverage пишет локальный `.coverage`, который игнорируется git. Если среда запрещает запись в repo root, укажи временный data file через переменные окружения shell или запускай проверку в окружении с правом записи.

## Restricted sandbox notes

В ограниченной среде `uv` может пытаться открыть cache в `~/.cache/uv`. Для таких запусков можно использовать project-local или `/tmp` cache, не меняя canonical command contract:

```bash
UV_CACHE_DIR=.uv-cache uv run pytest -q
```

Если сама рабочая директория доступна только read-only sandbox, checks, которые пишут `.pytest_cache`, `.ruff_cache` или `.coverage`, требуют разрешения на запись или отдельного writable checkout.

## Change-packets

- Small fixes и простые улучшения проходят без `docs/changes/`.
- Medium+ задачи получают packet в `docs/changes/active/<slug>/`.
- Для medium+ задачи acceptance считается незавершённым, пока не зелёные task-local acceptance, docs check и repo hygiene check.
