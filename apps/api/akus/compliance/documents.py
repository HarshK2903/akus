"""Private PDF storage. A configured local clamd must clear the bytes before download."""

import base64
import binascii
import hashlib
import os
import socket
import struct

from starlette.exceptions import HTTPException

from akus.compliance.schemas import Attachment


def inspect_pdf(upload: Attachment, expected: str) -> tuple[bytes, str]:
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
        return raw, "QUARANTINED"
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
                answer = reply.read(1024).rstrip(b"\x00\n")
    except OSError:
        return raw, "QUARANTINED"
    if answer.endswith(b" FOUND"):
        raise HTTPException(422, "DOCUMENT_SCAN_REJECTED")
    return raw, "CLEAN" if answer == b"stream: OK" else "QUARANTINED"
