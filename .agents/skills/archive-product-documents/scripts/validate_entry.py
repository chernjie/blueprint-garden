#!/usr/bin/env python3

import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tomllib
import urllib.parse
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path, PurePosixPath


ENTRY_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DOCUMENT_TYPE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LANGUAGE_PATTERN = re.compile(r"^[a-z]{2}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")

REQUIRED_PRODUCT_FIELDS = {
    "schema_version",
    "name",
    "brand",
    "model",
    "documents",
}
OPTIONAL_PRODUCT_FIELDS = {
    "manufacturer",
    "item_numbers",
    "upcs",
    "product_url",
    "support_url",
}
REQUIRED_DOCUMENT_FIELDS = {
    "title",
    "type",
    "file",
    "languages",
    "source_url",
    "source_type",
    "retrieved",
    "sha256",
    "bytes",
}
OPTIONAL_DOCUMENT_FIELDS = {
    "source_page_url",
    "source_filename",
    "resolved_url",
    "revision",
    "pages",
}
ALLOWED_DOCUMENT_TYPES = {
    "user-manual",
    "use-and-care-instructions",
    "installation-instructions",
    "assembly-instructions",
    "service-manual",
    "quick-start-guide",
    "parts-diagram",
    "specification-sheet",
    "warranty",
    "safety-data-sheet",
}
ALLOWED_SOURCE_TYPES = {"manufacturer", "retailer", "third-party-mirror"}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate one or more archived product-document entries."
    )
    parser.add_argument("entries", nargs="+", type=Path)
    return parser.parse_args()


def is_non_empty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_http_url(value, field_name: str, result: ValidationResult) -> None:
    if not is_non_empty_string(value):
        result.errors.append(f"{field_name} must be a non-empty string")
        return
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        result.errors.append(f"{field_name} must be an HTTP or HTTPS URL")
    if parsed.username or parsed.password:
        result.errors.append(f"{field_name} must not contain credentials")


def validate_known_fields(
    record: dict,
    required: set[str],
    optional: set[str],
    label: str,
    result: ValidationResult,
) -> None:
    missing = required - record.keys()
    unknown = record.keys() - required - optional
    if missing:
        result.errors.append(f"{label} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        result.errors.append(f"{label} has unknown fields: {', '.join(sorted(unknown))}")


def expected_document_path(entry_slug: str, document: dict) -> str | None:
    document_type = document.get("type")
    languages = document.get("languages")
    revision = document.get("revision")
    if not is_non_empty_string(document_type) or not isinstance(languages, list):
        return None

    filename = f"{entry_slug}-{document_type}"
    if revision:
        filename += f"-{revision}"
    if languages:
        filename += f"-{'-'.join(languages)}"
    return f"documents/{filename}.pdf"


def read_pdf_page_count(path: Path) -> tuple[int | None, str | None]:
    pdfinfo = shutil.which("pdfinfo")
    if not pdfinfo:
        return None, "pdfinfo is unavailable; page count was not verified"

    completed = subprocess.run(
        [pdfinfo, str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return None, f"pdfinfo could not read {path.name}"

    match = re.search(r"^Pages:\s+(\d+)\s*$", completed.stdout, re.MULTILINE)
    if not match:
        return None, f"pdfinfo did not report a page count for {path.name}"
    return int(match.group(1)), None


def validate_document(
    entry: Path,
    entry_slug: str,
    document: dict,
    index: int,
    readme: str,
    seen_files: set[str],
    seen_hashes: dict[str, str],
    result: ValidationResult,
) -> None:
    label = f"documents[{index}]"
    if not isinstance(document, dict):
        result.errors.append(f"{label} must be a TOML table")
        return

    validate_known_fields(
        document,
        REQUIRED_DOCUMENT_FIELDS,
        OPTIONAL_DOCUMENT_FIELDS,
        label,
        result,
    )
    if REQUIRED_DOCUMENT_FIELDS - document.keys():
        return

    for field_name in ("title", "type", "file", "source_url", "source_type"):
        if not is_non_empty_string(document[field_name]):
            result.errors.append(f"{label}.{field_name} must be a non-empty string")

    document_type = document["type"]
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        result.errors.append(f"{label}.type is unsupported: {document_type}")

    revision = document.get("revision")
    if revision is not None and (
        not is_non_empty_string(revision) or not DOCUMENT_TYPE_PATTERN.fullmatch(revision)
    ):
        result.errors.append(f"{label}.revision must be lowercase kebab-case")

    languages = document["languages"]
    if not isinstance(languages, list):
        result.errors.append(f"{label}.languages must be an array")
        languages = []
    else:
        if len(languages) != len(set(languages)):
            result.errors.append(f"{label}.languages contains duplicates")
        for language in languages:
            if not isinstance(language, str) or not LANGUAGE_PATTERN.fullmatch(language):
                result.errors.append(
                    f"{label}.languages values must be lowercase ISO 639-1 codes"
                )
                break

    expected_path = expected_document_path(entry_slug, document)
    relative_file = document["file"]
    pure_path = PurePosixPath(relative_file)
    if (
        pure_path.is_absolute()
        or ".." in pure_path.parts
        or pure_path.parent != PurePosixPath("documents")
    ):
        result.errors.append(f"{label}.file must be directly inside documents/")
        return
    if expected_path and relative_file != expected_path:
        result.errors.append(
            f"{label}.file does not match the naming convention: {expected_path}"
        )
    if relative_file in seen_files:
        result.errors.append(f"{label}.file is duplicated: {relative_file}")
    seen_files.add(relative_file)

    validate_http_url(document["source_url"], f"{label}.source_url", result)
    for optional_url in ("source_page_url", "resolved_url"):
        if optional_url in document:
            validate_http_url(document[optional_url], f"{label}.{optional_url}", result)

    source_type = document["source_type"]
    if source_type not in ALLOWED_SOURCE_TYPES:
        result.errors.append(f"{label}.source_type is unsupported: {source_type}")
    if source_type in {"retailer", "third-party-mirror"} and not document.get(
        "source_page_url"
    ):
        result.errors.append(
            f"{label}.source_page_url is required for {source_type} sources"
        )

    source_filename = document.get("source_filename")
    if source_filename is not None and not is_non_empty_string(source_filename):
        result.errors.append(f"{label}.source_filename must be a non-empty string")

    retrieved = document["retrieved"]
    if not isinstance(retrieved, date):
        result.errors.append(f"{label}.retrieved must be an unquoted TOML date")

    sha256 = document["sha256"]
    if not isinstance(sha256, str) or not SHA256_PATTERN.fullmatch(sha256):
        result.errors.append(f"{label}.sha256 must be a lowercase SHA-256 digest")

    byte_count = document["bytes"]
    if type(byte_count) is not int or byte_count <= 0:
        result.errors.append(f"{label}.bytes must be a positive integer")

    pages = document.get("pages")
    if pages is not None and (type(pages) is not int or pages <= 0):
        result.errors.append(f"{label}.pages must be a positive integer")

    file_path = entry / pure_path
    if not file_path.is_file():
        result.errors.append(f"{label}.file does not exist: {relative_file}")
        return

    data = file_path.read_bytes()
    if not data.startswith(b"%PDF-"):
        result.errors.append(f"{label}.file does not have a PDF signature")
    if type(byte_count) is int and len(data) != byte_count:
        result.errors.append(
            f"{label}.bytes is {byte_count}, but the file contains {len(data)} bytes"
        )

    actual_hash = hashlib.sha256(data).hexdigest()
    if isinstance(sha256, str) and actual_hash != sha256:
        result.errors.append(f"{label}.sha256 does not match the file")
    if actual_hash in seen_hashes:
        result.errors.append(
            f"{label}.file duplicates the content of {seen_hashes[actual_hash]}"
        )
    else:
        seen_hashes[actual_hash] = relative_file

    if f"({relative_file})" not in readme:
        result.errors.append(f"README.md does not link {relative_file}")

    if pages is not None:
        actual_pages, page_warning = read_pdf_page_count(file_path)
        if page_warning:
            result.warnings.append(page_warning)
        elif actual_pages != pages:
            result.errors.append(
                f"{label}.pages is {pages}, but pdfinfo reports {actual_pages}"
            )


def validate_entry(entry: Path) -> ValidationResult:
    result = ValidationResult()
    entry = entry.resolve()
    if not entry.is_dir():
        result.errors.append(f"entry directory does not exist: {entry}")
        return result
    if not ENTRY_SLUG_PATTERN.fullmatch(entry.name):
        result.errors.append("entry directory name must be lowercase kebab-case")

    metadata_path = entry / "item.toml"
    readme_path = entry / "README.md"
    if not metadata_path.is_file():
        result.errors.append("item.toml is missing")
        return result
    if not readme_path.is_file():
        result.errors.append("README.md is missing")
        readme = ""
    else:
        readme = readme_path.read_text()

    try:
        metadata = tomllib.loads(metadata_path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        result.errors.append(f"item.toml could not be parsed: {error}")
        return result
    if not isinstance(metadata, dict):
        result.errors.append("item.toml must contain a TOML table")
        return result

    validate_known_fields(
        metadata,
        REQUIRED_PRODUCT_FIELDS,
        OPTIONAL_PRODUCT_FIELDS,
        "item.toml",
        result,
    )
    if REQUIRED_PRODUCT_FIELDS - metadata.keys():
        return result

    if metadata["schema_version"] != 1:
        result.errors.append("schema_version must be 1")
    for field_name in ("name", "brand", "model"):
        if not is_non_empty_string(metadata[field_name]):
            result.errors.append(f"{field_name} must be a non-empty string")

    if "product_url" in metadata:
        validate_http_url(metadata["product_url"], "product_url", result)
    if "support_url" in metadata:
        validate_http_url(metadata["support_url"], "support_url", result)
    if "manufacturer" in metadata and not is_non_empty_string(metadata["manufacturer"]):
        result.errors.append("manufacturer must be a non-empty string")

    item_numbers = metadata.get("item_numbers")
    if item_numbers is not None and (
        not isinstance(item_numbers, list)
        or not item_numbers
        or not all(is_non_empty_string(value) for value in item_numbers)
    ):
        result.errors.append("item_numbers must be a non-empty array of strings")

    upcs = metadata.get("upcs")
    if upcs is not None and (
        not isinstance(upcs, list)
        or not upcs
        or not all(
            isinstance(value, str)
            and value.isdigit()
            and len(value) in {12, 13, 14}
            for value in upcs
        )
    ):
        result.errors.append("upcs must contain 12-, 13-, or 14-digit strings")

    documents = metadata["documents"]
    if not isinstance(documents, list) or not documents:
        result.errors.append("documents must contain at least one table")
        return result

    seen_files: set[str] = set()
    seen_hashes: dict[str, str] = {}
    for index, document in enumerate(documents):
        validate_document(
            entry,
            entry.name,
            document,
            index,
            readme,
            seen_files,
            seen_hashes,
            result,
        )

    documents_dir = entry / "documents"
    if not documents_dir.is_dir():
        result.errors.append("documents/ directory is missing")
    else:
        archived_pdfs = {
            path.relative_to(entry).as_posix()
            for path in documents_dir.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        }
        orphaned_pdfs = archived_pdfs - seen_files
        if orphaned_pdfs:
            result.errors.append(
                "documents/ contains unrecorded PDFs: "
                + ", ".join(sorted(orphaned_pdfs))
            )

    return result


def main() -> int:
    args = parse_args()
    failed = False
    for entry in args.entries:
        result = validate_entry(entry)
        for warning in result.warnings:
            print(f"warning: {entry}: {warning}", file=sys.stderr)
        for error in result.errors:
            print(f"error: {entry}: {error}", file=sys.stderr)
        if result.valid:
            print(f"valid: {entry}")
        else:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
