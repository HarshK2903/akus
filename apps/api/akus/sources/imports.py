"""Bounded CSV/XLSX staging. Committing revalidates every row in one transaction."""

import csv
import io
import re
from datetime import UTC, date, datetime
from hashlib import sha256
from pathlib import PurePath
from typing import Any
from uuid import UUID
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile, ZipFile

from defusedxml.common import DefusedXmlException  # type: ignore[import-untyped]
from openpyxl import load_workbook  # type: ignore[import-untyped]
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException

from akus.access import Actor
from akus.config import Settings
from akus.identity.models import InstitutionalEmail
from akus.identity.service import security_event, serialize_links
from akus.models import AcademicYear
from akus.people.models import Department, DepartmentAssignment, EmploymentEpisode, Person
from akus.people.schemas import StaffCreate
from akus.people.service import lock_command
from akus.sources.models import SourceImport, Subject, TeachingAssignment
from akus.sources.schemas import EmailFacts, EmploymentFacts, TeachingWrite
from akus.sources.service import source_context, validate_teaching

STAFF_COLUMNS = {
    "staff_key",
    "display_name",
    "department_code",
    "starts_on",
    "ends_before",
    "is_faculty",
    "email",
    "email_valid_from",
}
TEACHING_COLUMNS = {
    "external_key",
    "staff_key",
    "episode_starts_on",
    "subject_code",
    "department_code",
    "academic_year_start",
    "term",
    "starts_on",
    "ends_before",
}


def parse_file(filename: str, content: bytes) -> list[dict[str, str]]:
    if not content or len(content) > 4 * 1024 * 1024:
        raise HTTPException(413, "IMPORT_LIMIT_4_MB")
    suffix = PurePath(filename).suffix.lower()
    raw: list[list[str]] = []
    try:
        if suffix == ".csv":
            reader = csv.reader(io.StringIO(content.decode("utf-8-sig")), strict=True)
            for line in reader:
                raw.append(line)
                if len(raw) > 501:
                    raise HTTPException(422, "IMPORT_LIMIT_500_ROWS")
        elif suffix == ".xlsx":
            with ZipFile(io.BytesIO(content)) as archive:
                files = archive.infolist()
                if len(files) > 3000 or sum(f.file_size for f in files) > 20 * 1024 * 1024:
                    raise HTTPException(413, "XLSX_EXPANSION_LIMIT")
                if any(
                    "vbaproject" in f.filename.lower() or "externallinks" in f.filename.lower()
                    for f in files
                ):
                    raise HTTPException(422, "ACTIVE_WORKBOOK_CONTENT_REJECTED")
            workbook = load_workbook(
                io.BytesIO(content), read_only=True, data_only=False, keep_links=False
            )
            try:
                if len(workbook.worksheets) != 1:
                    raise HTTPException(422, "SINGLE_WORKSHEET_REQUIRED")
                sheet = workbook.worksheets[0]
                if (sheet.max_row or 0) > 501 or (sheet.max_column or 0) > 20:
                    raise HTTPException(422, "IMPORT_LIMIT_500_ROWS_20_COLUMNS")
                sheet.reset_dimensions()  # Do not trust attacker-controlled worksheet bounds.
                for row in sheet.iter_rows():
                    if len(raw) >= 501 or len(row) > 20:
                        raise HTTPException(422, "IMPORT_LIMIT_500_ROWS_20_COLUMNS")
                    line = []
                    for cell in row:
                        if cell.data_type == "f":
                            raise HTTPException(422, "SPREADSHEET_FORMULA_REJECTED")
                        value = cell.value
                        if isinstance(value, datetime):
                            value = value.date().isoformat()
                        line.append("" if value is None else str(value))
                    raw.append(line)
            finally:
                workbook.close()
        else:
            raise HTTPException(415, "CSV_OR_XLSX_REQUIRED")
    except (
        UnicodeError,
        csv.Error,
        BadZipFile,
        ValueError,
        KeyError,
        ParseError,
        DefusedXmlException,
        OSError,
    ) as exc:
        raise HTTPException(422, "INVALID_IMPORT_FILE") from exc
    if len(raw) < 2 or len(raw[0]) > 20:
        raise HTTPException(422, "HEADER_AND_DATA_REQUIRED")
    header = [h.strip() for h in raw[0]]
    if len(set(header)) != len(header) or any(not re.fullmatch(r"[a-z_]+", h) for h in header):
        raise HTTPException(422, "INVALID_OR_DUPLICATE_HEADERS")
    result = []
    for line in raw[1:]:
        if not any(c.strip() for c in line):
            continue
        if len(line) != len(header) or any(len(c) > 1000 for c in line):
            raise HTTPException(422, "ROW_SHAPE_OR_CELL_LIMIT")
        if any(c.lstrip().startswith(("=", "+", "-", "@")) for c in line):
            raise HTTPException(422, "SPREADSHEET_FORMULA_REJECTED")
        result.append(dict(zip(header, [c.strip() for c in line], strict=True)))
    if not result:
        raise HTTPException(422, "DATA_REQUIRED")
    return result


def normalize_row(
    db: Session, kind: str, row: dict[str, str], source: str, cfg: Settings
) -> dict[str, Any]:
    allowed = STAFF_COLUMNS if kind == "staff" else TEACHING_COLUMNS
    if set(row) - allowed:
        raise HTTPException(422, "UNKNOWN_COLUMNS_NO_ROLE_INFERENCE")
    department = db.scalar(select(Department).where(Department.code == row.get("department_code")))
    if not department:
        raise HTTPException(422, "DEPARTMENT_CODE_NOT_FOUND")
    if kind == "staff":
        faculty = row.get("is_faculty", "").lower()
        if faculty not in {"true", "false"}:
            raise HTTPException(422, "IS_FACULTY_MUST_BE_TRUE_OR_FALSE")
        person = StaffCreate(
            staff_key=row.get("staff_key", ""),
            display_name=row.get("display_name", ""),
            department_id=department.id,
            starts_on=row.get("starts_on", ""),
            is_faculty=faculty == "true",
            source_reference=source,
            reason="Official roster import",
        )
        if db.scalar(select(Person.id).where(Person.staff_key == person.staff_key)):
            raise HTTPException(409, "DUPLICATE_STAFF_KEY_USE_SOURCE_CORRECTION")
        episode = EmploymentFacts(
            starts_on=person.starts_on,
            ends_before=row.get("ends_before") or None,
            is_faculty=person.is_faculty,
        )
        result = person.model_dump(mode="json") | {
            "ends_before": str(episode.ends_before) if episode.ends_before else None
        }
        if row.get("email"):
            email = EmailFacts(email=row["email"], valid_from=row.get("email_valid_from", ""))
            if email.email.rsplit("@", 1)[1].lower() != (
                "example.test" if cfg.demo_enabled else "cmrit.ac.in"
            ):
                raise HTTPException(422, "EMAIL_ENVIRONMENT_BOUNDARY")
            if db.scalar(
                select(InstitutionalEmail.id).where(
                    InstitutionalEmail.normalized_email == email.email.lower(),
                    InstitutionalEmail.valid_until.is_(None),
                )
            ):
                raise HTTPException(409, "DUPLICATE_INSTITUTIONAL_EMAIL")
            result["email"] = email.model_dump(mode="json")
        return result
    person_record = db.scalar(select(Person).where(Person.staff_key == row.get("staff_key")))
    episode_record = (
        db.scalar(
            select(EmploymentEpisode).where(
                EmploymentEpisode.person_id == person_record.id,
                EmploymentEpisode.starts_on == date.fromisoformat(row.get("episode_starts_on", "")),
            )
        )
        if person_record
        else None
    )
    subject = db.scalar(select(Subject).where(Subject.code == row.get("subject_code")))
    year = db.scalar(
        select(AcademicYear).where(
            AcademicYear.starts_on == date.fromisoformat(row.get("academic_year_start", ""))
        )
    )
    if not episode_record or not subject or not year:
        raise HTTPException(422, "EPISODE_SUBJECT_OR_YEAR_NOT_FOUND")
    body = TeachingWrite(
        external_key=row.get("external_key", ""),
        episode_id=episode_record.id,
        subject_id=subject.id,
        department_id=department.id,
        academic_year_id=year.id,
        term=row.get("term", ""),
        starts_on=row.get("starts_on", ""),
        ends_before=row.get("ends_before", ""),
        source_reference=source,
        reason="Official teaching import",
    )
    validate_teaching(db, body)
    if db.scalar(
        select(TeachingAssignment.id).where(TeachingAssignment.external_key == body.external_key)
    ):
        raise HTTPException(409, "DUPLICATE_TEACHING_KEY_USE_SOURCE_CORRECTION")
    if db.scalar(
        select(TeachingAssignment.id).where(
            TeachingAssignment.episode_id == body.episode_id,
            TeachingAssignment.subject_id == body.subject_id,
            TeachingAssignment.department_id == body.department_id,
            TeachingAssignment.voided.is_(False),
            TeachingAssignment.starts_on < body.ends_before,
            TeachingAssignment.ends_before > body.starts_on,
        )
    ):
        raise HTTPException(409, "TEACHING_INTERVAL_CONFLICT")
    return body.model_dump(mode="json")


def preview(
    db: Session, kind: str, rows: list[dict[str, str]], source: str, cfg: Settings
) -> list[dict[str, Any]]:
    result, seen, emails = [], set(), set()
    intervals: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 2):
        errors: list[str] = []
        normalized: dict[str, Any] = {}
        try:
            normalized = normalize_row(db, kind, row, source, cfg)
            key = normalized["staff_key" if kind == "staff" else "external_key"]
            if key in seen:
                errors.append("DUPLICATE_KEY_IN_FILE")
            seen.add(key)
            if kind == "staff" and "email" in normalized:
                email = normalized["email"]["email"].lower()
                if email in emails:
                    errors.append("DUPLICATE_EMAIL_IN_FILE")
                emails.add(email)
            if kind == "teaching":
                for previous in intervals:
                    if (
                        all(
                            previous[k] == normalized[k]
                            for k in ("episode_id", "subject_id", "department_id")
                        )
                        and previous["starts_on"] < normalized["ends_before"]
                        and previous["ends_before"] > normalized["starts_on"]
                    ):
                        errors.append("OVERLAPPING_TEACHING_ROWS")
                intervals.append(normalized)
        except HTTPException as exc:
            errors.append(str(exc.detail))
        except (ValidationError, ValueError, TypeError):
            errors.append("INVALID_FIELDS_OR_DATE")
        result.append({"line": index, "raw": row, "normalized": normalized, "errors": errors})
    return result


def stage(
    db: Session, actor: Actor, kind: str, filename: str, content: bytes, source: str, cfg: Settings
) -> SourceImport:
    if kind not in {"staff", "teaching"} or not 3 <= len(source.strip()) <= 300:
        raise HTTPException(422, "IMPORT_KIND_AND_SOURCE_REQUIRED")
    rows = parse_file(filename, content)
    actor = lock_command(db, actor)
    content_hash = sha256(content).hexdigest()
    existing = db.scalar(
        select(SourceImport).where(
            SourceImport.kind == kind,
            SourceImport.content_hash == content_hash,
            SourceImport.source_reference == source,
        )
    )
    if existing:
        return existing
    record = SourceImport(
        actor_id=actor.person.id,
        kind=kind,
        filename=re.sub(r"[^A-Za-z0-9_.-]", "_", PurePath(filename).name)[-150:],
        content_hash=content_hash,
        source_reference=source,
        rows=preview(db, kind, rows, source, cfg),
    )
    db.add(record)
    db.flush()
    security_event(
        db,
        "SOURCE_IMPORT_STAGED",
        actor_person_id=str(actor.person.id),
        import_id=str(record.id),
        source_reference=source,
    )
    db.commit()
    return record


def commit(db: Session, actor: Actor, record_id: UUID, cfg: Settings) -> SourceImport:
    serialize_links(db)
    actor = lock_command(db, actor)
    # Serialize all import commits; direct commands still protected by unique/exclusion constraints.
    db.execute(text("SELECT pg_advisory_xact_lock(8210403)"))
    record = db.scalar(select(SourceImport).where(SourceImport.id == record_id).with_for_update())
    if not record:
        raise HTTPException(404, "NOT_FOUND")
    if record.status == "COMMITTED":
        return record
    normalized = preview(
        db, record.kind, [r["raw"] for r in record.rows], record.source_reference, cfg
    )
    record.rows = normalized
    if any(r["errors"] for r in normalized):
        record.status = "VALIDATION_FAILED"
        db.commit()  # Resumable row errors are durable; no source changes made.
        raise HTTPException(409, "IMPORT_HAS_ERRORS")
    # Lock all teaching subjects' permanent persons in a deterministic order before revalidation.
    if record.kind == "teaching":
        episode_ids = [UUID(r["normalized"]["episode_id"]) for r in normalized]
        ids = select(EmploymentEpisode.person_id).where(EmploymentEpisode.id.in_(episode_ids))
        list(
            db.scalars(
                select(Person).where(Person.id.in_(ids)).order_by(Person.id).with_for_update()
            )
        )
        normalized = preview(
            db, record.kind, [r["raw"] for r in record.rows], record.source_reference, cfg
        )
        if any(r["errors"] for r in normalized):
            record.rows, record.status = normalized, "VALIDATION_FAILED"
            db.commit()
            raise HTTPException(409, "IMPORT_HAS_ERRORS")
    source_context(db, actor, record.source_reference, f"Approved import {record.id}")
    try:
        for row in normalized:
            value = row["normalized"]
            if record.kind == "staff":
                person = Person(
                    staff_key=value["staff_key"],
                    display_name=value["display_name"],
                    source_reference=record.source_reference,
                )
                db.add(person)
                db.flush()
                episode = EmploymentEpisode(
                    person_id=person.id,
                    starts_on=date.fromisoformat(value["starts_on"]),
                    ends_before=date.fromisoformat(value["ends_before"])
                    if value["ends_before"]
                    else None,
                    is_faculty=value["is_faculty"],
                    source_reference=record.source_reference,
                )
                db.add(episode)
                db.flush()
                db.add(
                    DepartmentAssignment(
                        episode_id=episode.id,
                        department_id=UUID(value["department_id"]),
                        starts_on=episode.starts_on,
                        ends_before=episode.ends_before,
                        source_reference=record.source_reference,
                    )
                )
                if "email" in value:
                    email = EmailFacts.model_validate(value["email"])
                    db.add(
                        InstitutionalEmail(
                            person_id=person.id,
                            normalized_email=email.email.lower(),
                            source_reference=record.source_reference,
                            **email.model_dump(),
                        )
                    )
            else:
                teaching = TeachingWrite.model_validate(value)
                db.add(
                    TeachingAssignment(
                        **teaching.model_dump(exclude={"reason", "expected_version"})
                    )
                )
        record.status, record.committed_at = "COMMITTED", datetime.now(UTC)
        security_event(
            db,
            "SOURCE_IMPORT_COMMITTED",
            actor_person_id=str(actor.person.id),
            import_id=str(record.id),
            source_reference=record.source_reference,
            row_count=str(len(normalized)),
            acceptance="POLICY_PENDING:IO-02" if record.kind == "teaching" else "SOURCE_RECORDED",
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "IMPORT_SOURCE_CONFLICT_REVALIDATE") from exc
    return record
