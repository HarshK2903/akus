import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";

const source = {
  reason: "LOCAL_E2E synthetic academic decision",
  source_reference: "LOCAL_E2E_PHASE3",
};
async function signIn(page: Page, role: string) {
  await page.goto("/login");
  await page.getByLabel("Demo identity").selectOption(role);
  await page.getByRole("button", { name: "Enter local workspace" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    /workspace|oversight|overview/i,
  );
}
async function apiLogin(page: Page, role: string) {
  const r = await page.request.post("/api/v1/auth/demo-login", {
    data: { identity_key: role },
    headers: { Origin: process.env.AKUS_E2E_URL || "http://127.0.0.1:5173" },
  });
  expect(r.ok()).toBeTruthy();
  return (await r.json()).csrf_token as string;
}
async function post(page: Page, csrf: string, url: string, data: object) {
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
async function fixture(page: Page) {
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
async function evidence(page: Page) {
  await page
    .getByLabel("Official source reference", { exact: true })
    .fill(source.source_reference);
  await page.getByLabel("Reason for this source change").fill(source.reason);
}

test("catalog → applicant mapping intake → HoD decision → published annual quota, with scoped read oversight", async ({
  page,
}) => {
  const f = await fixture(page);
  await signIn(page, "faculty");
  await page.goto("/app/offerings/" + f.offering.id);
  await expect(
    page.getByText("Synthetic secondary", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: /Request.*mapping/i }).click();
  await expect(page.getByRole("status")).toContainText(/request/i);
  await signIn(page, "hod");
  await page.goto("/hod/topic-mappings/" + f.course.id + "/edit");
  await page.getByLabel("One primary charging topic").selectOption(f.topic.id);
  await evidence(page);
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Confirm primary topic" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Synthetic distributed systems " + f.suffix,
  );
  await page.goto("/hod/quotas/new");
  await page.getByLabel("Canonical charging topic").selectOption(f.topic.id);
  const context = await (
    await page.request.get("/api/v1/nptel/context")
  ).json();
  const year = context.years.find(
    (y: { starts_on: string }) => y.starts_on === "2026-07-01",
  );
  await page.getByLabel("Quota academic year").selectOption(year.id);
  await page.getByLabel("Maximum shared seats").fill("2");
  await page.getByLabel(/Publish this annual cap/).check();
  await evidence(page);
  await page.getByRole("button", { name: /Save quota decision/ }).click();
  await expect(
    page.getByRole("heading", { name: /PUBLISHED · 0 counted \/ 2 maximum/ }),
  ).toBeVisible();
  const quotaURL = page.url();
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: path.resolve("../../docs/qa/phase3-quota-" + width + ".png"),
      fullPage: true,
    });
  }
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await signIn(page, "principal");
  await page.goto(quotaURL);
  await expect(
    page.getByRole("heading", { name: /PUBLISHED · 0 counted/ }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Publish or revise quota" }),
  ).toHaveCount(0);
  await page.goto("/hod/topic-mappings/" + f.course.id + "/edit");
  await expect(page.getByRole("alert")).toContainText("Only the current HoD");
});

async function prepareAdmission(page: Page) {
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
async function submitApplication(
  page: Page,
  offeringId: string,
  role = "faculty",
) {
  await signIn(page, role);
  await page.goto("/app/applications/new/eligibility?offering=" + offeringId);
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

test("faculty submits, DRC then HoD approve, blocked cross-year transfer retains source until quota publication, then withdrawal releases current pool", async ({
  page,
}) => {
  const f = await prepareAdmission(page);
  const aid = await submitApplication(page, f.offering.id);
  await expect(page.getByText("Next review: DRC HEAD")).toBeVisible();
  for (const role of ["drc", "hod"]) {
    await signIn(page, role);
    await page.goto("/app/applications/" + aid);
    await page.getByLabel("Decision", { exact: true }).selectOption("APPROVE");
    await evidence(page);
    await page
      .getByLabel("I confirm this decision and its recorded rationale.")
      .check();
    await page.getByRole("button", { name: "Record review decision" }).click();
    await expect(
      page.getByText(role === "drc" ? "Next review: HOD" : "APPROVED", {
        exact: true,
      }),
    ).toBeVisible();
  }
  const admin = await apiLogin(page, "admin");
  await post(page, admin, "/admin/nptel/local-fixtures", {
    ...source,
    course_id: f.course.id,
    provider_id: f.d.provider_id,
    metadata: { ...f.d.metadata, scheduled_exam_on: "2027-07-15" },
  });
  await signIn(page, "admin");
  await page.goto("/app/offerings/" + f.offering.id);
  await evidence(page);
  await page
    .getByLabel(
      "I checked the exact course identity and official source applicability.",
    )
    .check();
  await page
    .getByRole("button", { name: /Accept.*source|Confirm.*source/i })
    .click();
  await expect(page.getByRole("status")).toContainText(/accepted|recorded/i);
  await signIn(page, "faculty");
  await page.goto("/app/applications/" + aid);
  await expect(
    page.getByText("TARGET QUOTA MISSING", { exact: true }),
  ).toBeVisible();
  const before = await (
    await page.request.get("/api/v1/applications/" + aid)
  ).json();
  expect(before.allocation.pool.id).toBe(f.pool.id);
  await signIn(page, "hod");
  const caseId = before.cases.find(
    (c: { kind: string; id: string }) => c.kind === "QUOTA_TRANSFER",
  ).id;
  await page.goto("/hod/quota-transfers/" + caseId);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Quota transfer case",
  );
  await expect(
    page.getByText("TARGET QUOTA MISSING", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await page
    .getByRole("link", { name: "Inspect or configure target annual quota →" })
    .click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Configure annual topic quota",
  );
  await page.goto("/hod/quotas/new");
  await page.getByLabel("Canonical charging topic").selectOption(f.topic.id);
  await page.getByLabel("Quota academic year").selectOption(f.nextYear.id);
  await page.getByLabel("Maximum shared seats").fill("2");
  await page.getByLabel("Publish this annual cap now").check();
  await evidence(page);
  await page.getByRole("button", { name: "Save quota decision" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Synthetic Systems",
  );
  await expect
    .poll(
      async () => {
        const a = await (
          await page.request.get("/api/v1/applications/" + aid)
        ).json();
        return a.allocation.pool.academic_year_id;
      },
      { timeout: 20000 },
    )
    .toBe(f.nextYear.id);
  await page.goto("/app/applications/" + aid + "/quota");
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: path.resolve("../../docs/qa/phase3-application-" + width + ".png"),
      fullPage: true,
    });
  }
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await signIn(page, "faculty");
  await page.goto("/app/applications/" + aid);
  await page
    .getByLabel("I have not enrolled externally in this offering.")
    .check();
  await evidence(page);
  await page.getByLabel("I confirm this withdrawal request.").check();
  await page.getByRole("button", { name: "Withdraw application" }).click();
  await expect(page.getByText("WITHDRAWN", { exact: true })).toBeVisible();
  await expect(page.getByText("RELEASED", { exact: true })).toBeVisible();
  const after = await (
    await page.request.get("/api/v1/applications/" + aid)
  ).json();
  expect(after.submission.original_pool_id).toBe(f.pool.id);
  expect(after.allocation.pool.academic_year_id).toBe(f.nextYear.id);
  expect(after.allocation.pool.occupied).toBe(0);
});

test("DRC applicant receives direct HoD route without a self-review action", async ({
  page,
}) => {
  const f = await prepareAdmission(page);
  const aid = await submitApplication(page, f.offering.id, "drc");
  await expect(page.getByText("Next review: HOD")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Record review decision" }),
  ).toHaveCount(0);
  await page.reload();
  await expect(page.getByText("Next review: HOD")).toBeVisible();
  const a = await (
    await page.request.get("/api/v1/applications/" + aid)
  ).json();
  expect(a.submission.facts.route).toEqual(["HOD"]);
  expect(a.allocation.state).toBe("HELD");
});

test("HoD authenticates one applicant hall ticket without changing another applicant in the same offering", async ({
  page,
}) => {
  const f = await prepareAdmission(page);
  const first = await submitApplication(page, f.offering.id, "faculty");
  const second = await submitApplication(page, f.offering.id, "drc");
  const hod = await apiLogin(page, "hod");
  await post(page, hod, `/departments/${f.ctx.home_department_id}/quotas`, {
    ...source,
    topic_id: f.topic.id,
    academic_year_id: f.nextYear.id,
    maximum: 2,
    publish: true,
  });
  await signIn(page, "faculty");
  await page.goto("/app/applications/" + first);
  await page.getByLabel("Claimed person-specific exam date").fill("2027-07-15");
  await page
    .getByLabel("Hall-ticket source identifier")
    .fill("LOCAL_E2E synthetic hall ticket for exact applicant");
  await page
    .getByLabel("Reason for person-specific schedule review")
    .fill("LOCAL_E2E individual date differs from global forecast");
  await page
    .getByRole("button", { name: "Record unverified schedule claim" })
    .click();
  await expect(
    page.getByText(
      "Recorded as unverified. No quota transfer or exam participation has been verified.",
    ),
  ).toBeVisible();
  await signIn(page, "hod");
  await page.goto("/app/applications/" + first);
  await page.getByLabel("Authenticated personal exam date").fill("2027-07-15");
  await page
    .getByLabel("Official archived hall-ticket reference")
    .fill("LOCAL_E2E synthetic independently reviewed hall ticket");
  await page
    .getByLabel("Official document SHA-256 digest")
    .fill("a".repeat(64));
  // Synthetic observation at a real past local instant; no future timestamp or real-user claim.
  const local = new Date(Date.now() - 120000);
  const pad = (n: number) => String(n).padStart(2, "0");
  await page
    .getByLabel("When you observed the official evidence (local time)")
    .fill(
      `${local.getFullYear()}-${pad(local.getMonth() + 1)}-${pad(local.getDate())}T${pad(local.getHours())}:${pad(local.getMinutes())}`,
    );
  await page
    .getByLabel("Hall-ticket verification rationale")
    .fill("LOCAL_E2E controlled synthetic person-specific evidence");
  await page
    .getByLabel(
      "I authenticated the official document, exact applicant, offering and scheduled date independently.",
    )
    .check();
  await page.getByRole("button", { name: "Confirm personal schedule" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Verified person-specific scheduled exam",
    }),
  ).toBeVisible();
  const a = await (
    await page.request.get("/api/v1/applications/" + first)
  ).json();
  const b = await (
    await page.request.get("/api/v1/applications/" + second)
  ).json();
  expect(a.allocation.pool.academic_year_id).toBe(f.nextYear.id);
  expect(a.personal_schedule.verification).toBe("MANUAL_HOD_AUTHENTICATED");
  expect(b.allocation.pool.id).toBe(f.pool.id);
  expect(b.personal_schedule).toBeNull();
  expect(a.annual_compliance).toBe("NOT_ASSESSED");
});

test("Admin source workspace exposes exact offerings and immutable versions; Faculty has no source maintenance form", async ({
  page,
}) => {
  const f = await fixture(page);
  await signIn(page, "admin");
  await page.getByRole("link", { name: "NPTEL provider sources" }).click();
  await page.getByLabel("Search source courses").fill(f.suffix);
  await page.getByLabel("Canonical source course").selectOption(f.course.id);
  await expect(
    page.getByRole("button", { name: "Fetch provider metadata" }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "Metadata versions", exact: true })
    .click();
  await page.getByLabel("Search source courses").fill(f.suffix);
  await expect(
    page.getByRole("link", { name: "LOCAL_" + f.suffix, exact: true }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page
    .getByRole("link", { name: "LOCAL_" + f.suffix, exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Review source observation" }),
  ).toBeVisible();
  await signIn(page, "faculty");
  await page.goto("/admin/nptel-sync");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Source administration unavailable",
  );
  await expect(
    page.getByRole("button", { name: "Fetch provider metadata" }),
  ).toHaveCount(0);
});
