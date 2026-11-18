"""Pinned public NPTEL preview schema, observed 2026-11-17. No participation claims."""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

import httpx

from akus.catalog.schemas import Metadata

BASE_URL = "https://onlinecourses.nptel.ac.in/e-learning/api/coursepreview"
MAX_BYTES = 2_000_000


class ProviderError(Exception):
    pass


class PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "iframe", "object"}:
            self.hidden += 1
        if tag in {"div", "p", "br", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "iframe", "object"} and self.hidden:
            self.hidden -= 1
        self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def plain(value: str) -> str:
    parser = PlainText()
    parser.feed(value)
    return " ".join("".join(parser.parts).split())[:12000]


@dataclass
class Observation:
    metadata: Metadata
    digest: str
    source_url: str
    observed_at: datetime


def parse(raw: bytes, provider_id: str) -> Metadata:
    try:
        if len(raw) > MAX_BYTES:
            raise ValueError("size")
        envelope = json.loads(raw)
        if envelope["status"] != 200 or not isinstance(envelope["payload"], str):
            raise ValueError("envelope")
        payload = json.loads(envelope["payload"])
        info = payload["course_info"]
        if info["_reserved"]["context_path"] != provider_id:
            raise ValueError("offering identity")
        course = info["course"]

        def local_date(key: str) -> str | None:
            value = course.get(key)
            if value in (None, ""):
                return None
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError("date timezone")
            return parsed.astimezone(ZoneInfo("Asia/Kolkata")).date().isoformat()

        return Metadata.model_validate(
            {
                "title": plain(course["title"]),
                "description": plain(course.get("about", "")),
                "categories": course["category_name"],
                "duration_weeks": course.get("weeks"),
                "starts_on": local_date("start_date"),
                "ends_on": local_date("end_date"),
                "enrollment_ends_on": local_date("enrollment_end_date"),
                "exam_registration_ends_on": local_date("exam_registration_end_date"),
                "scheduled_exam_on": local_date("exam_date"),
            }
        )
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ProviderError("PROVIDER_SCHEMA_CHANGED") from exc


def fetch(provider_id: str) -> Observation:
    if not re.fullmatch(r"noc\d{2}_[a-z0-9]{2,30}", provider_id):
        raise ProviderError("INVALID_PROVIDER_ID")
    observed = datetime.now(UTC)  # Request start orders concurrent fetch responses.
    url = f"{BASE_URL}?course_id={provider_id}"
    try:
        with httpx.Client(timeout=10, follow_redirects=False) as client:
            with client.stream("GET", url, headers={"Accept": "application/json"}) as response:
                response.raise_for_status()
                if "application/json" not in response.headers.get("content-type", ""):
                    raise ProviderError("PROVIDER_SCHEMA_CHANGED")
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_BYTES:
                        raise ProviderError("PROVIDER_RESPONSE_TOO_LARGE")
                    chunks.append(chunk)
        raw = b"".join(chunks)
        return Observation(parse(raw, provider_id), sha256(raw).hexdigest(), url, observed)
    except httpx.HTTPError as exc:
        raise ProviderError("PROVIDER_UNAVAILABLE") from exc
