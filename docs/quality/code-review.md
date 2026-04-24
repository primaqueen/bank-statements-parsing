# Code Review

## Приоритеты review

1. correctness и contract drift
2. регрессии duplicate/source-unit semantics
3. missing tests и verification gaps
4. data/privacy issues вокруг corpus и fixtures
5. maintainability и docs sync

## Что проверять

- не описана ли плановая `.zip`/parser functionality как уже реализованная;
- не изменился ли CLI/output contract без stable docs и tests;
- не стал ли duplicate detection зависеть от имени, пути или container path вместо bytes hash;
- не появились ли tests, завязанные на локальный ignored `data/` corpus;
- не попали ли в tracked files `.venv`, caches, `.coverage`, локальные env/IDE configs или corpus data;
- синхронно ли обновлены active packet и stable docs для medium+ изменения;
- нет ли новых root-level ad-hoc plan/runbook Markdown-файлов.

## Что не делать

- не превращать review в style-only комментарии, если нет риска для correctness;
- не принимать medium+ change без понятного acceptance и docs sync;
- не добавлять внешние dependencies только ради удобства, если stdlib достаточно.
