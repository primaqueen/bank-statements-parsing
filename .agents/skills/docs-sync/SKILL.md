---
name: docs-sync
description: Use when a change is accepted and the repository docs, change-packet, data policy, or verification instructions must be synchronized before the task is considered finished.
---

# Docs Sync

Use this skill to close the gap between real code behavior and repository knowledge.

## Use When

- CLI or output contract changed
- source-unit, duplicate-control or parser semantics changed
- architecture or verification flow changed
- an active change packet is ready to close
- new skills, commands or repo rules were introduced

## Workflow

1. Update the affected stable docs in `docs/`.
2. Update active packet status and acceptance if the task used `docs/changes/active/`.
3. Keep durable reference facts in `docs/reference/`.
4. Remove stale root-level plan/runbook notes and obsolete references.
5. Run `uv run python scripts/check_docs_consistency.py` and `uv run python scripts/check_repo_hygiene.py`.

## Safety

- do not leave stale references to moved docs
- do not describe planned `.zip` or parser support as current behavior
- do not add new technical or product assumptions outside stable docs or active packet
