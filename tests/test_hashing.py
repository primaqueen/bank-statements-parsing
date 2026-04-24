from __future__ import annotations

from pathlib import Path

from bank_statements_parsing.hashing import sha256_file


def test_equal_bytes_produce_same_hash(tmp_path: Path) -> None:
    left = tmp_path / "left.txt"
    right = tmp_path / "right.txt"
    payload = b"same-content\n"
    left.write_bytes(payload)
    right.write_bytes(payload)

    assert sha256_file(left) == sha256_file(right)


def test_different_bytes_produce_different_hashes(tmp_path: Path) -> None:
    left = tmp_path / "left.txt"
    right = tmp_path / "right.txt"
    left.write_bytes(b"one\n")
    right.write_bytes(b"two\n")

    assert sha256_file(left) != sha256_file(right)
