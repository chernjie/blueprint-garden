import hashlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import download_pdf
import validate_entry


PUBLIC_PDF_URL = "https://8.8.8.8/manual.pdf"


class FakeResponse(io.BytesIO):
    def __init__(self, data: bytes, url: str = PUBLIC_PDF_URL, headers=None):
        super().__init__(data)
        self._url = url
        self.headers = headers or {}

    def geturl(self) -> str:
        return self._url

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception, traceback):
        self.close()


class FakeOpener:
    def __init__(self, response: FakeResponse):
        self.response = response

    def open(self, request, timeout):
        return self.response


class DownloadPdfTests(unittest.TestCase):
    def test_downloads_pdf_and_reports_metadata(self):
        data = b"%PDF-1.7\npublic manual"
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "manual.pdf"
            result = download_pdf.download_pdf(
                PUBLIC_PDF_URL,
                output,
                max_bytes=1024,
                timeout=1,
                replace=False,
                opener=FakeOpener(FakeResponse(data)),
            )

            self.assertEqual(output.read_bytes(), data)
            self.assertEqual(result.byte_count, len(data))
            self.assertEqual(result.sha256, hashlib.sha256(data).hexdigest())
            self.assertEqual(result.resolved_url, PUBLIC_PDF_URL)

    def test_rejects_non_pdf_response_without_leaving_output(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "manual.pdf"
            with self.assertRaisesRegex(ValueError, "PDF signature"):
                download_pdf.download_pdf(
                    PUBLIC_PDF_URL,
                    output,
                    max_bytes=1024,
                    timeout=1,
                    replace=False,
                    opener=FakeOpener(FakeResponse(b"<html>blocked</html>")),
                )
            self.assertFalse(output.exists())

    def test_rejects_declared_oversized_response(self):
        response = FakeResponse(
            b"%PDF-1.7\n", headers={"Content-Length": "2048"}
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "manual.pdf"
            with self.assertRaisesRegex(ValueError, "exceeds"):
                download_pdf.download_pdf(
                    PUBLIC_PDF_URL,
                    output,
                    max_bytes=1024,
                    timeout=1,
                    replace=False,
                    opener=FakeOpener(response),
                )

    def test_refuses_silent_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "manual.pdf"
            output.write_bytes(b"existing")
            with self.assertRaises(FileExistsError):
                download_pdf.download_pdf(
                    PUBLIC_PDF_URL,
                    output,
                    max_bytes=1024,
                    timeout=1,
                    replace=False,
                    opener=FakeOpener(FakeResponse(b"%PDF-1.7\n")),
                )
            self.assertEqual(output.read_bytes(), b"existing")

    def test_rejects_private_initial_and_redirect_urls(self):
        with self.assertRaisesRegex(ValueError, "non-public"):
            download_pdf.validate_public_url("http://127.0.0.1/manual.pdf")

        handler = download_pdf.PublicOnlyRedirectHandler()
        with self.assertRaisesRegex(ValueError, "non-public"):
            handler.redirect_request(
                None,
                None,
                302,
                "Found",
                {},
                "http://169.254.169.254/manual.pdf",
            )

    def test_rejects_private_final_url(self):
        response = FakeResponse(
            b"%PDF-1.7\n", url="http://127.0.0.1/redirected.pdf"
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "manual.pdf"
            with self.assertRaisesRegex(ValueError, "non-public"):
                download_pdf.download_pdf(
                    PUBLIC_PDF_URL,
                    output,
                    max_bytes=1024,
                    timeout=1,
                    replace=False,
                    opener=FakeOpener(response),
                )


class ValidateEntryTests(unittest.TestCase):
    def create_entry(self, root: Path) -> Path:
        entry = root / "acme-123"
        documents = entry / "documents"
        documents.mkdir(parents=True)
        relative_file = "documents/acme-123-user-manual-en.pdf"
        pdf_data = b"%PDF-1.7\nmanual"
        (entry / relative_file).write_bytes(pdf_data)
        digest = hashlib.sha256(pdf_data).hexdigest()
        (entry / "README.md").write_text(
            "# ACME 123\n\n[User manual](documents/acme-123-user-manual-en.pdf)\n"
        )
        (entry / "item.toml").write_text(
            "\n".join(
                [
                    "schema_version = 1",
                    'name = "Product"',
                    'brand = "ACME"',
                    'model = "123"',
                    'product_url = "https://8.8.8.8/product"',
                    "",
                    "[[documents]]",
                    'title = "User Manual"',
                    'type = "user-manual"',
                    f'file = "{relative_file}"',
                    'languages = ["en"]',
                    f'source_url = "{PUBLIC_PDF_URL}"',
                    'source_type = "manufacturer"',
                    "retrieved = 2026-07-23",
                    f'sha256 = "{digest}"',
                    f"bytes = {len(pdf_data)}",
                    "",
                ]
            )
        )
        return entry

    def test_accepts_valid_entry(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            entry = self.create_entry(Path(temporary_directory))
            result = validate_entry.validate_entry(entry)
            self.assertEqual(result.errors, [])

    def test_accepts_upc_without_product_page(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            entry = self.create_entry(Path(temporary_directory))
            metadata_path = entry / "item.toml"
            metadata = metadata_path.read_text().replace(
                'product_url = "https://8.8.8.8/product"',
                'upcs = ["012345678905"]',
            )
            metadata_path.write_text(metadata)
            result = validate_entry.validate_entry(entry)
            self.assertEqual(result.errors, [])

    def test_rejects_orphaned_pdf(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            entry = self.create_entry(Path(temporary_directory))
            (entry / "documents" / "orphan.pdf").write_bytes(b"%PDF-1.7\n")
            result = validate_entry.validate_entry(entry)
            self.assertTrue(
                any("unrecorded PDFs" in error for error in result.errors),
                result.errors,
            )


if __name__ == "__main__":
    unittest.main()
