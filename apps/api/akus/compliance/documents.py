"""Private PDF storage. A configured local clamd must clear the bytes before download."""

import base64
import binascii
import hashlib
import os
import socket
import struct
from datetime import UTC, datetime, timedelta
from typing import NamedTuple

from starlette.exceptions import HTTPException

from akus.compliance.schemas import Attachment


class ScanResult(NamedTuple):
    content: bytes
    status: str
    scanner_version: str | None = None


def _current_signatures(path: str) -> str | None:
    # clamd VERSION reports the daily signature timestamp in the daemon's timezone (UTC).
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(3)
        sock.connect(path)
        sock.sendall(b"zVERSION\0")
        with sock.makefile("rb") as reply:
            version = reply.read(512)
    if not version.startswith(b"ClamAV ") or not version.endswith(b"\0"):
        return None
    try:
        _, serial, stamp = version[:-1].decode("ascii").split("/")
        updated = datetime.strptime(stamp, "%a %b %d %H:%M:%S %Y").replace(tzinfo=UTC)
    except (UnicodeError, ValueError):
        return None
    if serial.isdigit() and timedelta(0) <= datetime.now(UTC) - updated <= timedelta(days=7):
        return version[:-1].decode("ascii")
    return None


def inspect_pdf(upload: Attachment, expected: str) -> ScanResult:
    try:
        raw = base64.b64decode(upload.base64_data, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(422, "INVALID_DOCUMENT_ENCODING") from exc
    if (
        len(raw) > 2 * 1024 * 1024
        or not raw.startswith(b"%PDF-")
        or not raw.rstrip().endswith(b"%%EOF")
    ):
        raise HTTPException(422, "INVALID_OR_OVERSIZE_PDF")
    if hashlib.sha256(raw).hexdigest() != expected:
        raise HTTPException(422, "DOCUMENT_DIGEST_MISMATCH")
    path = os.getenv("AKUS_CLAMD_SOCKET")
    if not path:
        return ScanResult(raw, "QUARANTINED")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(3)
            sock.connect(path)
            sock.sendall(b"zINSTREAM\x00")
            for pos in range(0, len(raw), 65536):
                chunk = raw[pos : pos + 65536]
                sock.sendall(struct.pack("!I", len(chunk)) + chunk)
            sock.sendall(b"\0\0\0\0")
            with sock.makefile("rb") as reply:
                answer = reply.read(1025)
            if answer.startswith(b"stream: ") and answer.endswith(b" FOUND\0"):
                raise HTTPException(422, "DOCUMENT_SCAN_REJECTED")
        if answer == b"stream: OK\0" and (version := _current_signatures(path)):
            return ScanResult(raw, "CLEAN", version)
    except OSError:
        return ScanResult(raw, "QUARANTINED")
    return ScanResult(raw, "QUARANTINED")
