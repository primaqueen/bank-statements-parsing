# Status

- stage: `planning`
- current_step: active packet создан из root Task 2 plan
- blockers:
  - implementation not started
  - output contract changes need synchronized tests and stable docs update
- next_step:
  - implement discovery/source_io and update runner/models without breaking Task 1 behavior

## Verification

- pending:
  - `uv run pytest -q`
  - `uv run coverage run -m pytest -q`
  - `uv run coverage report`
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pyright`
  - `uv run python scripts/check_docs_consistency.py`
  - `uv run python scripts/check_repo_hygiene.py`
