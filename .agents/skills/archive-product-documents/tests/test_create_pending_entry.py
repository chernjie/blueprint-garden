#!/usr/bin/env python3

import argparse
import importlib.util
import tempfile
import tomllib
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "create_pending_entry.py"
)
SPEC = importlib.util.spec_from_file_location("create_pending_entry", SCRIPT_PATH)
assert SPEC and SPEC.loader
create_pending_entry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(create_pending_entry)


class CreatePendingEntryTests(unittest.TestCase):
    def make_args(self, items_root: Path, **overrides) -> argparse.Namespace:
        values = {
            "brand": "Rheem",
            "manufacturer": "Rheem Manufacturing Company",
            "model": "PROPH40T2 RH375-30",
            "name": "Professional Prestige ProTerra Heat Pump Water Heater",
            "product_page": "https://example.com/product",
            "items_root": items_root,
            "slug": None,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_creates_entry_inside_items_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            items_root = Path(temporary_directory) / "items"
            entry = create_pending_entry.create_entry(self.make_args(items_root))

            self.assertEqual(entry.parent, items_root.resolve())
            self.assertEqual(entry.name, "rheem-proph40t2-rh375-30")
            self.assertTrue((entry / "README.md").is_file())
            self.assertTrue((entry / "item.toml").is_file())

    def test_rejects_parent_directory_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            items_root = Path(temporary_directory) / "items"
            args = self.make_args(items_root, slug="../escaped-entry")

            with self.assertRaisesRegex(ValueError, "lowercase ASCII kebab-case"):
                create_pending_entry.create_entry(args)

            self.assertFalse((Path(temporary_directory) / "escaped-entry").exists())

    def test_rejects_absolute_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            items_root = Path(temporary_directory) / "items"
            args = self.make_args(items_root, slug="/tmp/escaped-entry")

            with self.assertRaisesRegex(ValueError, "lowercase ASCII kebab-case"):
                create_pending_entry.create_entry(args)

    def test_rejects_non_kebab_case_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            args = self.make_args(Path(temporary_directory), slug="Rheem Product")

            with self.assertRaisesRegex(ValueError, "lowercase ASCII kebab-case"):
                create_pending_entry.create_entry(args)

    def test_toml_string_escapes_newlines_and_control_characters(self) -> None:
        rendered = create_pending_entry.render_item_toml(
            brand="Brand\nName",
            manufacturer="Maker\tName",
            model='MODEL "A"',
            name="Product\rName",
            product_page="https://example.com/a\\b",
        )
        parsed = tomllib.loads(rendered)

        self.assertEqual(parsed["brand"], "Brand\nName")
        self.assertEqual(parsed["manufacturer"], "Maker\tName")
        self.assertEqual(parsed["model"], 'MODEL "A"')
        self.assertEqual(parsed["name"], "Product\rName")
        self.assertEqual(parsed["product_url"], "https://example.com/a\\b")


if __name__ == "__main__":
    unittest.main()
