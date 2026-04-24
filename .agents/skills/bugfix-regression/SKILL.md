---
name: bugfix-regression
description: Use when fixing a bug or behavioral regression that needs a clear repro, root-cause analysis, regression checks, and a concise acceptance note.
---

# Bugfix Regression

Use this skill for bugs where correctness and regression control matter more than broad feature planning.

## Use When

- there is a reproducible bug
- duplicate-control behavior drift must be traced
- CLI validation or output contract regressed
- source-unit or manifest semantics changed unexpectedly

## Workflow

1. Capture repro in concrete terms.
2. Trace the real execution path before proposing a fix.
3. Fix the smallest code path that removes the bug.
4. Add or update regression coverage where it materially reduces risk.
5. Document acceptance in the active change packet if the task is medium+.

## Output

- repro
- confirmed cause
- fix strategy
- regression checks
- acceptance result
