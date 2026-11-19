import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";
import {
  apiLogin,
  post,
  prepareAdmission,
  signIn,
  source,
  submitApplication,
} from "./support/academic";

async function accessibility(page: Page, name: string) {
  for (const width of [320, 390, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBeTruthy();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.screenshot({
      path: path.resolve("../../docs/qa/phase5-" + name + "-" + width + ".png"),
      fullPage: true,
    });
  }
}

test("discovered enrollment chronology holds a counted seat and can be inspected by HoD and Principal", async ({
  page,
}) => {
  const f = await prepareAdmission(page);
  const id = await submitApplication(page, f.offering.id);
  for (const [role, version] of [
    ["drc", 2],
    ["hod", 3],
  ] as const) {
    await post(
      page,
      await apiLogin(page, role),
      "/applications/" + id + "/review",
      { ...source, expected_version: version, decision: "APPROVE" },
    );
  }
  const claim = {
    ...source,
    expected_version: 0,
    enrolled_on: new Date(Date.now() - 86400000).toISOString().slice(0, 10),
    observed_at: new Date().toISOString(),
    document_digest: "c".repeat(64),
  };
  await post(
    page,
    await apiLogin(page, "faculty"),
    "/applications/" + id + "/enrollment-claims",
    claim,
  );
  const csrf = await apiLogin(page, "hod");
  const app = await (
    await page.request.get("/api/v1/applications/" + id)
  ).json();
  await post(page, csrf, "/applications/" + id + "/verify-enrollment", {
    ...claim,
    claim_id: app.participation.claims[0].id,
    outcome: "VERIFIED",
    independently_authenticated: true,
  });
  await signIn(page, "hod");
  await page
    .getByRole("link", { name: "Integrity reviews", exact: true })
    .click();
  await page.getByLabel("Case status").selectOption("ALL");
  await page
    .getByRole("link", { name: new RegExp("LOCAL_" + f.suffix) })
    .click();
  const detail = page.url();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Integrity case dossier" }),
  ).toBeVisible();
  await expect(page.getByText("CONFIRMED", { exact: true })).toBeVisible();
  await page
    .getByText(/EVIDENCE RECORDED/)
    .first()
    .click();
  await expect(page.getByText("SUSPENDED", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Record case decision" }),
  ).toHaveCount(0);
  await accessibility(page, "integrity");
  await page.getByRole("link", { name: "Back to case list" }).click();
  await expect(page.getByLabel("Case status")).toHaveValue("ALL");
  await signIn(page, "principal");
  await page.goto(detail);
  await expect(page.getByText(/Recognition is suspended/)).toBeVisible();
  await apiLogin(page, "faculty");
  expect(
    (
      await page.request.get(
        "/api/v1/integrity-cases/" + new URL(detail).pathname.split("/").pop(),
      )
    ).status(),
  ).toBe(403);
});

test("HR records a sourced permanent order on a dedicated synthetic former staff episode", async ({
  page,
}) => {
  const csrf = await apiLogin(page, "admin");
  const deps = await (
    await page.request.get("/api/v1/people/departments")
  ).json();
  const key = "LOCAL_E2E_" + crypto.randomUUID().slice(0, 8).toUpperCase();
  const p = await post(page, csrf, "/admin/staff", {
    ...source,
    staff_key: key,
    display_name: "LOCAL E2E departed " + key,
    department_id: deps[0].id,
    starts_on: "2026-07-01",
    is_faculty: true,
  });
  const records = await (
    await page.request.get("/api/v1/people/staff/" + p.id + "/sources")
  ).json();
  const ep = records.episodes[0],
    member = records.memberships[0];
  for (const [kind, row, values] of [
    [
      "department",
      member,
      { episode_id: ep.id, department_id: member.department_id },
    ],
    ["employment", ep, { is_faculty: true }],
  ] as const) {
    await post(page, csrf, "/admin/staff/" + p.id + "/sources", {
      ...source,
      kind,
      id: row.id,
      expected_version: row.source_version,
      values: { ...values, starts_on: "2026-07-01", ends_before: "2026-09-01" },
    });
  }
  await signIn(page, "admin");
  await page.goto("/admin/staff/" + p.id + "/sources");
  const form = page.locator("form").filter({
    has: page.getByRole("button", { name: "Record permanent order" }),
  });
  await form
    .getByLabel("Official source reference", { exact: true })
    .fill(source.source_reference);
  await form.getByLabel("Reason for this source change").fill(source.reason);
  await form.getByLabel("Official document SHA-256").fill("d".repeat(64));
  await form
    .getByLabel("Source observed at (local time)")
    .fill("2026-09-02T12:00");
  await form.getByRole("checkbox").check();
  await form.getByRole("button", { name: "Record permanent order" }).click();
  await expect(form.getByRole("status")).toContainText(
    "Permanent order recorded",
  );
  await page.goto("/app/review-office-alerts");
  await page.getByLabel("Review office coverage").selectOption("all");
  await page.reload();
  await expect(page.getByLabel("Review office coverage")).toHaveValue("all");
  await expect(page.getByText(/^As of /)).toBeVisible();
  await signIn(page, "principal");
  await page.goto("/hod/separation-cases");
  await page.getByLabel("Case status").selectOption("RESOLVED");
  await page.reload();
  await expect(page.getByLabel("Case status")).toHaveValue("RESOLVED");
  await accessibility(page, "separation");
  await apiLogin(page, "faculty");
  expect(
    (await page.request.get("/api/v1/review-office-alerts")).status(),
  ).toBe(403);
  expect((await page.request.get("/api/v1/separation-cases")).status()).toBe(
    403,
  );
});
