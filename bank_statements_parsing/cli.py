from __future__ import annotations

import argparse
from pathlib import Path

from .runner import run_duplicate_control


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bank-statements-parsing",
        description="Duplicate control MVP for standalone .txt files",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Process one standalone .txt file")
    run_parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to input .txt",
    )
    run_parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output directory",
    )
    run_parser.add_argument("--run-id", default=None, help="Optional run identifier")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        try:
            run_duplicate_control(
                input_path=args.input,
                output_dir=args.output,
                run_id=args.run_id,
            )
        except ValueError as exc:
            parser.exit(status=2, message=f"{exc}\n")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
