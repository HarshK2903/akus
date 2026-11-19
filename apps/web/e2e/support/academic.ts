import { expect, type Page } from "@playwright/test";
export const source = {
  reason: "LOCAL_E2E synthetic academic decision",
  source_reference: "LOCAL_E2E_PHASE3",
};
export async function signIn(page: Page, role: string) {
  await page.goto("/login");
  await page.getByLabel("Demo identity").selectOption(role);
  await page.getByRole("button", { name: "Enter local workspace" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    /workspace|oversight|overview/i,
  );
}
export async function apiLogin(page: Page, role: string) {
  const r = await page.request.post("/api/v1/auth/demo-login", {
    data: { identity_key: role },
    headers: { Origin: process.env.AKUS_E2E_URL || "http://127.0.0.1:5173" },
  });
  expect(r.ok()).toBeTruthy();
  return (await r.json()).csrf_token as string;
}
export async function post(
  page: Page,
  csrf: string,
  url: string,
  data: object,
) {
  const r = await page.request.post("/api/v1" + url, {
    data,
    headers: {
      Origin: process.env.AKUS_E2E_URL || "http://127.0.0.1:5173",
      "X-CSRF-Token": csrf,
      "Idempotency-Key": crypto.randomUUID(),
    },
  });
  expect(r.ok(), await r.text()).toBeTruthy();
  return r.json();
}
export async function fixture(page: Page) {
  const csrf = await apiLogin(page, "admin");
  const suffix = Date.now().toString();
  const topic = await post(page, csrf, "/admin/nptel/topics", {
    ...source,
    code: "E2E" + suffix,
    name: "Synthetic Systems " + suffix,
  });
  const course = await post(page, csrf, "/admin/nptel/courses", {
    ...source,
    code: "E2E" + suffix,
    title: "Synthetic distributed systems " + suffix,
    description: "LOCAL/DEMO synthetic course for browser verification.",
  });
  const offering = await post(page, csrf, "/admin/nptel/local-fixtures", {
    ...source,
    course_id: course.id,
    provider_id: "LOCAL_" + suffix,
    metadata: {
      title: "Synthetic distributed systems",
      description: "LOCAL/DEMO source only",
      categories: [
        "Synthetic Systems " + suffix,
        "Synthetic secondary",
        "Synthetic third",
      ],
      duration_weeks: 12,
      starts_on: "2027-01-15",
      ends_on: "2027-04-15",
      enrollment_ends_on: "2027-01-01",
      exam_registration_ends_on: "2027-02-01",
      scheduled_exam_on: "2027-06-30",
    },
  });
  const d = await (
    await page.request.get("/api/v1/nptel/offerings/" + offering.id)
  ).json();
  await post(page, csrf, "/admin/nptel/offerings/" + offering.id + "/accept", {
    ...source,
    snapshot_id: d.observations[0].id,
    expected_version: 0,
  });
  return { topic, course, offering, suffix };
}
export async function evidence(page: Page) {
  const form = page.locator("form:visible");
  await form
    .getByLabel("Official source reference", { exact: true })
    .fill(source.source_reference);
  await form.getByLabel("Reason for this source change").fill(source.reason);
}

export async function prepareAdmission(page: Page) {
  const f = await fixture(page);
  const csrf = await apiLogin(page, "hod");
  const ctx = await (await page.request.get("/api/v1/nptel/context")).json();
  const d = await (
    await page.request.get("/api/v1/nptel/offerings/" + f.offering.id)
  ).json();
  await post(
    page,
    csrf,
    `/departments/${ctx.home_department_id}/topic-mappings/${f.course.id}`,
    {
      ...source,
      topic_id: f.topic.id,
      snapshot_id: d.snapshot_id,
      expected_version: 0,
    },
  );
  const year = ctx.years.find(
    (y: { starts_on: string }) => y.starts_on === "2026-07-01",
  );
  const nextYear = ctx.years.find(
    (y: { starts_on: string }) => y.starts_on === "2027-07-01",
  );
  const pool = await post(
    page,
    csrf,
    `/departments/${ctx.home_department_id}/quotas`,
    {
      ...source,
      topic_id: f.topic.id,
      academic_year_id: year.id,
      maximum: 2,
      publish: true,
    },
  );
  return { ...f, ctx, d, pool, nextYear };
}
export async function submitApplication(
  page: Page,
  offeringId: string,
  role = "faculty",
) {
  await signIn(page, role);
  await page.goto("/app/applications/new/eligibility?offering=" + offeringId);
  await page
    .getByLabel("Academic relevance to your teaching or discipline")
    .fill("LOCAL_E2E distributed systems teaching relevance");
  await page.getByLabel("I will select Yes for NPTEL score sharing.").check();
  await page
    .getByLabel("I have not already enrolled externally in this offering.")
    .check();
  await page
    .getByLabel("Previous attempts at this canonical course")
    .selectOption("NONE_DECLARED");
  await page
    .getByLabel(
      "I confirm these declarations and understand that evidence discrepancies require review.",
    )
    .check();
  await page.getByRole("button", { name: "Save draft for review" }).click();
  await page
    .getByRole("link", { name: "Continue to review", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review and submit", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("I confirm these source facts and declarations for submission.")
    .check();
  await page
    .getByRole("button", { name: "Submit application and reserve one seat" })
    .click();
  await expect(page.getByText("UNDER_REVIEW", { exact: true })).toBeVisible();
  return new URL(page.url()).pathname.split("/").pop()!;
}
