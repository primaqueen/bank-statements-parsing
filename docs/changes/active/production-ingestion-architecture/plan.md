# Production Ingestion Architecture Plan

Этот документ фиксирует промежуточные архитектурные решения для будущей production-системы обработки банковских выписок.

Документ не описывает текущее реализованное поведение Python MVP. Текущее поведение описано в `docs/architecture/ARCHITECTURE.md`.

## Цель

Спроектировать production-систему, которая:

- обрабатывает исторический корпус банковских выписок;
- далее обрабатывает новые выписки на ежедневной основе;
- берёт файлы из S3-хранилища;
- учитывает существующую таблицу загруженных документов;
- поддерживает текстовые 1C-выписки и архивы;
- фиксирует историю загрузок, попыток обработки, дублей, ошибок и unsupported-файлов;
- предоставляет API для внешнего использования;
- предоставляет внутренний frontend для мониторинга и обратной связи.

## Вводные

Бизнес-объём текущих данных — около 36 GB за год.

После первичной обработки исторического корпуса ожидается ежедневная инкрементальная обработка новых выписок.

Один файл может быть от нескольких мегабайт до сотен мегабайт. Очень большие файлы встречаются редко.

## Production source

Production-источником файлов является S3-хранилище.

Файлы загружаются в S3 внешним бизнес-процессом. Сервис обработки не обязан принимать production-файлы через frontend upload.

Основной production-flow:

```text
существующая таблица документов
  ↓
scanner
  ↓
import_source
  ↓
import_run
  ↓
worker
  ↓
S3 object
  ↓
source discovery
  ↓
archive extraction
  ↓
classification
  ↓
parsing
  ↓
normalization
  ↓
database
```

Frontend upload нужен в основном для dev/test-сценариев и ручной проверки проблемных файлов.

## Existing documents table

В существующей таблице загруженных документов файлы банковских выписок имеют `type = 9`.

Пример значимых полей исходной записи:

```text
id
file_path
size
mime_type
original_name
type
created
deleted
updated
company
customer_company
```

Для production scanner-а используются:

* `id` — стабильный внешний идентификатор записи;
* `file_path` — S3 key;
* `type` — первичный бизнес-признак кандидата;
* `mime_type` — первичный технический признак кандидата;
* `original_name` — дополнительный признак расширения и человекочитаемое имя;
* `size` — заявленный размер из исходной таблицы;
* `created` — metadata;
* `deleted` — признак удаления исходной записи;
* `company` / `customer_company` — бизнес-контекст.

`updated` не используется как основной reconciliation-cursor, потому что значимые для файла поля старых записей в нормальном сценарии не меняются.

Единственное значимое изменение старой записи для import-сервиса — удаление исходной записи. Если исходная запись была удалена, новые обработки по ней не запускаются, а внутренний source помечается как `source_deleted`.

## Scanner policy

Scanner идёт по `id ASC`.

Основной отбор:

```text
type = 9
file_path заполнен
deleted пустой
```

Scanner должен создавать внутреннюю запись `import_source` не только для поддерживаемых файлов, но и для unsupported-кандидатов `type = 9`.

Причина: в UI должно быть видно, что запись не была пропущена молча. Если файл не входит в поддерживаемую область обработки, он должен получить явный статус вроде `skipped_unsupported_format`.

## Supported candidate formats

`type = 9` не является гарантией, что файл является 1C-выпиской.

На этапе scanner-а в обработку или регистрацию попадают кандидаты с `type = 9`.

Дальше они делятся на:

1. supported candidates;
2. unsupported candidates.

### Supported top-level extensions

Поддерживаемые top-level расширения для production-пайплайна:

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

### Supported MIME types

Основные MIME-типы:

```text
text/plain
application/zip
application/x-zip-compressed
application/x-rar-compressed
application/vnd.rar
application/x-7z-compressed
```

`application/octet-stream` допускается только если `file_path` или `original_name` имеют поддерживаемое расширение.

### Unsupported candidates

Примеры unsupported-кандидатов:

```text
.xlsx
.xls
.pdf
.doc
.docx
unknown binary
```

Такие записи не передаются в 1C parser, но сохраняются во внутреннем состоянии import-сервиса со статусом `skipped_unsupported_format`.

## Content-based discovery

`mime_type`, `file_path` и `original_name` используются только для первичного отбора.

Окончательное определение типа файла выполняется по содержимому S3 object:

```text
raw bytes
container signatures
1C header
encoding token family
structural coherence
```

Перед попыткой декодирования текста нужно проверить сигнатуры контейнеров:

```text
PK\x03\x04        -> ZIP
Rar!\x1a\x07      -> RAR
7z\xbc\xaf\x27\x1c -> 7z
```

Если файл с расширением `.txt` фактически является архивом, он должен обрабатываться как архив, а не как plain text.

## Archive support

Production-версия должна учитывать:

```text
ZIP
RAR
7z
disguised archives with misleading extensions
```

Архивы раскрываются в logical source units.

Logical source unit — это отдельный файл внутри top-level объекта, который может быть классифицирован и потенциально распарсен как выписка.

Примеры:

```text
standalone .txt
.txt member внутри .zip
.txt member внутри .rar
.txt member внутри .7z
архивный member, который сам оказался disguised archive
```

Поддержка архивов должна быть изолирована в отдельном внутреннем компоненте `archive-extractor`.

## S3 identity

Production-сервис работает с S3 object по:

```text
bucket
key
```

`versionId` не используется.

`bucket + key` определяет местоположение объекта, но не является идентификатором содержимого.

Фактически обработанное содержимое идентифицируется через:

```text
raw_file_hash = SHA-256(raw bytes top-level S3 object)
```

Для logical source unit внутри архива используется:

```text
source_unit_hash = SHA-256(raw bytes logical source unit)
```

S3 `ETag` можно сохранять как справочную metadata, но нельзя использовать как основной content hash.

## Idempotency levels

В системе есть несколько уровней идемпотентности.

### Source-level idempotency

Одна запись существующей таблицы документов не должна создавать несколько `import_source`.

Уникальность:

```text
(source_kind, source_document_id)
```

Где:

```text
source_kind = document_table
source_document_id = documents.id
```

### File-level idempotency

Один и тот же top-level S3 object по содержимому не должен импортироваться как новый файл повторно.

Идентичность файла:

```text
raw_file_hash = SHA-256(raw bytes)
```

Тем же самым файлом считается только файл с полностью одинаковым бинарным содержимым.

Если файл с таким `raw_file_hash` уже был успешно обработан, обычная повторная обработка не допускается.

При этом новая попытка загрузки или обработки обязательно фиксируется как отдельный `import_run` со статусом вроде:

```text
skipped_duplicate_file
```

или

```text
rejected_duplicate_file
```

### Source-unit idempotency

Если top-level object является архивом, каждый logical source unit внутри архива получает собственный hash:

```text
source_unit_hash = SHA-256(raw bytes source unit)
```

Это позволяет определить, что разные архивы содержат одну и ту же выписку.

## Import source

`import_source` — внутренняя запись сервиса, соответствующая одной найденной записи исходной таблицы документов.

Минимальные поля:

```text
id
source_kind
source_document_id
source_type
bucket
key
original_name
mime_type
declared_size
company_id
customer_company_id
source_created_at
source_deleted
discovered_at
current_status
unsupported_reason
```

Пример статусов:

```text
discovered
queued
processing
processed
failed
source_deleted
skipped_unsupported_format
```

## Import run

`import_run` — отдельная попытка обработки `import_source`.

Даже если обработка не была допущена из-за duplicate file, попытка должна быть сохранена.

Минимальные поля:

```text
id
import_source_id
reason
status
started_at
finished_at
worker_id
error_message
duplicate_of_file_id
parser_version
```

Пример `reason`:

```text
scanner_discovered
manual_retry
manual_reprocess
dev_upload
queue_event
source_deleted_check
```

Пример `status`:

```text
queued
processing
succeeded
succeeded_with_warnings
failed
skipped_duplicate_file
skipped_unsupported_format
source_deleted
```

## Runtime

Основной runtime для TypeScript-части будущей production-системы — Bun.

Bun используется для:

* API;
* worker;
* internal frontend;
* test runner;
* package management в монорепозитории.

Production-критичные IO-границы должны быть изолированы адаптерами:

```text
S3 client
archive extractor
database access
worker/job execution
dev/test upload path
```

Если конкретная интеграция окажется нестабильной под Bun, она должна быть заменяема без изменения архитектуры core pipeline.

## Service-first model

Система проектируется как service-first ingestion platform.

Внешний потребитель не вызывает classifier/parser/normalizer напрямую.

Основной внешний контракт:

```text
API сервиса
```

Отдельные внутренние компоненты:

```text
source discovery
archive extraction
classification
parser
normalizer
diagnostics
```

не являются самостоятельными публичными API для внешнего источника.

## Internal frontend

Frontend является внутренним инструментом мониторинга и обратной связи.

Он должен показывать:

* историю найденных записей `type = 9`;
* историю import sources;
* историю import runs;
* статусы обработки;
* duplicate/rejected attempts;
* unsupported candidates;
* source units внутри архивов;
* diagnostics;
* warnings/errors;
* прогресс обработки исторического корпуса;
* результаты dev/test загрузок.

Frontend не является обязательной частью production-интеграции.

## Proposed future monorepo structure

Ориентировочная структура будущего production-проекта:

```text
apps/
  api/
  worker/
  web/
  cli/

packages/
  import-core/
    source-discovery/
    archive-extractor/
    source-classifier/
    one-c-parser/
    normalizer/
    diagnostics/

  import-contracts/
    statuses/
    api-dto/
    events/

  db/
    migrations/
    repositories/
```

В текущем Python MVP эта структура не реализуется автоматически. Она фиксирует целевую архитектурную модель для будущей production-системы.

## Open questions

Пока не зафиксировано:

* финальная схема БД;
* полный список статусов `import_source`;
* полный список статусов `import_run`;
* политика удаления уже обработанных данных при `source_deleted`;
* точный механизм очереди;
* batch/COPY стратегия записи в БД;
* финальная taxonomy для classifier;
* граница между parser diagnostics и normalizer diagnostics;
* политика reprocess после изменения parser version;
* требования к внутреннему frontend;
* API-контракты.

