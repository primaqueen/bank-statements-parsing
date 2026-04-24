---
name: git-commit
description: Use when the task is to finish a repo-local change set with intentional staging, a Conventional Commits style message, and a safe commit.
---

# Git Commit

Use this skill only when the user explicitly asks to create a commit or asks for a commit message.

## Defaults

- language: `ru`
- source diff: staged changes, unless the user specified files
- unrelated changes outside task scope are not staged or committed
- current repository baseline may be fully untracked, so never auto-commit without explicit user request

## Workflow

1. Read `git status --short`.
2. Determine the current task scope and stage only matching files.
3. If the user specified files, stage only those files.
4. If staged diff is empty and files were not specified, stop.
5. Read `git diff --staged`.
6. Choose one primary Conventional Commits type.
7. Compose a concise Russian commit message.
8. Run required checks if the user requested a ready commit.
9. Do not commit if checks fail due to files inside commit scope.
10. Commit only after explicit user request.

## Safety

- do not stage the entire worktree silently
- do not include local `data/`, `.venv`, caches or generated outputs
- do not invent ticket IDs, body details or footers without evidence
