# Status

- stage: `architecture-discussion`
- current_step: `source-intake-and-idempotency-decisions`
- implementation_started: `false`
- last_updated: `2026-04-24`

## Зафиксировано

- Production-файлы берутся из S3.
- Production scanner ориентируется на существующую таблицу загруженных документов.
- Для обработки рассматриваются записи `type = 9`.
- `id` исходной записи используется как стабильный внешний идентификатор source.
- `file_path` используется как S3 key.
- `bucket + key` достаточно для доступа к объекту; `versionId` не используется.
- `bucket + key` не является идентификатором содержимого.
- Идентичность содержимого определяется через `SHA-256(raw bytes)`.
- Основной scanner идёт по `id`.
- `updated` не используется как основной reconciliation-cursor.
- Удаление исходной записи учитывается отдельным deletion reconciliation.
- `type = 9` не гарантирует, что файл является 1C-выпиской.
- Unsupported-кандидаты сохраняются во внутреннем состоянии, чтобы UI показывал, что запись не была пропущена.
- Поддерживаются top-level `.txt`, `.txt1`, `.txt2`, `.txt3`, `.txt4`, `.zip`, `.rar`, `.7z`.
- Disguised archives должны определяться по содержимому.
- Внешний потребитель работает через сервисный API, а не через отдельные classifier/parser/normalizer пакеты.
- Internal frontend является optional client для мониторинга и обратной связи.
- Основной TypeScript runtime будущей production-системы — Bun.

## Blockers / open decisions

- Не зафиксирована финальная схема БД.
- Не зафиксирован полный список статусов.
- Не зафиксирована политика удаления уже обработанных данных при удалении исходной записи.
- Не выбран механизм очереди.
- Не описаны API endpoints.
- Не описана стратегия batch-записи результатов.
- Не зафиксирована финальная classifier taxonomy.
- Не описана модель diagnostics.
- Не описана политика parser version / reprocess.

## Next step

Следующий архитектурный вопрос:

Определить внутреннюю модель данных для:

- `import_source`;
- `import_run`;
- `import_file`;
- `source_unit`;
- `diagnostic`.

После этого можно переходить к статусам и жизненному циклу обработки.

## Verification

Docs-only commit.

Рекомендуемые проверки:

```bash
uv run python scripts/check_docs_consistency.py
uv run python scripts/check_repo_hygiene.py
```

