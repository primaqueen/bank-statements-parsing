# Acceptance

## Happy Path

- Standalone `.txt` сохраняет поведение Task 1: первый run `new`, повторный run того же content `duplicate`.
- `.zip` с одним `.txt` member создаёт один run event и одну manifest entry.
- `.zip` с несколькими `.txt` members создаёт отдельный run event на каждый member.
- Nested directories внутри `.zip` поддерживаются, а member path сохраняется в source locator.

## Negative Path

- Input, который не является `.txt` или `.zip`, завершается с non-zero exit code и не создаёт state/run outputs.
- Directory entries и non-`.txt` entries внутри `.zip` пропускаются.
- `.zip` без `.txt` entries завершается штатно с `source_units_total = 0` и не меняет manifest.

## Duplicate Semantics

- Одинаковые bytes под разными standalone names считаются duplicate.
- Одинаковые bytes в разных `.zip` member paths считаются duplicate.
- Одинаковые bytes между standalone `.txt` и `.zip` member считаются duplicate.
- Manifest не разрастается от одинакового content в разных container/member paths.

## Verification

- `uv run pytest -q`
- `uv run coverage run -m pytest -q`
- `uv run coverage report`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run python scripts/check_docs_consistency.py`
- `uv run python scripts/check_repo_hygiene.py`
