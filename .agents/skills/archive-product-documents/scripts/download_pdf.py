#!/usr/bin/env python3

import argparse
import hashlib
import ipaddress
import os
import socket
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MAX_BYTES = 100 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 60
USER_AGENT = "BlueprintGardenArchive/1.0"


@dataclass(frozen=True)
class DownloadResult:
    sha256: str
    byte_count: int
    resolved_url: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a public PDF atomically and report archive metadata."
    )
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--referer")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def validate_public_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must be a public HTTP or HTTPS URL")
    if parsed.username or parsed.password:
        raise ValueError("URL must not contain credentials")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must contain a hostname")

    normalized_hostname = hostname.rstrip(".").lower()
    if (
        normalized_hostname == "localhost"
        or normalized_hostname.endswith(".localhost")
        or normalized_hostname.endswith(".local")
    ):
        raise ValueError("URL hostname must be public")

    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as error:
        raise ValueError("URL contains an invalid port") from error

    try:
        addresses = {
            result[4][0]
            for result in socket.getaddrinfo(
                hostname, port, type=socket.SOCK_STREAM
            )
        }
    except socket.gaierror as error:
        raise ValueError(f"URL hostname could not be resolved: {hostname}") from error

    if not addresses:
        raise ValueError(f"URL hostname did not resolve: {hostname}")

    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise ValueError(
                f"URL hostname resolves to a non-public address: {address}"
            )


class PublicOnlyRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        validate_public_url(new_url)
        return super().redirect_request(
            request, file_pointer, code, message, headers, new_url
        )


def download_pdf(
    url: str,
    output: Path,
    max_bytes: int,
    timeout: float,
    replace: bool,
    referer: str | None = None,
    opener: urllib.request.OpenerDirector | None = None,
) -> DownloadResult:
    if max_bytes <= 0:
        raise ValueError("--max-bytes must be positive")
    if timeout <= 0:
        raise ValueError("--timeout must be positive")
    if output.suffix.lower() != ".pdf":
        raise ValueError("output filename must end in .pdf")
    if output.exists() and not replace:
        raise FileExistsError(f"refusing to overwrite existing file: {output}")

    validate_public_url(url)
    headers = {
        "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
        "User-Agent": USER_AGENT,
    }
    if referer:
        validate_public_url(referer)
        headers["Referer"] = referer

    output.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers=headers)
    url_opener = opener or urllib.request.build_opener(PublicOnlyRedirectHandler())
    temporary_path: Path | None = None

    try:
        with url_opener.open(request, timeout=timeout) as response:
            resolved_url = response.geturl()
            validate_public_url(resolved_url)

            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    declared_bytes = int(content_length)
                except ValueError as error:
                    raise ValueError("response has an invalid Content-Length") from error
                if declared_bytes > max_bytes:
                    raise ValueError(f"response exceeds {max_bytes} bytes")

            with tempfile.NamedTemporaryFile(
                dir=output.parent, prefix=f".{output.name}.", delete=False
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                digest = hashlib.sha256()
                byte_count = 0
                first_chunk = True

                while chunk := response.read(64 * 1024):
                    if first_chunk:
                        if not chunk.startswith(b"%PDF-"):
                            raise ValueError("response does not have a PDF signature")
                        first_chunk = False
                    byte_count += len(chunk)
                    if byte_count > max_bytes:
                        raise ValueError(f"response exceeds {max_bytes} bytes")
                    digest.update(chunk)
                    temporary_file.write(chunk)

                if first_chunk:
                    raise ValueError("response was empty")

        os.replace(temporary_path, output)
        temporary_path = None
        return DownloadResult(digest.hexdigest(), byte_count, resolved_url)
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def main() -> int:
    args = parse_args()
    try:
        result = download_pdf(
            args.url,
            args.output,
            args.max_bytes,
            args.timeout,
            args.replace,
            args.referer,
        )
    except (ValueError, OSError, urllib.error.URLError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"file={args.output}")
    print(f"bytes={result.byte_count}")
    print(f"sha256={result.sha256}")
    print(f"source_url={args.url}")
    print(f"resolved_url={result.resolved_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
