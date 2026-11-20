import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";
import {
  prepareAdmission,
  submitApplication,
  signIn,
} from "./support/academic";

test("faculty submits a private certificate, retrieves its pending history and opens the actual-year ledger", async ({
  page,
}) => {
  const offering = await prepareAdmission(page);
  const aid = await submitApplication(page, offering.offering.id);
  await page
    .getByRole("link", { name: "Exam and certificate dossier" })
    .click();
  const f = page.locator("form").filter({
    has: page.getByRole("heading", {
      name: "Record exam or certificate evidence",
    }),
  });
  const local = await page.evaluate(() => {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 19);
  });
  const day = new Date().toLocaleDateString("en-CA", {
    timeZone: "Asia/Kolkata",
  });
  await f.getByLabel(/Private PDF/).setInputFiles({
    name: "local-evidence.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.7\nLOCAL_E2E " + aid + "\n%%EOF"),
  });
  await f.getByLabel("Exam sitting or session").fill("LOCAL_E2E session A");
  await f.getByLabel("Actual examination date").fill(day);
  await f.getByLabel("Issuer certificate identifier").fill("LOCAL_E2E_" + aid);
  await f.getByLabel("Evidence observed at (local time)").fill(local);
  await f.getByLabel("Official source reference").fill("LOCAL_E2E archive");
  await f
    .getByLabel("Reason for this source change")
    .fill("LOCAL_E2E pending attendance record");
  await f.getByRole("button", { name: "Submit evidence for review" }).click();
  await expect(page.getByText(/Revision 1 · asserted/)).toBeVisible();
  await page.reload();
  await expect(page.getByText(/Private PDF · quarantined/)).toBeVisible();
  await page.setViewportSize({ width: 320, height: 850 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: path.resolve("../../docs/qa/phase6-certificate-mobile.png"),
    fullPage: true,
  });
  await page.goto("/app/compliance/annual");
  await expect(
    page.getByRole("heading", { name: "Assessment history" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Save current observation" }).click();
  await expect(page).toHaveURL(/snapshot=/);
  await page.reload();
  await expect(page.getByText(/Saved observation ·/)).toBeVisible();
  await page
    .getByRole("link", { name: "Subject-wise Silver", exact: true })
    .click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Subject-wise Silver",
  );
});

test("academic reports honor all five roles, preserve filters and expose service errors", async ({
  page,
}) => {
  for (const [role, section] of [
    ["drc", "/app/compliance"],
    ["hod", "/hod/reports"],
    ["principal", "/principal/reports"],
  ]) {
    await signIn(page, role);
    await page.goto(section + "/annual");
    await expect(
      page.getByRole("heading", { name: "Assessment history" }),
    ).toBeVisible();
    if (role === "principal") {
      await expect(
        page.getByRole("button", { name: "Save current observation" }),
      ).toHaveCount(0);
      await page.getByLabel("Find staff by name").fill("Mira");
      await page.reload();
      await expect(page.getByLabel("Find staff by name")).toHaveValue("Mira");
      const register = page.locator("section").filter({
        has: page.getByRole("heading", {
          name: "Annual compliance register",
          exact: true,
        }),
      });
      await expect(register.getByLabel("Reporting year")).toBeVisible();
      await register.getByRole("link").first().click();
      await expect(
        page.getByRole("link", { name: "Show all years" }),
      ).toBeVisible();
    }
    await page.goto(section + "/silver");
    await expect(
      page.getByRole("heading", { name: /Teaching subject obligations/ }),
    ).toBeVisible();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  }
  await signIn(page, "admin");
  await page.goto("/principal/reports/annual");
  await expect(page.getByRole("alert")).toBeVisible();
  await signIn(page, "faculty");
  await page.route("**/api/v1/compliance/episodes?*", (r) =>
    r.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ error: { code: "SERVICE_UNAVAILABLE" } }),
    }),
  );
  await page.goto("/app/compliance/annual");
  await expect(page.getByRole("alert")).toBeVisible();
});
