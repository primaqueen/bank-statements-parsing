# Production Ingestion Draft

Этот документ фиксирует черновую целевую архитектуру production-системы обработки банковских выписок.

Он не описывает текущее реализованное поведение Python MVP. Текущее поведение описано в `docs/architecture/ARCHITECTURE.md`.

Детальная история текущего обсуждения и открытые вопросы находятся в:

```text
docs/changes/active/production-ingestion-architecture/
```

## Краткое резюме

Целевая система должна обрабатывать банковские выписки из S3-хранилища.

Production-файлы уже загружаются в S3 внешним бизнес-процессом. Сервис импорта должен находить нужные записи в существующей таблице документов, где банковские выписки имеют `type = 9`.

Основной поток:

```text
documents table, type = 9
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
1C parsing
  ↓
normalization
  ↓
database
```

## Основные решения

### 1. Service-first

Система проектируется как service-first ingestion platform.

Внешние потребители работают через API сервиса.

Отдельные внутренние компоненты `classifier`, `parser`, `normalizer` не являются публичными интерфейсами для внешних потребителей.

### 2. Production source — S3

Production-файлы берутся из S3 по:

```text
bucket
key
```

`key` берётся из поля `file_path` существующей таблицы документов.

`versionId` не используется.

### 3. Existing documents table

Основной источник обнаружения файлов — существующая таблица загруженных документов.

Scanner рассматривает записи:

```text
type = 9
file_path заполнен
deleted пустой
```

`id` исходной записи используется как стабильный внешний идентификатор source.

### 4. Unsupported-файлы тоже фиксируются

`type = 9` не гарантирует, что файл является 1C-выпиской.

Если запись имеет `type = 9`, но формат файла не поддерживается, она всё равно должна быть сохранена во внутреннем состоянии import-сервиса со статусом вроде:

```text
skipped_unsupported_format
```

Это нужно, чтобы внутренний UI показывал, что запись была обнаружена и осознанно пропущена.

### 5. Content hash

Идентичность файла определяется только по содержимому.

Для top-level S3 object:

```text
raw_file_hash = SHA-256(raw bytes)
```

Для logical source unit внутри архива:

```text
source_unit_hash = SHA-256(raw bytes source unit)
```

Имя файла, путь, original name, MIME type и S3 key не являются content identity.

### 6. Поддерживаемые форматы

Поддерживаемые top-level форматы:

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

Также должны учитываться disguised archives, когда расширение не соответствует фактической бинарной сигнатуре файла.

### 7. Archive support

ZIP, RAR и 7z должны обрабатываться как контейнеры.

Внутри архивов выделяются logical source units.

Каждый logical source unit классифицируется и хэшируется отдельно.

### 8. Bun

Основной runtime для будущей TypeScript-части — Bun.

Production-критичные интеграции должны быть изолированы адаптерами:

```text
S3 client
archive extractor
database access
worker/job execution
dev/test upload path
```

### 9. Internal frontend

Internal frontend является необязательным клиентом API.

Его задача:

* история обработок;
* мониторинг процесса;
* visibility по unsupported-файлам;
* visibility по duplicate attempts;
* diagnostics;
* ручные dev/test загрузки;
* анализ проблемных source units.

## Не зафиксировано

Этот документ пока не фиксирует:

* финальную схему БД;
* API-контракты;
* полную модель статусов;
* стратегию очереди;
* политику удаления данных;
* parser/normalizer diagnostics;
* reprocess policy;
* frontend screens.
