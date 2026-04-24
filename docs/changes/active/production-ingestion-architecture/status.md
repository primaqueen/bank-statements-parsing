# Status

- stage: `architecture-discussion`
- current_step: `status-model-defined`
- implementation_started: `false`
- last_updated: `2026-04-24`

## Зафиксировано

### Production source

- Production-файлы берутся из S3.
- Production scanner ориентируется на существующую таблицу загруженных документов.
- Для обработки рассматриваются записи `type = 9`.
- `id` исходной записи используется как стабильный внешний идентификатор source.
- `file_path` используется как S3 key.
- `bucket + key` достаточно для доступа к объекту.
- `versionId` не используется.
- `bucket + key` не является идентификатором содержимого.
- Идентичность содержимого определяется через `SHA-256(raw bytes)`.

### Scanner

- Основной scanner идёт по `id`.
- `updated` не используется как основной reconciliation-cursor.
- Удаление исходной записи учитывается отдельным deletion reconciliation.
- `type = 9` не гарантирует, что файл является 1C-выпиской.
- Unsupported-кандидаты сохраняются во внутреннем состоянии, чтобы UI показывал, что запись не была пропущена.
- `.xlsx` и похожие форматы получают `skipped_unsupported_format`, если они обнаружены как записи `type = 9`.

### Supported formats

Поддерживаются top-level расширения:

```text
.txt
.txt1
.txt2
.txt3
.txt4
.zip
.rar
.7z
```

Disguised archives должны определяться по содержимому, а не по расширению.

ZIP, RAR и 7z учитываются как контейнеры.

### Service model

- Система проектируется как service-first ingestion platform.
- Внешний потребитель работает через сервисный API.
- Внешний потребитель не вызывает отдельные classifier/parser/normalizer пакеты напрямую.
- Internal frontend является optional client для мониторинга, истории обработки и обратной связи.
- Frontend upload нужен в основном для dev/test-сценариев.

### Runtime

- Основной TypeScript runtime будущей production-системы — Bun.
- Production-критичные IO-границы должны быть изолированы адаптерами:
  - S3 client;
  - archive extractor;
  - database access;
  - worker/job execution;
  - dev/test upload path.

### Idempotency

Зафиксированы уровни идемпотентности:

```text
source-level idempotency
file-level idempotency
source-unit idempotency
```

Source-level idempotency:

```text
(source_kind, source_document_id)
```

File-level idempotency:

```text
raw_file_hash = SHA-256(raw bytes top-level S3 object)
```

Source-unit idempotency:

```text
source_unit_hash = SHA-256(raw bytes logical source unit)
```

Тем же самым файлом считается только файл с полностью одинаковым бинарным содержимым.

Если файл с таким `raw_file_hash` уже был успешно обработан, обычная повторная обработка не допускается.

При этом новая попытка обязательно фиксируется как отдельный `import_run`.

### Internal entities

Зафиксирована базовая внутренняя модель состояния:

```text
import_source
import_run
import_file
source_unit
diagnostic
```

`import_source` соответствует записи из существующей таблицы документов.

`import_run` соответствует отдельной попытке обработки.

`import_file` соответствует фактически прочитанному top-level S3 object.

`source_unit` соответствует logical source unit внутри top-level объекта или архива.

`diagnostic` хранит предупреждения, ошибки и информационные события.

### Status model

Полная модель статусов вынесена в отдельный документ:

```text
docs/changes/active/production-ingestion-architecture/status-model.md
```

Зафиксированы отдельные status sets для:

```text
import_source.status
import_run.status
import_file.status
source_unit.status
diagnostic.severity
```

Зафиксировано, что lifecycle status, reason, classification и diagnostic должны храниться отдельно.

### import_source.status

Зафиксированные значения:

```text
discovered
queued
processing
processed
processed_with_warnings
partially_processed
failed
skipped_unsupported_format
skipped_duplicate_file
skipped_no_eligible_source_units
source_deleted
```

### import_run.status

Зафиксированные значения:

```text
queued
processing
succeeded
succeeded_with_warnings
partially_succeeded
failed
skipped_unsupported_format
skipped_duplicate_file
skipped_no_eligible_source_units
skipped_source_deleted
cancelled
```

### import_file.status

Зафиксированные значения:

```text
reading
hash_calculated
classified
extracted
ready
skipped_duplicate_file
unsupported_format
failed
```

Для типа top-level object используется отдельное поле `top_level_kind`.

Зафиксированные значения `top_level_kind`:

```text
plain_text
zip
rar
7z
disguised_zip
disguised_rar
disguised_7z
unsupported_binary
unknown
```

### source_unit.status

Зафиксированные значения:

```text
discovered
classified
processing
succeeded
succeeded_with_warnings
failed
requires_review
skipped_not_1c
skipped_unsupported_format
skipped_duplicate_source_unit
```

Для результата classifier-а используется отдельное поле `classification`.

Минимальный набор classification values:

```text
1c_full_statement_with_documents
1c_statement_without_payment_documents
1c_statement_incomplete
1c_document_export_only
1c_other_non_statement_or_broken
not_1c
unsupported_binary
archive_member_extract_error
```

### diagnostic.severity

Зафиксированные значения:

```text
info
warning
error
fatal
```

### Production-scope defaults

Зафиксированные defaults:

- `1c_statement_without_payment_documents` считается успешной обработкой с `documents_count = 0`.
- `.xlsx` и похожие форматы получают `skipped_unsupported_format`, видимы в UI и могут не читаться из S3, если metadata однозначна.
- Архив с частью успешно обработанных source units и частью проблемных получает `partially_succeeded` на уровне `import_run`.
- Diagnostics хранятся отдельно, а не только как одно поле `error_message`.
- `requires_review` используется на уровне `source_unit`, а не как `import_run.status`.
- `1c_document_export_only` считается unsupported для текущего production-scope.

### Aggregation rules

Зафиксированы правила агрегации:

```text
source_unit -> import_run
import_run  -> import_source
```

Ключевые правила:

- все eligible source units успешны -> `import_run.succeeded`;
- все eligible source units успешны, но есть warnings -> `import_run.succeeded_with_warnings`;
- есть успешные и проблемные eligible source units -> `import_run.partially_succeeded`;
- нет eligible source units -> `import_run.skipped_no_eligible_source_units`;
- top-level unsupported -> `import_run.skipped_unsupported_format`;
- top-level duplicate -> `import_run.skipped_duplicate_file`;
- source deleted before processing -> `import_run.skipped_source_deleted`;
- нет успешных eligible units и есть error/fatal -> `import_run.failed`.

### Retry policy

Зафиксирована базовая retry policy:

- `succeeded` не требует automatic retry;
- `succeeded_with_warnings` не требует automatic retry;
- `partially_succeeded` требует review перед manual reprocess;
- `failed` допускает automatic retry только для infrastructure failures;
- `skipped_unsupported_format` не retry-ится автоматически;
- `skipped_duplicate_file` не retry-ится автоматически;
- `skipped_no_eligible_source_units` не retry-ится автоматически;
- `skipped_source_deleted` не retry-ится автоматически;
- `cancelled` может быть запущен повторно вручную.

## Blockers / open decisions

Не зафиксировано:

- финальная SQL-схема БД;
- точный список полей для `import_source`;
- точный список полей для `import_run`;
- точный список полей для `import_file`;
- точный список полей для `source_unit`;
- точный список полей для `diagnostic`;
- политика удаления уже обработанных данных при `source_deleted`;
- точный механизм очереди;
- API endpoints;
- стратегия batch/COPY записи результатов;
- полный catalog diagnostic codes;
- граница между parser diagnostics и normalizer diagnostics;
- политика parser version / reprocess;
- требования к internal frontend screens;
- права доступа и роли пользователей internal frontend.

## Next step

Следующий архитектурный вопрос:

Определить внутреннюю модель данных и минимальные поля для:

```text
import_source
import_run
import_file
source_unit
diagnostic
```

После этого можно переходить к:

- SQL-схеме;
- индексам;
- unique constraints;
- lifecycle transitions;
- API-контрактам для истории и мониторинга.

## Verification

Docs-only commit.

Рекомендуемые проверки:

```bash
uv run python scripts/check_docs_consistency.py
uv run python scripts/check_repo_hygiene.py
```