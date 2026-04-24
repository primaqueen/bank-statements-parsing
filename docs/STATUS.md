# STATUS.md

## Snapshot

- Stage: `lean-harness-v1`
- Active delivery slice: `zip-source-units`
- Last updated: `2026-04-24`
- Priority: `high`

## Что уже зафиксировано

- Python MVP реализует duplicate control для одного standalone `.txt`.
- CLI пишет `state/files_manifest.jsonl`, `runs/<run_id>/files.jsonl` и `runs/<run_id>/report.json`.
- Duplicate detection выполняется по `sha256(raw_bytes)`, а не по имени или пути файла.
- Quality stack проекта: `pytest`, `coverage.py`, `ruff`, `pyright`.
- Stable knowledge store нормализован под `docs/`.
- Root `AGENTS.md` служит ссылочным entrypoint, а не manual.
- `data/` считается локальным ignored corpus; deterministic tests используют synthetic temporary files.
- Medium+ work ведётся через `docs/changes/active/<slug>/`.

## Текущая цель

Реализовать следующий vertical slice: source discovery и duplicate control для standalone `.txt` и `.txt` members внутри `.zip` как отдельных logical source units.

## Риски

- Doc drift между текущим CLI contract и плановыми `.zip`/parser capabilities.
- Случайная привязка deterministic tests к локальному `data/` corpus.
- Изменение output JSONL/report contract без синхронного обновления docs и active packet.
- `uv run` в restricted sandbox может требовать project-local `UV_CACHE_DIR` или разрешение на `~/.cache/uv`.

## Следующий шаг

1. Довести active packet `zip-source-units` до реализации.
2. После закрытия packet поднять durable facts в stable docs.
3. Решить, нужен ли curated tracked fixtures-набор отдельно от локального `data/` corpus.
