import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";
import {
  apiLogin,
  post,
  source,
  prepareAdmission,
  submitApplication,
  signIn,
} from "./support/academic";

async function fillProof(
  page: Page,
  section: ReturnType<Page["locator"]>,
  label: string,
  when: string,
) {
  await section.getByLabel(`${label} enrollment time (local time)`).fill(when);
  await section
    .getByLabel("Archived official document SHA-256")
    .fill("d".repeat(64));
  await section
    .getByLabel("Evidence observed at (local time)")
    .fill(await localNow(page));
  await fillSource(section);
}
async function fillSource(section: ReturnType<Page["locator"]>) {
  await section
    .getByLabel("Official source reference", { exact: true })
    .fill("LOCAL_E2E_OFFICIAL_ARCHIVE");
  await section
    .getByLabel("Reason for this source change")
    .fill("LOCAL_E2E independent synthetic document finding");
}
async function localNow(page: Page) {
  return page.evaluate(() => {
    const d = new Date();
    const p = (n: number) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
  });
}

test("saved draft resumes, preserves revisions, then enrollment verification and Q04 withdrawal release the seat", async ({
  page,
}) => {
  const f = await prepareAdmission(page);
  await signIn(page, "faculty");
  await page.goto(
    `/app/applications/new/eligibility?offering=${f.offering.id}`,
  );
  await page
    .getByLabel("Academic relevance to your teaching or discipline")
    .fill("LOCAL_E2E initial teaching relevance");
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
  await expect(page).toHaveURL(/new\/evidence\?draft=/);
  const aid = new URL(page.url()).searchParams.get("draft")!;
  await page.reload();
  await page.getByRole("link", { name: "2. Eligibility", exact: true }).click();
  await expect(
    page.getByLabel("Academic relevance to your teaching or discipline"),
  ).toHaveValue("LOCAL_E2E initial teaching relevance");
  await page
    .getByLabel("Academic relevance to your teaching or discipline")
    .fill("LOCAL_E2E revised teaching alignment preserved");
  await page.getByRole("button", { name: "Save draft for review" }).click();
  await page
    .getByRole("link", { name: "Continue to review", exact: true })
    .click();
  const before = await (
    await page.request.get(`/api/v1/applications/${aid}`)
  ).json();
  expect(before.draft_revisions).toHaveLength(2);
  expect(before.allocation).toBeNull();
  await page
    .getByLabel("I confirm these source facts and declarations for submission.")
    .check();
  await page
    .getByRole("button", { name: "Submit application and reserve one seat" })
    .click();
  await expect(page).toHaveURL(`/app/applications/${aid}`);
  await page.waitForTimeout(1100);
  const when = await localNow(page);
  const evidence = page.locator("section").filter({
    has: page.getByRole("heading", {
      name: "External enrollment evidence",
      exact: true,
    }),
  });
  await evidence
    .getByText("Record or correct enrollment evidence", { exact: true })
    .click();
  await fillProof(page, evidence, "Claimed", when);
  await evidence.getByRole("checkbox").check();
  await evidence
    .getByRole("button", { name: "Record enrollment assertion" })
    .click();
  await expect(evidence.getByRole("status")).toContainText(
    "Assertion recorded",
  );
  await signIn(page, "hod");
  await page.goto(`/app/applications/${aid}/evidence`);
  const finding = page.locator("section").filter({
    has: page.getByRole("heading", {
      name: "Authenticate enrollment chronology",
      exact: true,
    }),
  });
  await fillProof(page, finding, "Official", when);
  await finding
    .getByLabel("Enrollment verification finding")
    .selectOption("VERIFIED");
  await finding.getByRole("checkbox").check();
  await finding
    .getByRole("button", { name: "Record enrollment finding" })
    .click();
  await expect(
    page.getByText("HoD verified submission first", { exact: true }),
  ).toBeVisible();
  await signIn(page, "faculty");
  await page.goto(`/app/applications/${aid}`);
  const request = page.locator("section").filter({
    has: page.getByRole("heading", {
      name: "Request withdrawal after enrollment",
      exact: true,
    }),
  });
  await fillSource(request);
  await request.getByRole("checkbox").check();
  await request
    .getByRole("button", { name: "Request HoD withdrawal decision" })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Pending HoD withdrawal request",
      exact: true,
    }),
  ).toBeVisible();
  await signIn(page, "hod");
  await page.goto(`/app/applications/${aid}`);
  const decision = page.locator("section").filter({
    has: page.getByRole("heading", {
      name: "Pending HoD withdrawal request",
      exact: true,
    }),
  });
  await decision
    .getByLabel("Withdrawal request decision")
    .selectOption("AUTHORIZE");
  await fillSource(decision);
  await decision.getByRole("checkbox").check();
  await decision
    .getByRole("button", { name: "Record withdrawal decision" })
    .click();
  await expect(page.getByText("WITHDRAWN", { exact: true })).toBeVisible();
  const after = await (
    await page.request.get(`/api/v1/applications/${aid}`)
  ).json();
  expect(after.allocation.state).toBe("RELEASED");
  expect(after.allocation.pool.occupied).toBe(0);
  expect(
    after.ledger.filter(
      (r: { kind: string }) => r.kind === "HOD_WITHDRAW_RELEASE",
    ),
  ).toHaveLength(1);
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    await page.screenshot({
      path: path.resolve(`../../docs/qa/phase4-participation-${width}.png`),
      fullPage: true,
    });
  }
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test("an enrollment assertion does not authorize approval or private cross-person access", async ({
  page,
}) => {
  const f = await prepareAdmission(page);
  const aid = await submitApplication(page, f.offering.id);
  await page.waitForTimeout(1100);
  const section = page.locator("section").filter({
    has: page.getByRole("heading", {
      name: "External enrollment evidence",
      exact: true,
    }),
  });
  await section
    .getByText("Record or correct enrollment evidence", { exact: true })
    .click();
  await fillProof(page, section, "Claimed", await localNow(page));
  await section.getByRole("checkbox").check();
  await section
    .getByRole("button", { name: "Record enrollment assertion" })
    .click();
  await expect(section.getByRole("status")).toBeVisible();
  await signIn(page, "drc");
  await page.goto(`/drc/reviews/${aid}`);
  const review = page
    .locator("form")
    .filter({ has: page.getByLabel("Decision", { exact: true }) });
  await review.getByLabel("Decision", { exact: true }).selectOption("APPROVE");
  await fillSource(review);
  await review.getByRole("checkbox").check();
  await review.getByRole("button", { name: "Record review decision" }).click();
  await expect(review.getByRole("alert")).toContainText(
    /verified enrollment chronology/i,
  );
  await expect(page.getByText("UNDER_REVIEW", { exact: true })).toBeVisible();
  await signIn(page, "acting-hod");
  expect((await page.request.get(`/api/v1/applications/${aid}`)).status()).toBe(
    403,
  );
});

test("an applicant reports a prior run, the current HoD verifies it, and a later certificate correction blocks repeat admission", async ({
  page,
}) => {
  const f = await prepareAdmission(page);
  const admin = await apiLogin(page, "admin");
  const old = await post(page, admin, "/admin/nptel/local-fixtures", {
    ...source,
    course_id: f.course.id,
    provider_id: "LOCAL_PRIOR_" + f.suffix,
    metadata: {
      ...f.d.metadata,
      starts_on: "2025-01-10",
      ends_on: "2025-04-10",
      enrollment_ends_on: "2025-01-01",
      exam_registration_ends_on: "2025-02-01",
      scheduled_exam_on: "2025-04-20",
    },
  });
  await signIn(page, "faculty");
  await page.goto("/app/offerings/" + old.id);
  await page.getByRole("link", { name: "Report a prior attempt" }).click();
  const report = page.locator("form").filter({
    has: page.getByRole("heading", { name: "Request outcome verification" }),
  });
  await report
    .getByLabel("Reported prior result")
    .selectOption("NO_VALID_CERT");
  await report.getByLabel("Archived document SHA-256").fill("a".repeat(64));
  await report
    .getByLabel("Evidence observed at (local time)")
    .fill(await localNow(page));
  await fillSource(report);
  await report
    .getByRole("button", { name: "Send evidence for review" })
    .click();
  await expect(
    page.getByText("Awaiting conclusive verification", { exact: true }),
  ).toBeVisible();
  const id = new URL(page.url()).pathname.split("/").pop();
  await signIn(page, "hod");
  await page
    .getByRole("link", { name: "Prior-result verification", exact: true })
    .click();
  await page
    .getByLabel("Search course, offering or applicant")
    .fill("LOCAL_PRIOR_" + f.suffix);
  await page.getByLabel("Sort attempts").selectOption("oldest");
  await page
    .getByRole("link", { name: new RegExp("LOCAL_PRIOR_" + f.suffix) })
    .click();
  await expect
    .poll(() => new URL(page.url()).pathname)
    .toBe("/hod/outcome-verifications/" + id);
  await expect
    .poll(() => new URL(page.url()).searchParams.get("search"))
    .toBe("LOCAL_PRIOR_" + f.suffix);
  await page.reload();
  const decide = page.locator("form").filter({
    has: page.getByRole("heading", { name: "Record independent finding" }),
  });
  async function finding(value: string) {
    await decide.getByLabel("HoD outcome finding").selectOption(value);
    await decide.getByLabel("Official result date").fill("2025-04-30");
    await decide
      .getByLabel("Archived document SHA-256")
      .fill((value === "NO_VALID_CERT" ? "b" : "c").repeat(64));
    await decide
      .getByLabel("Evidence observed at (local time)")
      .fill(await localNow(page));
    await fillSource(decide);
    await decide
      .getByLabel("I independently checked the person and exact offering.")
      .check();
    await decide
      .getByLabel("The official result conclusively establishes this outcome.")
      .check();
    await decide.getByRole("button", { name: "Record finding" }).click();
  }
  await finding("NO_VALID_CERT");
  await expect(
    page.getByText("No certificate verified", { exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: path.resolve("../../docs/qa/phase4-prior-outcome-390.png"),
    fullPage: true,
  });
  await page.setViewportSize({ width: 1280, height: 900 });
  const aid = await submitApplication(page, f.offering.id);
  await signIn(page, "hod");
  await page.goto("/hod/outcome-verifications/" + id);
  await finding("VALID_CERT");
  await expect(
    page.getByText("Repeat prohibited", { exact: true }),
  ).toBeVisible();
  await signIn(page, "drc");
  await page.goto("/drc/reviews/" + aid);
  const review = page
    .locator("form")
    .filter({ has: page.getByLabel("Decision", { exact: true }) });
  await fillSource(review);
  await review.getByRole("checkbox").check();
  await review.getByRole("button", { name: "Record review decision" }).click();
  await expect(review.getByRole("alert")).toContainText(/repeat prohibited/i);
  await expect(page.getByText("UNDER_REVIEW", { exact: true })).toBeVisible();
});
