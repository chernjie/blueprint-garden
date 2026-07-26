#!/usr/bin/env python3

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a minimal product-document archive entry for deferred completion."
    )
    parser.add_argument("--brand", required=True)
    parser.add_argument("--manufacturer", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--product-page", required=True)
    parser.add_argument(
        "--items-root",
        type=Path,
        default=Path("docs/items"),
        help="Archive items root (default: docs/items)",
    )
    parser.add_argument(
        "--slug",
        help="Optional explicit entry slug. Defaults to <brand>-<model>.",
    )
    return parser.parse_args()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_item_toml(
    *, brand: str, manufacturer: str, model: str, name: str, product_page: str
) -> str:
    lines = [
        "schema_version = 1",
        f"name = {toml_string(name)}",
        f"brand = {toml_string(brand)}",
        f"manufacturer = {toml_string(manufacturer)}",
        f"model = {toml_string(model)}",
        f"product_url = {toml_string(product_page)}",
        "",
    ]
    return "\n".join(lines)


def render_readme(
    *, brand: str, model: str, name: str, manufacturer: str, product_page: str
) -> str:
    return (
        f"# {name}\n\n"
        f"Public product record for **{brand} {model}**.\n\n"
        f"- **Brand:** {brand}\n"
        f"- **Manufacturer:** {manufacturer}\n"
        f"- **Model:** {model}\n"
        f"- **Product page:** {product_page}\n\n"
        "## Documents\n\n"
        "No documents have been archived yet. Complete this entry later with the "
        "archive-product-documents skill and its existing download and validation tools.\n"
    )


def create_entry(args: argparse.Namespace) -> Path:
    slug = args.slug or slugify(f"{args.brand}-{args.model}")
    if not slug:
        raise ValueError("entry slug is empty")

    entry = args.items_root / slug
    if entry.exists():
        raise FileExistsError(f"entry already exists: {entry}")

    entry.mkdir(parents=True)
    (entry / "item.toml").write_text(
        render_item_toml(
            brand=args.brand,
            manufacturer=args.manufacturer,
            model=args.model,
            name=args.name,
            product_page=args.product_page,
        ),
        encoding="utf-8",
    )
    (entry / "README.md").write_text(
        render_readme(
            brand=args.brand,
            manufacturer=args.manufacturer,
            model=args.model,
            name=args.name,
            product_page=args.product_page,
        ),
        encoding="utf-8",
    )
    return entry


def main() -> int:
    args = parse_args()
    try:
        entry = create_entry(args)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
