import type { components } from "./schema";
import { api } from "./api";
import type { Identity } from "./api";
import { sessionCsrf } from "./session";
export type StaffPage = components["schemas"]["StaffPage"];
export type StaffDetail = components["schemas"]["StaffDetail"];
export type Department = components["schemas"]["DepartmentView"];
export type Appointment = components["schemas"]["AppointmentView"];
export type AppointmentPage = components["schemas"]["AppointmentPage"];
export type StaffCreate = components["schemas"]["StaffCreate"];
export type AppointmentCreate = components["schemas"]["AppointmentCreate"];
export function command(path: string, body: unknown, key: string) {
  return api<{ id: string }>(path, {
    method: "POST",
    headers: { "X-CSRF-Token": sessionCsrf.get(), "Idempotency-Key": key },
    body: JSON.stringify(body),
  });
}
export const officeLabel = (office: string) =>
  ({
    DRC_HEAD: "DRC Head",
    HOD: "HoD",
    ACTING_HOD: "Acting HoD",
    PRINCIPAL: "Principal",
  })[office] ?? office;
export function instant(value: string | null | undefined) {
  return value
    ? new Intl.DateTimeFormat("en-IN", {
        dateStyle: "medium",
        timeStyle: "medium",
        timeZone: "Asia/Kolkata",
      }).format(new Date(value)) + " IST"
    : "Open-ended";
}
export const commandError = (code: string) =>
  ({
    OFFICE_INTERVAL_CONFLICT:
      "This interval conflicts with an existing appointment. DRC and HoD cannot overlap for one person, even across departments. Each departmental office has one current holder.",
    STAFF_KEY_EXISTS:
      "That permanent staff key already exists. Open the existing record; do not create a duplicate identity.",
    IDEMPOTENCY_KEY_REUSED:
      "This request key belongs to different data. Return to the form and submit a new request.",
    OPTIMISTIC_LOCK_CONFLICT:
      "This appointment changed. Refresh the record before making another decision.",
    ADMIN_AUTHORITY_REQUIRED:
      "Your current records do not grant administration access. Refresh your profile.",
    OFFICE_OUTSIDE_EMPLOYMENT:
      "The appointment must fit within an existing employment episode.",
    DRC_REQUIRES_FACULTY:
      "A DRC Head must have an eligible faculty employment record.",
    AUTHORITY_POLICY_PENDING:
      "These overlapping offices require an institutional authority decision. The appointment has not been created.",
    INVALID_REQUEST:
      "Check the required fields, dates, scope and source reference.",
  })[code] ?? code.replaceAll("_", " ").toLowerCase();

// Force scoped reads to refresh when current authority changes in the shell.
export const accessKey = (actor: Identity) => [
  actor.person_id,
  actor.roles,
  actor.department_ids,
  actor.department,
  actor.applicant_eligible,
];
