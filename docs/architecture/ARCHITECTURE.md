# ARCHITECTURE

## System map

```text
CLI args
  -> bank_statements_parsing/cli.py
  -> bank_statements_parsing/runner.py
  -> hashing.py / state.py / models.py
  -> output_dir/state/files_manifest.jsonl
  -> output_dir/runs/<run_id>/{files.jsonl,report.json}
```

## Current implemented slice

Текущий production behavior проекта - Task 1 duplicate control для одного standalone `.txt`.

- Один CLI run принимает один существующий `.txt` file.
- Non-file inputs и inputs без suffix `.txt` отклоняются с non-zero exit code.
- `file_hash` считается как SHA-256 по raw bytes.
- Duplicate detection зависит только от `file_hash`.
- Один и тот же content под другим именем считается `duplicate`.
- То же имя с другим content считается `new`.
- State store - локальный append-only JSONL manifest, не БД.

## Output contract

```text
<output>/
  state/
    files_manifest.jsonl
  runs/
    <run_id>/
      files.jsonl
      report.json
```

`state/files_manifest.jsonl` хранит одну запись на уникальный `file_hash`.

`runs/<run_id>/files.jsonl` хранит run event текущего input.

`runs/<run_id>/report.json` хранит run counters и elapsed time.

## Planned source-unit model

Следующий active slice вводит `source unit`:

- `plain_txt` - standalone `.txt`;
- `zip_txt_member` - отдельный `.txt` member внутри `.zip`.

До реализации active packet нельзя описывать `.zip` support как текущий CLI behavior.

## Data policy

- `data/` - локальный ignored corpus для manual/corpus smoke и исследования форматов.
- Deterministic tests не зависят от `data/`.
- Tracked fixtures возможны только отдельным решением и должны быть минимальными, обезличенными и явно описанными.

## Docs update contract

Если изменение затрагивает CLI contract, output schema, source-unit semantics, duplicate semantics, data policy или verification contours, обновляй этот файл и профильные docs в том же change set.
