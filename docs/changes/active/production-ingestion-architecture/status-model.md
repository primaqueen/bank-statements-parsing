# Status Model

Этот документ фиксирует модель статусов для будущей production-системы обработки банковских выписок.

Документ не описывает текущее реализованное поведение Python MVP. Текущее поведение описано в `docs/architecture/ARCHITECTURE.md`.

Связанные документы:

```text
docs/changes/active/production-ingestion-architecture/plan.md
docs/changes/active/production-ingestion-architecture/status.md
docs/architecture/PRODUCTION_INGESTION_DRAFT.md
```

## Цель

Статусная модель должна позволять:

- видеть все найденные записи `type = 9`;
- не терять unsupported-кандидаты;
- фиксировать каждую попытку обработки;
- различать source, run, top-level file и logical source unit;
- корректно отражать архивы с несколькими файлами внутри;
- показывать в UI историю и текущее состояние обработки;
- поддерживать retry, manual reprocess и duplicate handling;
- не смешивать lifecycle status, classification, diagnostic severity и reason.

## Базовый принцип

В системе не должно быть одного универсального статуса на всё.

Статусы задаются отдельно для разных сущностей:

```text
import_source.status  -> состояние исходной записи из documents table
import_run.status     -> результат конкретной попытки обработки
import_file.status    -> состояние фактически прочитанного top-level S3 object
source_unit.status    -> состояние logical source unit
diagnostic.severity   -> серьёзность конкретной проблемы или события
```

## Status, reason, classification, diagnostic

Эти понятия должны храниться отдельно.

### Status

`status` показывает текущее lifecycle-состояние сущности.

Примеры:

```text
queued
processing
succeeded
failed
skipped_unsupported_format
```

### Reason

`reason` показывает, почему была создана попытка обработки.

Примеры для `import_run.reason`:

```text
scanner_discovered
queue_event
manual_retry
manual_reprocess
dev_upload
source_deleted_check
```

### Classification

`classification` показывает, что именно было найдено по содержимому source unit.

Примеры:

```text
1c_full_statement_with_documents
1c_statement_without_payment_documents
not_1c
unsupported_binary
```

### Diagnostic

`diagnostic` хранит конкретное предупреждение, ошибку или информационное событие.

Примеры:

```text
S3_OBJECT_NOT_FOUND
DISGUISED_ARCHIVE_DETECTED
TRAILING_NUL_BYTES_TRIMMED
INVALID_REQUIRED_DATE
DOCUMENT_WITHOUT_END_MARKER
```

## Entity overview

Минимальная модель состояния состоит из следующих сущностей:

```text
import_source
import_run
import_file
source_unit
diagnostic
```

Связи:

```text
import_source 1 -> N import_run

import_run N -> 0/1 import_file

import_file 1 -> N source_unit

diagnostic N -> 0/1 import_source
diagnostic N -> 0/1 import_run
diagnostic N -> 0/1 import_file
diagnostic N -> 0/1 source_unit
```

`diagnostic` может быть привязан к разным уровням, потому что проблема может возникнуть как на уровне source, так и на уровне S3 object, архива, source unit, parser-а или normalization.

---

# import_source.status

`import_source` соответствует одной записи из существующей таблицы загруженных документов.

Для production-источника:

```text
source_kind = document_table
source_document_id = documents.id
source_type = documents.type
key = documents.file_path
```

`import_source` создаётся для всех обнаруженных записей `type = 9` с заполненным `file_path`, включая unsupported-кандидаты.

Это нужно, чтобы UI показывал, что запись была обнаружена и осознанно пропущена, а не потеряна.

## Allowed values

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

## Значения

### discovered

Запись `type = 9` найдена scanner-ом и зарегистрирована во внутреннем состоянии.

Processing ещё не поставлен в очередь.

### queued

Для source создан `import_run`, который ожидает worker.

### processing

Есть активный `import_run`, который сейчас обрабатывается worker-ом.

### processed

Последняя значимая попытка обработки завершилась успешно.

Для обычной выписки это означает:

```text
файл прочитан
source units классифицированы
1C-выписка распарсена
данные нормализованы
результат записан в БД
нет warning/error diagnostics, влияющих на качество
```

### processed_with_warnings

Обработка завершена целостно, данные записаны, но есть нефатальные warnings.

Примеры:

```text
неизвестный необязательный ключ
пустое необязательное поле
нестандартное значение Кодировка=...
лишние строки после КонецФайла
архив содержит дополнительные not_1c members
```

Это успешный статус.

### partially_processed

Часть содержимого обработана успешно, часть — нет.

Основной кейс — архив с несколькими source units:

```text
archive.zip
  statement_1.txt -> succeeded
  statement_2.txt -> failed
  readme.txt      -> skipped_not_1c
```

Этот статус нужен, потому что `processed_with_warnings` слишком мягкий, а `failed` слишком жёсткий.

### failed

Последняя значимая попытка не смогла завершить обработку source.

Примеры:

```text
S3 object not found
S3 read failed
archive extraction failed
DB transaction failed
parser fatal error
невозможно безопасно выделить source units
```

### skipped_unsupported_format

Source найден, но формат не входит в текущую область обработки.

Пример:

```text
type = 9
file_path = *.xlsx
mime_type = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

Такой source должен быть виден в UI, но не должен попадать в 1C parser.

### skipped_duplicate_file

Top-level file по `raw_file_hash` уже был успешно обработан ранее, поэтому повторный обычный import не запускается.

При этом новая попытка фиксируется отдельным `import_run`.

### skipped_no_eligible_source_units

Файл или архив технически обработан, но внутри не найдено ни одной source unit, которую нужно парсить как банковскую выписку.

Пример:

```text
archive.zip
  contract.pdf
  image.png
  readme.txt
```

Это отличается от `skipped_unsupported_format`: сам top-level формат может быть поддерживаемым архивом, но внутри нет подходящих файлов.

### source_deleted

Исходная запись из существующей таблицы была удалена.

Новые обработки по ней не запускаются.

Этот статус не означает автоматическое удаление уже распарсенных данных. Политика удаления данных фиксируется отдельно.

---

# import_run.status

`import_run` соответствует одной попытке обработки `import_source`.

Один `import_source` может иметь несколько `import_run`.

Примеры:

```text
первая обработка
retry после ошибки
manual reprocess
повторная попытка, заблокированная как duplicate
проверка, завершившаяся skipped_unsupported_format
```

Даже если обработка не была допущена из-за duplicate или unsupported format, попытка всё равно сохраняется как отдельный `import_run`.

## Allowed values

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

## Значения

### queued

Run создан и ожидает worker.

### processing

Run взят worker-ом.

Рекомендуемые дополнительные поля:

```text
worker_id
started_at
heartbeat_at
```

Если worker перестал обновлять heartbeat, run может быть переведён в `failed` с diagnostic code:

```text
WORKER_HEARTBEAT_TIMEOUT
```

### succeeded

Попытка обработки завершена полностью и без существенных warnings.

### succeeded_with_warnings

Попытка обработки завершена полностью, но есть нефатальные diagnostics.

Это успешный статус.

### partially_succeeded

Часть содержимого обработана успешно, часть — нет.

Основной кейс — архив с несколькими source units.

### failed

Попытка не завершила pipeline.

Причина должна храниться в diagnostics, а не только в текстовом поле `error_message`.

Примеры diagnostic codes:

```text
S3_OBJECT_NOT_FOUND
S3_READ_FAILED
ARCHIVE_EXTRACTION_FAILED
UNSUPPORTED_ARCHIVE_ENCRYPTION
PARSER_FATAL_ERROR
DB_WRITE_FAILED
WORKER_HEARTBEAT_TIMEOUT
```

### skipped_unsupported_format

Run завершён без обработки, потому что формат source не поддерживается.

Пример:

```text
.xlsx
.xls
.pdf
.doc
.docx
unknown binary
```

### skipped_duplicate_file

Run завершён без повторного парсинга, потому что top-level file по `raw_file_hash` уже был успешно обработан ранее.

### skipped_no_eligible_source_units

Run обработал top-level object или архив, но не нашёл source units, подходящих для 1C parsing.

### skipped_source_deleted

Run не запущен или остановлен, потому что исходная запись уже помечена как deleted.

### cancelled

Ручная отмена или административная остановка.

В первой версии UI может не быть кнопки cancel, но статус стоит оставить для будущей эксплуатации.

---

# import_file.status

`import_file` соответствует фактически прочитанному top-level S3 object.

`bucket + key` определяет местоположение объекта.

Идентичность содержимого определяется через:

```text
raw_file_hash = SHA-256(raw bytes)
```

`import_file` может не создаваться, если source был пропущен как очевидный unsupported-кандидат только по metadata.

Пример:

```text
type = 9
file_path = *.xlsx
mime_type = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

В таком случае достаточно создать:

```text
import_source.status = skipped_unsupported_format
import_run.status = skipped_unsupported_format
```

## Allowed values

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

## top_level_kind

Тип top-level object не должен смешиваться со статусом.

Для этого используется отдельное поле:

```text
top_level_kind
```

Allowed values:

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

## Значения status

### reading

Worker читает S3 object.

### hash_calculated

`raw_file_hash` посчитан.

На этом этапе уже можно проверить file-level duplicate.

### classified

Top-level kind определён.

Примеры:

```text
plain_text
zip
rar
7z
unsupported_binary
```

### extracted

Для архива extraction завершён, source units созданы.

Для standalone text-файла допускается считать, что создан один synthetic source unit.

### ready

Top-level object полностью подготовлен к обработке source units.

### skipped_duplicate_file

После расчёта `raw_file_hash` найден ранее успешно обработанный файл, и дальнейший pipeline не запускался.

### unsupported_format

Фактическое содержимое top-level object не поддерживается.

### failed

Ошибка на уровне top-level file.

Примеры:

```text
S3_READ_FAILED
HASH_CALCULATION_FAILED
ARCHIVE_EXTRACTION_FAILED
FILE_SIGNATURE_CONFLICT
```

---

# source_unit.status

`source_unit` соответствует logical source unit внутри top-level объекта.

Для standalone text-файла source unit — сам файл.

Для archive-файла source units — members архива.

Каждый source unit имеет собственный hash:

```text
source_unit_hash = SHA-256(raw bytes source unit)
```

## Allowed values

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

## classification

Классификация source unit хранится отдельно от статуса.

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

## Production-scope mapping

### 1c_full_statement_with_documents

Поддерживаемая 1C-выписка с документами.

Ожидаемый status:

```text
succeeded
```

или:

```text
succeeded_with_warnings
```

если есть нефатальные diagnostics.

### 1c_statement_without_payment_documents

Поддерживаемая пустая 1C-выписка без платёжных документов.

Это не ошибка.

Ожидаемый status:

```text
succeeded
```

При этом:

```text
documents_count = 0
```

### 1c_statement_incomplete

Неполная 1C-выписка.

Ожидаемый status:

```text
requires_review
```

или:

```text
failed
```

в зависимости от тяжести structural diagnostics.

Такая source unit не должна молча попадать в business tables как полноценная выписка.

### 1c_document_export_only

1C export документов без полноценной структуры выписки.

Для текущего production-scope считается unsupported.

Ожидаемый status:

```text
skipped_unsupported_format
```

### 1c_other_non_statement_or_broken

1C-like файл, который не является поддерживаемой выпиской или имеет существенные structural problems.

Ожидаемый status:

```text
requires_review
```

или:

```text
failed
```

### not_1c

Файл не является 1C-выпиской.

Для archive member это обычно не ошибка.

Ожидаемый status:

```text
skipped_not_1c
```

### unsupported_binary

Неподдерживаемый бинарный файл.

Ожидаемый status:

```text
skipped_unsupported_format
```

### archive_member_extract_error

Ошибка извлечения конкретного member внутри архива.

Ожидаемый status:

```text
failed
```

## Значения status

### discovered

Source unit найдена.

Пример:

```text
archive.zip/member_1.txt
```

### classified

Classifier определил тип source unit.

### processing

Source unit передана в parser/normalizer.

### succeeded

Source unit успешно обработана.

### succeeded_with_warnings

Source unit обработана, но есть нефатальные diagnostics.

### failed

Source unit не удалось безопасно обработать.

### requires_review

Source unit требует ручного анализа или отдельного решения.

Этот статус нужен, чтобы отличать:

```text
технический сбой
```

от:

```text
структурно спорный файл, который не стоит молча импортировать
```

### skipped_not_1c

Source unit не является 1C-файлом.

Для archive members это нормальный случай.

### skipped_unsupported_format

Source unit имеет неподдерживаемый формат.

Примеры:

```text
.xlsx внутри архива
.pdf внутри архива
1c_document_export_only
```

### skipped_duplicate_source_unit

Source unit по `source_unit_hash` уже была успешно обработана ранее.

---

# diagnostic.severity

Diagnostics хранятся отдельно от статусов.

Один `import_run` может иметь много diagnostics.

## Allowed values

```text
info
warning
error
fatal
```

## Значения

### info

Информационное событие.

Примеры:

```text
DISGUISED_ARCHIVE_DETECTED
EMPTY_STATEMENT_DETECTED
DUPLICATE_FILE_DETECTED
```

### warning

Нефатальная проблема.

Примеры:

```text
UNKNOWN_OPTIONAL_KEY
TRAILING_NUL_BYTES_TRIMMED
NON_STANDARD_ENCODING_LABEL
ARCHIVE_CONTAINS_NON_1C_MEMBERS
```

### error

Проблема, из-за которой конкретная source unit или часть обработки не может быть корректно завершена.

Примеры:

```text
INVALID_REQUIRED_DATE
INVALID_REQUIRED_AMOUNT
DOCUMENT_WITHOUT_END_MARKER
```

### fatal

Проблема, из-за которой нельзя безопасно продолжать текущий уровень обработки.

Примеры:

```text
S3_OBJECT_NOT_FOUND
ARCHIVE_EXTRACTION_FATAL
DB_TRANSACTION_FAILED
UNRECOVERABLE_PARSER_STATE
```

---

# Aggregation rules

Статусы нижних уровней агрегируются наверх.

## source_unit -> import_run

### Все eligible source units успешно обработаны

```text
all eligible units succeeded
  -> import_run.succeeded
```

### Все eligible source units обработаны, но есть warnings

```text
all eligible units succeeded or succeeded_with_warnings
and at least one warning exists
  -> import_run.succeeded_with_warnings
```

### Есть успешные и проблемные eligible source units

```text
at least one eligible unit succeeded
and at least one eligible unit failed or requires_review
  -> import_run.partially_succeeded
```

### Нет eligible source units

```text
no eligible source units
  -> import_run.skipped_no_eligible_source_units
```

### Top-level формат не поддерживается

```text
top-level unsupported
  -> import_run.skipped_unsupported_format
```

### Top-level file является duplicate

```text
top-level duplicate file
  -> import_run.skipped_duplicate_file
```

### Source удалён до обработки

```text
source deleted before processing
  -> import_run.skipped_source_deleted
```

### Нет успешных units, есть error/fatal на eligible unit или выше

```text
no successful eligible units
and at least one error/fatal diagnostic exists
  -> import_run.failed
```

## import_run -> import_source

`import_source.status` обычно отражает состояние последнего значимого `import_run`.

```text
run.queued
  -> source.queued

run.processing
  -> source.processing

run.succeeded
  -> source.processed

run.succeeded_with_warnings
  -> source.processed_with_warnings

run.partially_succeeded
  -> source.partially_processed

run.failed
  -> source.failed

run.skipped_unsupported_format
  -> source.skipped_unsupported_format

run.skipped_duplicate_file
  -> source.skipped_duplicate_file

run.skipped_no_eligible_source_units
  -> source.skipped_no_eligible_source_units

run.skipped_source_deleted
  -> source.source_deleted
```

---

# Empty statements

Пустая 1C-выписка без платёжных документов считается успешно обработанной.

На уровне `source_unit`:

```text
classification = 1c_statement_without_payment_documents
status = succeeded
documents_count = 0
```

На уровне `import_run`:

```text
succeeded
```

или:

```text
succeeded_with_warnings
```

если есть нефатальные diagnostics.

Отдельный статус `empty_statement` не нужен.

---

# Unsupported `.xlsx`

Для `.xlsx` и похожих файлов из записей `type = 9`:

```text
import_source.status = skipped_unsupported_format
import_run.status = skipped_unsupported_format
```

`import_file` можно не создавать, если решение принято по очевидным metadata:

```text
mime_type = application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
extension = .xlsx
```

Но `import_source` и `import_run` должны быть сохранены, чтобы UI показывал, что запись была обнаружена и осознанно пропущена.

---

# Duplicate handling

File-level duplicate определяется по:

```text
raw_file_hash = SHA-256(raw bytes top-level S3 object)
```

Source-unit duplicate определяется по:

```text
source_unit_hash = SHA-256(raw bytes source unit)
```

## File-level duplicate

Если top-level file с таким `raw_file_hash` уже был успешно обработан, обычная повторная обработка не допускается.

При этом новая попытка фиксируется как отдельный `import_run`:

```text
import_run.status = skipped_duplicate_file
```

## Source-unit duplicate

Если source unit с таким `source_unit_hash` уже была успешно обработана, её можно пропустить:

```text
source_unit.status = skipped_duplicate_source_unit
```

Это особенно важно для разных архивов, внутри которых находится одна и та же выписка.

## Duplicate blocking policy

Не все terminal statuses одинаково блокируют повторный ordinary import.

| Status | Blocks ordinary duplicate import |
|---|---:|
| `succeeded` | yes |
| `succeeded_with_warnings` | yes |
| `partially_succeeded` | conditional |
| `failed` | no |
| `skipped_unsupported_format` | no, если S3 object не читался |
| `skipped_duplicate_file` | no |
| `skipped_no_eligible_source_units` | yes, если файл был прочитан и классифицирован |
| `skipped_source_deleted` | no |
| `cancelled` | no |

Для `partially_succeeded` решение зависит от причины:

```text
partial из-за детерминированного содержимого файла
  -> ordinary duplicate import можно блокировать

partial из-за инфраструктурной ошибки
  -> retry должен быть разрешён
```

Причина определяется по diagnostics.

---

# Retry policy

| Run status | Automatic retry | Manual retry / reprocess | Комментарий |
|---|---:|---:|---|
| `succeeded` | no | yes | Только осознанный reprocess |
| `succeeded_with_warnings` | no | yes | Warnings не должны сами запускать retry |
| `partially_succeeded` | no | yes | Нужен review перед reprocess |
| `failed` | conditional | yes | Auto retry только для infrastructure failures |
| `skipped_unsupported_format` | no | yes | Только если появилась поддержка формата |
| `skipped_duplicate_file` | no | yes | Только forced reprocess |
| `skipped_no_eligible_source_units` | no | yes | Обычно только после изменения classifier |
| `skipped_source_deleted` | no | limited | Только если исходная запись восстановлена |
| `cancelled` | no | yes | Административный случай |

## Retry categories

Diagnostics должны позволять отделять инфраструктурные ошибки от ошибок содержимого.

Примеры infrastructure failures:

```text
S3_READ_FAILED
DB_WRITE_FAILED
WORKER_HEARTBEAT_TIMEOUT
TEMP_STORAGE_UNAVAILABLE
```

Примеры content failures:

```text
ARCHIVE_EXTRACTION_FAILED
UNSUPPORTED_ARCHIVE_ENCRYPTION
DOCUMENT_WITHOUT_END_MARKER
UNRECOVERABLE_PARSER_STATE
```

Automatic retry допускается только для infrastructure failures.

---

# Terminal statuses

## import_run terminal statuses

```text
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

## import_source terminal-like statuses

`import_source` может находиться в terminal-like status до ручного действия, retry, reprocess или изменения внешней записи.

```text
processed
processed_with_warnings
partially_processed
failed
skipped_unsupported_format
skipped_duplicate_file
skipped_no_eligible_source_units
source_deleted
```

`import_source` не является immutable: новый `import_run` может изменить его агрегированный статус.

---

# UI expectations

Internal frontend должен показывать статусы на всех уровнях.

Минимально:

```text
import_source.status
latest import_run.status
import_file.status, если import_file был создан
source_unit.status
source_unit.classification
diagnostic.severity
diagnostic.code
```

UI должен явно различать:

```text
не найдено
найдено и ожидает обработки
обрабатывается
успешно
успешно с warnings
частично успешно
ошибка
duplicate
unsupported
source deleted
нет eligible source units
```

Unsupported-кандидаты `type = 9` должны быть видны в UI.

---

# Defaults

Зафиксированные defaults:

1. `1c_statement_without_payment_documents` считается успешной обработкой с `documents_count = 0`.
2. `.xlsx` и похожие форматы получают `skipped_unsupported_format`, видимы в UI и могут не читаться из S3, если metadata однозначна.
3. Архив с частью успешно обработанных source units и частью проблемных получает `partially_succeeded` на уровне `import_run`.
4. Diagnostics хранятся отдельно, а не только как одно поле `error_message`.
5. `requires_review` используется на уровне `source_unit`, а не как `import_run.status`.
6. `1c_document_export_only` считается unsupported для текущего production-scope.