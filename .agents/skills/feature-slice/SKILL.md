---
name: feature-slice
description: Use when a medium+ feature or improvement needs a change-packet in docs/changes/active and must stay synchronized with stable docs, checks, and acceptance criteria.
---

# Feature Slice

Use this skill for medium+ feature or improvement work that crosses modules, changes CLI/output contracts, changes source-unit semantics, or needs explicit acceptance.

## Use When

- multi-step implementation
- source discovery, parser, normalize, writer or metrics changes
- CLI contract or output JSON/JSONL schema changes
- data-contract or corpus policy changes
- risky duplicate-control behavior changes

## Required Packet

Create or update `docs/changes/active/<slug>/` with at least:

- `brief.md`
- `plan.md`
- `acceptance.md`
- `status.md`

Add `context.md`, `design.md` or `decisions.md` only when they reduce ambiguity.

## Workflow

1. Confirm that the packet matches the real scope.
2. Read stable docs before coding.
3. Keep task-local decisions inside the packet until they become durable repo knowledge.
4. Implement the change in small slices with explicit verification.
5. Sync stable docs in the same change set when system contracts move.
6. Close the packet only after acceptance and docs sync are done.

## Done Criteria

- packet acceptance is current
- `uv run python scripts/check_docs_consistency.py` is green
- `uv run python scripts/check_repo_hygiene.py` is green
- durable knowledge has been promoted to `docs/`
