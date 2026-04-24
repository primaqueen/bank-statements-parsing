# RUNBOOK

Этот документ описывает repeatable operational сценарии для текущего MVP.

## Preconditions

- Запускать команды из корня репозитория.
- `uv` должен быть установлен.
- Зависимости должны быть синхронизированы через:

```bash
uv sync --group dev
```

## Smoke Run

Пример запуска на одном локальном sample `.txt`:

```bash
uv run python -m bank_statements_parsing run \
  --input data/<company>/<file>.txt \
  --output /tmp/bsp-smoke-run \
  --run-id smoke-run
```

Ожидаемый результат:

- команда завершается с exit code `0`;
- создаются файлы:
  - `/tmp/bsp-smoke-run/state/files_manifest.jsonl`
  - `/tmp/bsp-smoke-run/runs/smoke-run/files.jsonl`
  - `/tmp/bsp-smoke-run/runs/smoke-run/report.json`

Проверить созданные файлы:

```bash
find /tmp/bsp-smoke-run -maxdepth 3 -type f | sort
```

Посмотреть run event:

```bash
sed -n '1,40p' /tmp/bsp-smoke-run/runs/smoke-run/files.jsonl
```

Посмотреть report:

```bash
python -m json.tool /tmp/bsp-smoke-run/runs/smoke-run/report.json
```

## Synthetic Smoke Run

Если локальный `data/` corpus недоступен:

```bash
mkdir -p /tmp/bsp-synthetic
printf '1CClientBankExchange\n' > /tmp/bsp-synthetic/input.txt

uv run python -m bank_statements_parsing run \
  --input /tmp/bsp-synthetic/input.txt \
  --output /tmp/bsp-synthetic/out \
  --run-id synthetic-smoke
```

Этот smoke проверяет CLI/output mechanics, но не заменяет corpus smoke для parser/source-IO changes.

## Duplicate Scenario

Первый запуск:

```bash
mkdir -p /tmp/bsp-duplicate-check
cp data/<company>/<file>.txt /tmp/bsp-duplicate-check/original.txt

uv run python -m bank_statements_parsing run \
  --input /tmp/bsp-duplicate-check/original.txt \
  --output /tmp/bsp-duplicate-check/out \
  --run-id run-1
```

Второй запуск того же содержимого под другим именем:

```bash
cp /tmp/bsp-duplicate-check/original.txt /tmp/bsp-duplicate-check/copy.txt

uv run python -m bank_statements_parsing run \
  --input /tmp/bsp-duplicate-check/copy.txt \
  --output /tmp/bsp-duplicate-check/out \
  --run-id run-2
```

Ожидаемое поведение:

- `run-1` получает `status = "new"`;
- `run-2` получает `status = "duplicate"`;
- в `state/files_manifest.jsonl` остаётся одна запись на это содержимое.

## Quality Checks

```bash
uv run pytest -q
uv run coverage run -m pytest -q
uv run coverage report
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run python scripts/check_docs_consistency.py
uv run python scripts/check_repo_hygiene.py
```

## Troubleshooting

### `uv: command not found`

`uv` не установлен или не доступен в `PATH`. Установите `uv` и повторите запуск из нового shell.

### `Failed to initialize cache at ~/.cache/uv`

В restricted sandbox укажите writable cache:

```bash
UV_CACHE_DIR=.uv-cache uv run pytest -q
```

### `Input path must point to a .txt file`

Текущий MVP принимает только standalone `.txt`. `.zip`, директории и любые другие suffix пока не поддерживаются.

### Нет файлов в `<output>/runs/...`

Чаще всего входной путь не прошёл валидацию. Проверьте suffix, существование файла и stderr команды.

### Почему файл под другим именем стал `duplicate`

Это ожидаемо. Duplicate detection основан только на `file_hash`, а не на имени или пути файла.

## Out of Scope

Этот runbook описывает только текущее реализованное поведение.

Сейчас вне scope:

- `.zip` archives;
- обработка нескольких source units за запуск;
- parsing `1CClientBankExchange` на уровне документов;
- запись в БД;
- workers и parallel processing.
