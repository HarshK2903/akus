"""Explicit operator acceptance with real vendor signatures and an isolated PostgreSQL DB."""

import base64
import os
from hashlib import sha256
from uuid import uuid4

from test_admission import draft, setup
from test_application_files import payload, send
from test_people import login


def specimen(attachment):
    # A one-page PDF with a standards-compliant EmbeddedFiles entry.
    import zlib

    encoded = zlib.compress(attachment)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R /Names << /EmbeddedFiles << /Names [(test.txt) 4 0 R] >> >> >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] /Resources << >> >>",
        b"<< /Type /Filespec /F (test.txt) /EF << /F 5 0 R >> >>",
        b"<< /Type /EmbeddedFile /Filter /FlateDecode /Length %d >>\nstream\n" % len(encoded)
        + encoded
        + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.7\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    start = len(pdf)
    pdf.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n{start}\n%%EOF\n".encode())
    return bytes(pdf)


def test_real_private_evidence_scanner(client, monkeypatch):
    scanner = os.environ["AKUS_CLAMD_SOCKET"]
    aid, h = draft(client, setup(client))
    url = f"/api/v1/applications/{aid}/attachments"
    body = payload(label="benign scanner acceptance")
    pdf = base64.b64decode(body["attachment"]["base64_data"])
    # The standardized harmless EICAR test string, embedded in the submitted PDF.
    marker = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$" + b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
    marked = specimen(marker)
    detected = send(
        client,
        url,
        h,
        body
        | {
            "document_digest": sha256(marked).hexdigest(),
            "attachment": {
                "media_type": "application/pdf",
                "base64_data": base64.b64encode(marked).decode(),
            },
        },
    )
    assert detected.status_code == 422 and "DOCUMENT_SCAN_REJECTED" in detected.text
    assert client.get(url).json()["total"] == 0
    key = uuid4()
    with monkeypatch.context() as patch:
        patch.setenv("AKUS_CLAMD_SOCKET", scanner + ".unavailable")
        held = send(client, url, h, body, key)
    assert held.status_code == 200, held.text
    rid = held.json()["id"]
    assert client.get(f"{url}/{rid}/content").status_code == 423
    assert send(client, url, h, body, key).json() == held.json()
    new = send(client, url, h, body | {"expected_version": 2, "previous_id": rid})
    assert new.status_code == 200, new.text
    content = f"{url}/{new.json()['id']}/content"
    download = client.get(content)
    assert download.status_code == 200 and download.content == pdf
    assert client.get(f"{url}/{rid}/content").status_code == 423
    assert {r["scan"] for r in client.get(url).json()["items"]} == {"QUARANTINED", "CLEAN"}
    login(client, "admin")
    assert client.get(content).status_code == 403


def test_real_certificate_scan_revision_recovery(client, db, monkeypatch):
    from test_catalog import post
    from test_compliance import academic_case

    with monkeypatch.context() as outage:
        outage.delenv("AKUS_CLAMD_SOCKET")
        _, path, _, body, staff = academic_case(client, db)
    url = "/api/v1" + path
    h = login(client, staff)
    first = client.get(url).json()["events"][0]
    content = f"{url}/documents/{first['document_id']}"
    assert client.get(content).status_code == 423
    result = post(client, path + "/evidence", body | {"expected_version": 1}, h)
    assert result.status_code == 200, result.text
    second, original = client.get(url).json()["events"]
    assert original == first and second["document_id"] == first["document_id"]
    assert second["document_state"] == "CLEAN" and second["facts"]["scanner_version"].startswith(
        "ClamAV "
    )
    assert second["kind"] == "ASSERTED"
    assert client.get(content, params={"revision": first["id"]}).status_code == 423
    assert client.get(content, params={"revision": uuid4()}).status_code == 404
    params = {"revision": second["id"]}
    assert client.get(content, params=params).content == base64.b64decode(
        body["attachment"]["base64_data"]
    )
    login(client, "admin")
    assert client.get(content, params=params).status_code == 403
