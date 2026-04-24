# Plan

Этот документ детализирует следующий vertical slice после [../../../architecture/ARCHITECTURE.md](../../../architecture/ARCHITECTURE.md): обработку standalone `.txt` и `.txt` внутри `.zip` как отдельных source units с тем же duplicate control по содержимому.

## Summary

Цель второй задачи: расширить текущий Python CLI так, чтобы он принимал на вход либо standalone `.txt`, либо `.zip`, находил внутри архива все `.txt` entries, обрабатывал каждый такой entry как отдельный logical source и применял duplicate detection по `file_hash`.

Главный принцип этой задачи:

- duplicate detection выполняется по содержимому logical source unit;
- для standalone `.txt` logical source unit это сам файл;
- для `.zip` logical source unit это каждый отдельный `.txt` member после чтения его байтов как самостоятельного текстового файла;
- одинаковое содержимое считается duplicate независимо от имени файла, пути файла, имени архива или пути member внутри архива.

В этот срез не входят:

- парсинг `1CClientBankExchange`;
- декодирование `cp1251` и любых других текстовых кодировок;
- document-level outputs;
- запись в БД;
- parallel workers;
- рекурсивная обработка архивов внутри архивов.

## Implementation Changes

### Target Layout

```text
pyproject.toml
bank_statements_parsing/
  __init__.py
  __main__.py
  cli.py
  models.py
  hashing.py
  state.py
  runner.py
  discover.py
  source_io.py
tests/
```

`discover.py` и `source_io.py` добавляются в этом срезе. Остальные модули из `Task 1` сохраняются и расширяются.

### CLI Contract

Запуск:

```bash
python -m bank_statements_parsing run --input PATH --output OUTPUT_DIR [--run-id RUN_ID]
```

Правила CLI:

- `--input` обязателен и должен указывать либо на существующий standalone `.txt`, либо на существующий `.zip`.
- `--output` обязателен и указывает на рабочий каталог MVP.
- `--run-id` опционален; если не передан, генерируется UTC timestamp вида `YYYYMMDDTHHMMSSZ`.
- директории и любые входы, кроме `.txt` и `.zip`, отклоняются с non-zero exit code.

### Source Unit Model

В этом срезе вводится понятие `source unit`.

Виды source unit:

- `plain_txt`
- `zip_txt_member`

Идентификация source unit:

- standalone `.txt`: `source_locator = <input_path>`
- `.txt` member внутри архива: `source_locator = <input_path>::<member_path>`

Правила:

- директории внутри `.zip` не считаются source units;
- не-`.txt` entries внутри `.zip` не считаются source units;
- nested directories внутри `.zip` поддерживаются штатно;
- один архив может содержать несколько `.txt`, и каждый из них обрабатывается отдельно.

### Persistent State

Состояние по-прежнему хранится локально:

```text
OUTPUT_DIR/
  state/
    files_manifest.jsonl
  runs/
    <run_id>/
      files.jsonl
      report.json
```

#### `state/files_manifest.jsonl`

Один JSON object на уникальный `file_hash` logical source unit.

Поля:

- `file_hash`
- `source_kind`
- `first_seen_run_id`
- `first_seen_at`
- `first_seen_input_path`
- `first_seen_container_path`
- `first_seen_member_path`
- `first_seen_source_locator`
- `logical_size_bytes`

Правила:

- manifest остаётся реестром уникальных logical sources;
- при повторной загрузке дубля новая запись в manifest не добавляется;
- duplicate detection выполняется только по `file_hash`;
- duplicate может совпасть между:
  - standalone `.txt` и standalone `.txt`;
  - standalone `.txt` и `.txt` member внутри `.zip`;
  - двумя разными `.txt` members в одном архиве;
  - `.txt` members из разных архивов.

#### `runs/<run_id>/files.jsonl`

Один JSON object на каждый обработанный source unit текущего запуска.

Поля:

- `run_id`
- `processed_at`
- `input_path`
- `source_kind`
- `container_path`
- `member_path`
- `source_locator`
- `file_hash`
- `logical_size_bytes`
- `status` = `new` | `duplicate`
- `duplicate_of_run_id`
- `duplicate_of_source_locator`

#### `runs/<run_id>/report.json`

Поля:

- `run_id`
- `inputs_total`
- `source_units_total`
- `new_files_count`
- `duplicate_files_count`
- `zip_members_total`
- `zip_txt_members_total`
- `zip_skipped_entries_count`
- `bytes_total`
- `wall_clock_seconds`

### Discovery Logic

Алгоритм discovery:

1. Если вход это standalone `.txt`:
   - создать один source unit вида `plain_txt`.
2. Если вход это `.zip`:
   - открыть архив;
   - перечислить entries верхнего уровня и вложенных директорий;
   - пропустить directory entries;
   - пропустить все entries, не оканчивающиеся на `.txt`;
   - для каждого `.txt` entry создать отдельный source unit вида `zip_txt_member`.

Правила discovery:

- порядок обработки zip members должен быть детерминированным;
- source units внутри одного запуска должны обрабатываться последовательно в стабильном порядке;
- если архив не содержит ни одного `.txt`, запуск завершается штатно, но с нулём source units и соответствующим `report.json`.

### Duplicate Detection Logic

Алгоритм для каждого source unit:

1. Прочитать байты source unit потоково.
2. Посчитать `file_hash = sha256(raw_bytes)`.
3. Определить `logical_size_bytes`.
4. Загрузить `state/files_manifest.jsonl` в mapping `file_hash -> manifest entry`.
5. Если `file_hash` отсутствует:
   - создать manifest entry;
   - записать entry в manifest;
   - записать run event со `status=new`;
   - увеличить `new_files_count`.
6. Если `file_hash` уже есть:
   - не изменять manifest;
   - записать run event со `status=duplicate`;
   - заполнить `duplicate_of_run_id` и `duplicate_of_source_locator` из first-seen entry;
   - увеличить `duplicate_files_count`.

Правила duplicate control:

- одинаковое содержимое под разными именами считается `duplicate`;
- одинаковое содержимое в разных member paths считается `duplicate`;
- одинаковое содержимое в standalone `.txt` и в `.zip` member считается `duplicate`;
- разные архивы с одинаковыми `.txt` members не должны создавать новые manifest entries;
- статус определяется только содержимым logical source unit.

### Module Responsibilities

- `discover.py`
  - определение source units для standalone `.txt` и `.zip`;
  - фильтрация directory entries и не-`.txt` entries;
  - стабильный порядок source units.
- `source_io.py`
  - открытие standalone `.txt`;
  - открытие `.txt` member внутри `.zip`;
  - единый интерфейс чтения байтов source unit.
- `hashing.py`
  - потоковый SHA-256 по source unit без загрузки всего источника в память.
- `state.py`
  - чтение manifest JSONL;
  - поиск записи по `file_hash`;
  - append новой записи для `new` source unit.
- `runner.py`
  - orchestration запуска;
  - обход source units;
  - сбор counters;
  - запись `files.jsonl` и `report.json`.
- `models.py`
  - структуры для manifest entry, source unit descriptor, run event и report.
- `cli.py`
  - валидация аргументов;
  - вызов `runner`.

## Test Plan

### Unit Tests

- discovery для standalone `.txt` создаёт один source unit вида `plain_txt`;
- discovery для `.zip` с несколькими `.txt` возвращает по одному source unit на каждый member;
- discovery для `.zip` с вложенной директорией корректно возвращает member paths;
- discovery пропускает directory entries и не-`.txt` entries;
- одинаковые байты дают одинаковый SHA-256 независимо от source kind;
- manifest корректно хранит `first_seen_source_locator`.

### Integration Tests

- запуск на standalone `.txt` сохраняет поведение `Task 1`:
  - первый запуск даёт `status=new`;
  - повторный запуск того же содержимого даёт `status=duplicate`.
- запуск на `.zip` с одним `.txt`:
  - создаёт один run event;
  - создаёт одну запись в manifest.
- запуск на `.zip` с несколькими `.txt`:
  - создаёт несколько run events;
  - report отражает `zip_members_total` и `zip_txt_members_total`.
- запуск на `.zip` с вложенной директорией:
  - member path сохраняется в `source_locator`;
  - обработка проходит штатно.
- запуск на `.zip`, где два разных member paths содержат одинаковые байты:
  - первый source unit получает `status=new`;
  - второй получает `status=duplicate`;
  - в manifest остаётся одна запись для этого содержимого.
- запуск standalone `.txt`, если такое же содержимое уже ранее встретилось как `.zip` member:
  - результат `duplicate`.
- запуск на `.zip` без `.txt` entries:
  - штатный exit code `0`;
  - `source_units_total = 0`;
  - manifest не изменяется.
- запуск на не-`.txt` и не-`.zip` входе:
  - non-zero exit code;
  - state и run outputs не создаются.

### Acceptance Criteria

- текущий сценарий `Task 1` не ломается;
- `.zip` с несколькими `.txt` members обрабатывается детерминированно;
- duplicate control работает одинаково для standalone `.txt` и `.txt` внутри `.zip`;
- nested directories внутри `.zip` поддерживаются;
- manifest не разрастается от одинакового содержимого в разных контейнерах и путях;
- тесты используют временные файлы и временные архивы и не зависят от `data/`.

## Assumptions

- `Task 2` по-прежнему работает только на уровне logical source units, а не документов внутри выписки;
- hash считается по байтам standalone `.txt` или по байтам конкретного `.txt` member после чтения из архива;
- container-level hash для `.zip` в этом срезе не вводится;
- runtime-only dependencies не требуются beyond stdlib;
- для тестов используется `pytest`.
