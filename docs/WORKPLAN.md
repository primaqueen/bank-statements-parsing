# WORKPLAN.md

Program-level план развития repo harness и ближайших MVP slices.

## Milestones

| ID | Milestone | Status | Exit criteria |
|---|---|---|---|
| M0 | Реализовать Task 1 duplicate control для standalone `.txt` | `done` | CLI пишет manifest/run/report, duplicate status детерминирован, тесты зелёные |
| M1 | Нормализовать lean harness | `done` | `docs/` стал canonical knowledge store, root plans перенесены, локальные docs/repo checks добавлены |
| M2 | Реализовать `.zip` source units | `pending` | `.txt` и `.txt` members внутри `.zip` обрабатываются как logical source units с тем же duplicate control |
| M3 | Ввести parser/normalize MVP для `1CClientBankExchange` | `pending` | Появляются document-level outputs и quality metrics без записи в БД |
| M4 | Решить вопрос curated fixtures и CI | `pending` | Определён tracked fixtures policy и необходимость hosted CI |

## Next milestone

### M2 - `.zip` source units

Нужно:

- сохранить поведение Task 1 для standalone `.txt`;
- добавить discovery для `.zip` и nested `.txt` members;
- считать duplicate по logical source bytes независимо от container/member path;
- обновить tests, runbook и architecture docs после реализации.

## Update contract

Обновляй `WORKPLAN.md`, когда:

- меняется project-level milestone;
- появляется новый обязательный этап repo harness;
- меняется следующий крупный delivery slice.

Не используй `WORKPLAN.md` как task-local журнал. Для medium+ задач есть `docs/changes/active/<slug>/plan.md` и `status.md`.
