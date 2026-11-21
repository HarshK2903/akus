"""PDF history is private, immutable and independent of academic credit."""

import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from hashlib import sha256
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_admission import draft, setup, submit
from test_catalog import SOURCE
from test_people import login


def payload(version=1, label="first"):
    pdf = b"%PDF-1.4\nLOCAL acceptance " + label.encode() + b"\n%%EOF"
    return SOURCE | {
        "expected_version": version,
        "document_digest": sha256(pdf).hexdigest(),
        "filename": "local.pdf",
        "kind": "ACADEMIC_RELEVANCE",
        "attachment": {
            "media_type": "application/pdf",
            "base64_data": base64.b64encode(pdf).decode(),
        },
    }


def send(client, url, headers, body, key=None):
    return client.post(url, headers=headers | {"Idempotency-Key": str(key or uuid4())}, json=body)


def test_attachment_revision_manifest_replay_and_privacy(client, db, monkeypatch):
    monkeypatch.delenv("AKUS_CLAMD_SOCKET", raising=False)
    aid, h = draft(client, setup(client))
    url = f"/api/v1/applications/{aid}/attachments"
    body = payload()
    key = uuid4()
    assert client.post(url, headers={"Idempotency-Key": str(key)}, json=body).status_code == 403
    first = send(client, url, h, body, key)
    assert first.status_code == 200, first.text
    rid = first.json()["id"]
    assert send(client, url, h, body, key).json() == first.json()
    item = client.get(url).json()["items"][0]
    assert (
        item["scan"] == "QUARANTINED"
        and not item["can_download"]
        and item["digest"] == body["document_digest"]
    )
    assert "content" not in item and client.get(url + "/" + rid + "/content").status_code == 423
    login(client, "hod")
    assert client.get(url).status_code == 403
    h = login(client, "faculty")
    assert send(client, url, h, payload(1, "second") | {"previous_id": rid}).status_code == 409
    second = send(client, url, h, payload(2, "second") | {"previous_id": rid})
    assert second.status_code == 200
    newer = second.json()["id"]
    assert submit(client, aid, h).status_code == 200
    app = client.get("/api/v1/applications/" + aid).json()
    assert app["submission"]["facts"]["attachment_revision_ids"] == [newer]
    assert (
        send(
            client, url + "/" + newer + "/remove", h, SOURCE | {"expected_version": app["version"]}
        ).status_code
        == 409
    )
    corrected = send(client, url, h, payload(app["version"], "late") | {"previous_id": newer})
    assert corrected.status_code == 200
    report = client.get(url).json()
    assert {r["id"] for r in report["items"] if r["submitted"]} == {newer}
    assert {r["id"] for r in report["items"] if r["current"]} == {corrected.json()["id"]}
    for role in ("hod", "principal", "drc"):
        other = login(client, role)
        assert client.get(url).status_code == 200
        assert not client.get(url).json()["can_upload"]
        assert client.get(url + "/" + rid + "/content").status_code == 403
        assert send(client, url, other, payload()).status_code == 403
    with pytest.raises(DBAPIError), db.begin_nested():
        db.execute(
            text("UPDATE application_attachment_revisions SET reason='changed' WHERE id=:id"),
            {"id": UUID(rid)},
        )


def test_remove_draft_and_reject_malformed_evidence(client):
    aid, h = draft(client, setup(client))
    url = f"/api/v1/applications/{aid}/attachments"
    assert send(client, url, h, payload() | {"filename": "../private.pdf"}).status_code == 422
    assert send(client, url, h, payload() | {"document_digest": "0" * 64}).status_code == 422
    assert client.get(url).json()["total"] == 0
    rid = send(client, url, h, payload()).json()["id"]
    res = send(client, url + "/" + rid + "/remove", h, SOURCE | {"expected_version": 2})
    assert res.status_code == 200
    current = client.get(url).json()
    assert current["total"] == 2 and current["items"][0]["scan"] == "REMOVED"
    assert not any(x["current"] for x in current["items"])
    assert submit(client, aid, h).status_code == 200
    assert (
        client.get("/api/v1/applications/" + aid).json()["submission"]["facts"][
            "attachment_revision_ids"
        ]
        == []
    )


def test_competing_attachment_updates_leave_one_current_revision(client):
    from threading import Barrier

    aid, h = draft(client, setup(client))
    url = f"/api/v1/applications/{aid}/attachments"
    rid = send(client, url, h, payload()).json()["id"]
    barrier = Barrier(2)

    def change(label):
        barrier.wait(timeout=10)
        return send(client, url, h, payload(2, label) | {"previous_id": rid}).status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(change, ["left", "right"])) == [200, 409]
    files = client.get(url).json()
    assert files["total"] == 2 and sum(x["current"] for x in files["items"]) == 1


def test_owner_download_requires_clean_scan_and_records_access(client, db, tmp_path, monkeypatch):
    """Exercise the socket protocol with a test responder in an isolated test database."""
    import socketserver
    import struct

    from sqlalchemy import func, select

    from akus.catalog.models import AcademicEvent

    aid, h = draft(client, setup(client))
    url = f"/api/v1/applications/{aid}/attachments"
    body = payload(label="local scanner protocol fixture")
    document = base64.b64decode(body["attachment"]["base64_data"])
    received = []

    class ScannerReply(socketserver.StreamRequestHandler):
        def handle(self):
            command = self.rfile.read(2)
            if command == b"zV":
                assert self.rfile.read(7) == b"ERSION\0"
                stamp = datetime.now(UTC).strftime("%a %b %d %H:%M:%S %Y")
                self.wfile.write(f"ClamAV local/123/{stamp}\0".encode())
                return
            assert command + self.rfile.read(8) == b"zINSTREAM\0"
            chunks = []
            while size := struct.unpack("!I", self.rfile.read(4))[0]:
                chunks.append(self.rfile.read(size))
            received.append(b"".join(chunks))
            self.wfile.write(b"stream: OK\0")

    path = str(tmp_path / "scan.sock")
    monkeypatch.setenv("AKUS_CLAMD_SOCKET", path)
    with socketserver.UnixStreamServer(path, ScannerReply) as server:
        server.timeout = 5
        with ThreadPoolExecutor(max_workers=1) as executor:
            response = executor.submit(lambda: [server.handle_request() for _ in range(2)])
            saved = send(client, url, h, body)
            response.result(timeout=8)
    assert received == [document] and saved.status_code == 200
    rid = saved.json()["id"]
    content_url = f"{url}/{rid}/content"
    res = client.get(content_url)
    assert res.status_code == 200 and res.content == document
    assert res.headers["content-type"] == "application/pdf"
    assert "attachment" in res.headers["content-disposition"]
    assert res.headers["cache-control"] == "private, no-store"
    assert submit(client, aid, h).status_code == 200
    for role in ("admin", "hod", "drc", "principal"):
        login(client, role)
        assert client.get(content_url).status_code == 403
        if role == "admin":
            assert client.get(url).status_code == 403
    assert (
        db.scalar(
            select(func.count())
            .select_from(AcademicEvent)
            .where(
                AcademicEvent.entity_id == UUID(rid),
                AcademicEvent.kind == "APPLICATION_ATTACHMENT_DOWNLOAD",
            )
        )
        == 1
    )


def test_search_only_lists_current_authorized_application_files(client):
    aid, h = draft(client, setup(client))
    url = f"/api/v1/applications/{aid}/attachments"
    name = f"LOCAL-{uuid4()}.pdf"

    def hits():
        resp = client.get("/api/v1/registers/search", params={"search": name, "status": "DOCUMENT"})
        assert resp.status_code == 200, resp.text
        return [(r["id"], r["href"]) for r in resp.json()["items"]]

    rid = send(client, url, h, payload() | {"filename": name}).json()["id"]
    link = f"/app/applications/{aid}/evidence"
    assert hits() == [(rid, link)]
    login(client, "hod")
    assert hits() == []
    h = login(client, "faculty")
    removed = send(client, url + "/" + rid + "/remove", h, SOURCE | {"expected_version": 2})
    assert removed.status_code == 200 and hits() == []
    rid = send(client, url, h, payload(3) | {"filename": name}).json()["id"]
    assert submit(client, aid, h).status_code == 200
    for role in ("hod", "drc", "principal"):
        login(client, role)
        assert hits() == [(rid, link)]
    login(client, "admin")
    assert hits() == []


@pytest.mark.parametrize(
    ("verdict", "version"),
    [
        (b"stream: OK", None),
        (b"stream: OK\x00extra", None),
        (b"stream: size limit exceeded ERROR\x00", None),
        (b"stream: OK\x00", b"ClamAV 1/123/Sun Jan 01 00:00:00 2023\x00"),
        (b"stream: OK\x00", b"ClamAV 1/123/invalid\x00"),
        (b"stream: OK\x00", b"UNKNOWN COMMAND\x00"),
    ],
)
def test_incomplete_or_untrustworthy_scan_is_quarantined(tmp_path, monkeypatch, verdict, version):
    import socketserver
    import struct

    from akus.compliance.documents import inspect_pdf
    from akus.compliance.schemas import Attachment

    class Reply(socketserver.StreamRequestHandler):
        def handle(self):
            command = self.rfile.read(2)
            if command == b"zV":
                assert self.rfile.read(7) == b"ERSION\0" and version is not None
                self.wfile.write(version)
            else:
                assert command + self.rfile.read(8) == b"zINSTREAM\0"
                while size := struct.unpack("!I", self.rfile.read(4))[0]:
                    assert len(self.rfile.read(size)) == size
                self.wfile.write(verdict)

    path = str(tmp_path / "private.sock")
    monkeypatch.setenv("AKUS_CLAMD_SOCKET", path)
    body = payload()
    with socketserver.UnixStreamServer(path, Reply) as server, ThreadPoolExecutor(1) as pool:
        server.timeout = 3
        replies = pool.submit(lambda: [server.handle_request() for _ in range(1 + bool(version))])
        result = inspect_pdf(Attachment(**body["attachment"]), body["document_digest"])
        replies.result(timeout=8)
    assert result.status == "QUARANTINED"
