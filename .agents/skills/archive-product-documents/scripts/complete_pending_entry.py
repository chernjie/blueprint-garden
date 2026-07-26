#!/usr/bin/env python3

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find product archive entries that do not yet contain [[documents]]. "
            "Use the archive-product-documents skill to complete the reported entries."
        )
    )
    parser.add_argument(
        "entries",
        nargs="*",
        type=Path,
        help="Optional entry directories. Defaults to scanning docs/items.",
    )
    parser.add_argument(
        "--items-root",
        type=Path,
        default=Path("docs/items"),
        help="Archive items root (default: docs/items)",
    )
    parser.add_argument(
        "--validate-complete",
        action="store_true",
        help="Run validate_entry.py for entries that already contain documents.",
    )
    return parser.parse_args()


def candidate_entries(args: argparse.Namespace) -> list[Path]:
    if args.entries:
        return sorted(path.resolve() for path in args.entries)
    return sorted(path.parent.resolve() for path in args.items_root.glob("*/item.toml"))


def load_metadata(entry: Path) -> dict:
    metadata_path = entry / "item.toml"
    if not metadata_path.is_file():
        raise FileNotFoundError(f"item.toml is missing: {entry}")
    return tomllib.loads(metadata_path.read_text(encoding="utf-8"))


def validator_path() -> Path:
    return Path(__file__).with_name("validate_entry.py")


def validate(entry: Path) -> int:
    completed = subprocess.run(
        [sys.executable, str(validator_path()), str(entry)],
        check=False,
    )
    return completed.returncode


def main() -> int:
    args = parse_args()
    incomplete: list[Path] = []
    failed = False

    for entry in candidate_entries(args):
        try:
            metadata = load_metadata(entry)
        except (OSError, tomllib.TOMLDecodeError) as error:
            print(f"error: {error}", file=sys.stderr)
            failed = True
            continue

        documents = metadata.get("documents")
        if isinstance(documents, list) and documents:
            if args.validate_complete and validate(entry) != 0:
                failed = True
            continue
        incomplete.append(entry)

    if incomplete:
        print("Incomplete product-document archives:")
        for entry in incomplete:
            print(entry)
        print(
            "\nComplete these entries with the archive-product-documents skill: "
            "discover official PDFs, download them with download_pdf.py, add "
            "validator-compliant [[documents]] metadata, update README.md, and run "
            "validate_entry.py."
        )
    else:
        print("No incomplete product-document archives found.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
