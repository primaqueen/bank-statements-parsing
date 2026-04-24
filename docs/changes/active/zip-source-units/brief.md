# Brief

## Goal

Расширить текущий Python CLI так, чтобы он принимал standalone `.txt` и `.zip`, находил внутри архива `.txt` entries и обрабатывал каждый `.txt` member как отдельный logical source unit с тем же duplicate control по содержимому.

## Why Now

Task 1 уже подтвердил минимальный manifest-based duplicate control для одного standalone `.txt`. Следующий MVP slice должен проверить source discovery и container handling до document-level parsing, чтобы не смешивать zip/source semantics с parser complexity.

## In Scope

- Поддержка input kind: standalone `.txt` и `.zip`.
- Discovery `.txt` members внутри `.zip`, включая nested directories.
- Детерминированный порядок source units.
- Duplicate detection по raw bytes каждого logical source unit.
- Расширение manifest/run/report records под `plain_txt` и `zip_txt_member`.
- Unit/integration tests на synthetic temporary files и temporary zip archives.

## Out Of Scope

- Парсинг `1CClientBankExchange`.
- Декодирование `cp1251` и других кодировок.
- Document-level outputs.
- Запись в БД.
- Parallel workers.
- Рекурсивная обработка архивов внутри архивов.
