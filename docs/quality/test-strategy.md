# Test Strategy

## Deterministic baseline

Базовый обязательный набор проверок:

- `uv run pytest -q`
- `uv run coverage run -m pytest -q`
- `uv run coverage report`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright`
- `uv run python scripts/check_docs_consistency.py`
- `uv run python scripts/check_repo_hygiene.py`

## Test data policy

- Unit и integration tests используют `tmp_path` и synthetic files.
- Tests не читают локальный `data/` corpus.
- Corpus smoke по `data/` является manual/data-dependent проверкой и не входит в deterministic baseline.

## Current coverage focus

Для Task 1 обязательны проверки:

- одинаковые bytes дают одинаковый SHA-256;
- разные bytes дают разные SHA-256;
- пустой manifest читается как пустое состояние;
- manifest append/reload работает без повреждения существующих entries;
- первый CLI run получает `status=new`;
- повторный run того же content получает `status=duplicate`;
- копия с тем же content считается duplicate независимо от имени;
- non-`.txt` input завершается с non-zero exit code и не создаёт outputs.

## Change-packet acceptance

Для medium+ задач acceptance живёт в `docs/changes/active/<slug>/acceptance.md`.

Минимум для закрытия packet:

- task-local acceptance обновлён и закрыт;
- durable knowledge поднято в stable docs;
- `uv run python scripts/check_docs_consistency.py` зелёный;
- `uv run python scripts/check_repo_hygiene.py` зелёный;
- профильные Python checks из baseline зелёные или verification gap явно описан.
