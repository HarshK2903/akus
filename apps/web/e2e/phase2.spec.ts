import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";
async function signIn(page: Page, identity = "admin") {
  await page.goto("/login");
  await page.getByLabel("Demo identity").selectOption(identity);
  await page.getByRole("button", { name: "Enter local workspace" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    /workspace|oversight|overview/i,
  );
}
async function source(
  page: Page,
  reason = "LOCAL_E2E official synthetic source",
) {
  await page
    .getByLabel("Official source reference", { exact: true })
    .fill("LOCAL_E2E_PHASE2");
  await page.getByLabel("Reason for this source change").fill(reason);
}

test("Admin imports a CSV roster, reviews rows, commits once, and corrects the source name", async ({
  page,
}) => {
  await signIn(page);
  const key = `E2E-${Date.now()}`;
  const name = `Synthetic import ${Date.now()}`;
  await page.getByRole("link", { name: "Source imports", exact: true }).click();
  await page
    .getByLabel("Official source reference", { exact: true })
    .fill(`LOCAL_E2E_${key}`);
  await page.getByLabel("CSV or XLSX file").setInputFiles({
    name: "synthetic-roster.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      `staff_key,display_name,department_code,starts_on,ends_before,is_faculty\n${key},${name},CSE,2020-07-01,,true\n`,
    ),
  });
  await page.getByRole("button", { name: "Upload and preview" }).click();
  await expect(
    page.getByRole("heading", { name: "Import preview" }),
  ).toBeVisible();
  await expect(
    page.getByText("1 rows · 0 rows with validation errors."),
  ).toBeVisible();
  await page
    .getByLabel("I confirm these are authorized official source records.")
    .check();
  await page.getByRole("button", { name: "Commit validated import" }).click();
  await expect(page.getByRole("status")).toContainText("Committed at");
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Source records committed" }),
  ).toBeVisible();
  await page.goto(`/admin/staff?q=${key}`);
  await page.getByRole("link", { name, exact: true }).click();
  await page.getByRole("link", { name: "Manage source records" }).click();
  await page.getByLabel("Official display name").fill(`${name} corrected`);
  await source(page);
  await page.getByRole("button", { name: "Save source change" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Source change recorded",
  );
  const correction = page
    .getByRole("listitem")
    .filter({ has: page.getByText("Source correction", { exact: true }) })
    .first();
  await expect(correction).toBeVisible();
  await correction.getByText("View recorded facts", { exact: true }).click();
  await expect(
    page.getByRole("definition").filter({ hasText: name }).first(),
  ).toContainText("corrected");
});

test("invalid roster rows remain visible after reload and cannot be committed", async ({
  page,
}) => {
  await signIn(page);
  await page.goto("/admin/imports");
  await page
    .getByLabel("Official source reference", { exact: true })
    .fill(`LOCAL_E2E_BAD_${Date.now()}`);
  await page.getByLabel("CSV or XLSX file").setInputFiles({
    name: "invalid-roster.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "staff_key,display_name,department_code,starts_on,is_faculty\nINVALID,Invalid synthetic,UNKNOWN,2020-07-01,true\n",
    ),
  });
  await page.getByRole("button", { name: "Upload and preview" }).click();
  await expect(
    page.getByRole("heading", { name: "Import preview", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByText("DEPARTMENT CODE NOT FOUND")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Commit validated import" }),
  ).toBeDisabled();
});

test("Admin records a canonical subject, teaching allocation and date correction with immutable history", async ({
  page,
}) => {
  await signIn(page);
  const code = `E2E${Date.now()}`;
  await page.goto("/admin/reference");
  await page.getByLabel("Stable canonical code").fill(code);
  await page
    .getByLabel("Official name", { exact: true })
    .fill(`Synthetic subject ${code}`);
  await source(page);
  await page.getByRole("button", { name: "Save official reference" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Official reference saved",
  );
  await page.goto("/admin/teaching/new");
  await page.getByLabel("Find staff by name or key").fill("DEMO-FACULTY");
  await page
    .getByLabel("Staff member", { exact: true })
    .selectOption({ label: "Mira Rao · DEMO-FACULTY" });
  await page.getByLabel("Official allocation key").fill(`LOCAL-${code}`);
  await page
    .getByLabel("Employment episode")
    .selectOption({ label: "2020-07-01 → Open-ended" });
  await page
    .getByLabel("Canonical subject")
    .selectOption({ label: `${code} · Synthetic subject ${code}` });
  await page
    .getByLabel("Teaching department")
    .selectOption({ label: "Computer Science · DEMO" });
  await page
    .getByLabel("Official academic year")
    .selectOption({ label: "2026–27" });
  await page.getByLabel("Academic term").fill("Synthetic semester 1");
  await page.getByLabel("Teaching starts on").fill("2026-07-10");
  await page.getByLabel("Teaching ends before (exclusive)").fill("2026-11-01");
  await source(page);
  await page.getByRole("button", { name: "Save teaching source" }).click();
  await expect(
    page.getByRole("heading", {
      name: `Synthetic subject ${code}`,
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByText("2028-07-10", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Correct source record" }).click();
  await page.getByLabel("Teaching starts on").fill("2026-07-20");
  await source(page, "LOCAL_E2E source corrects actual first teaching date");
  await page.getByRole("button", { name: "Save teaching source" }).click();
  await expect(page.getByText("2028-07-20", { exact: true })).toBeVisible();
  await page.reload();
  await expect(
    page.getByText("POLICY_PENDING · IO-02", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: path.resolve("../../docs/qa/phase2-completion-teaching-detail.png"),
    fullPage: true,
  });
});

for (const width of [1440, 390, 320]) {
  test(`five distinct role dashboards, responsive sources and no invented academic results at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 1000 });
    for (const [role, title] of [
      ["faculty", "Faculty workspace"],
      ["drc", "DRC Head workspace"],
      ["hod", "HoD department oversight"],
      ["principal", "Principal institution overview"],
      ["admin", "Administration workspace"],
    ]) {
      await signIn(page, role);
      await expect(
        page.getByRole("heading", { name: title, exact: true }),
      ).toBeVisible();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBeTruthy();
      expect(
        (
          await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze()
        ).violations,
      ).toEqual([]);
      await page.screenshot({
        path: path.resolve(
          `../../docs/qa/phase2-completion-${role}-${width}.png`,
        ),
        fullPage: true,
      });
    }
    for (const route of [
      "/admin/imports",
      "/admin/reference",
      "/admin/accounts",
      "/people/teaching",
    ]) {
      await page.goto(route);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBeTruthy();
      expect(
        (
          await new AxeBuilder({ page })
            .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
            .analyze()
        ).violations,
      ).toEqual([]);
      await page.screenshot({
        path: path.resolve(
          `../../docs/qa/phase2-completion-${route.split("/").at(-1)}-${width}.png`,
        ),
        fullPage: true,
      });
    }
  });
}

test("Google configuration and account recovery routes are honest; academic pages enforce role scope", async ({
  page,
}) => {
  await page.goto("/api/v1/auth/google/begin");
  await expect(
    page.getByRole("heading", { name: "Google configuration required" }),
  ).toBeVisible();
  for (const state of [
    "account-pending",
    "account-disabled",
    "duplicate-link",
    "account-not-authorized",
  ]) {
    await page.goto(`/auth/${state}`);
    await expect(
      page.getByRole("link", { name: "Return to sign-in" }),
    ).toBeVisible();
  }
  await signIn(page, "drc");
  await page.goto("/app/applications");
  await expect(
    page.getByText("Your own application will route directly to HoD."),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Submit|Approve/ }),
  ).toHaveCount(0);
  await signIn(page, "principal");
  await page.goto("/app/applications");
  await expect(
    page.getByRole("heading", { name: "NPTEL applications", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /Submit|Approve/ }),
  ).toHaveCount(0);
  await page.goto("/app/applications/new/offering");
  await expect(page.getByRole("alert")).toContainText(
    "HoD and Principal offices are NPTEL-exempt",
  );
  await page.goto("/admin/imports");
  await expect(
    page.getByRole("heading", { name: "Administration access required" }),
  ).toBeVisible();
});

test("canonical Admin reference and year routes persist changes and reject duplicate years", async ({
  page,
}) => {
  await signIn(page);
  const code = `REF${Date.now()}`;
  const alias = `synthetic alias ${code.toLowerCase()}`;
  await page.goto("/admin/academic-reference");
  await page.getByLabel("Stable canonical code").fill(code);
  await page
    .getByLabel("Official name", { exact: true })
    .fill(`Synthetic ${code}`);
  await source(page);
  await page.getByRole("button", { name: "Save official reference" }).click();
  await expect(
    page.getByRole("button", { name: `Correct ${code}`, exact: true }),
  ).toBeVisible();
  await page.getByLabel("Reference type").selectOption("alias");
  await page
    .getByLabel("Canonical subject", { exact: true })
    .selectOption({ label: `${code} · Synthetic ${code}` });
  await page.getByLabel("Alias name").fill(alias);
  await source(page);
  await page.getByRole("button", { name: "Save official reference" }).click();
  await expect(
    page.getByRole("button", { name: `Correct alias ${alias}`, exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: `Correct alias ${alias}`, exact: true })
    .click();
  await page.getByLabel("Alias name").fill(`${alias} corrected`);
  await source(page);
  await page.getByRole("button", { name: "Save official reference" }).click();
  await expect(
    page.getByRole("button", {
      name: `Correct alias ${alias} corrected`,
      exact: true,
    }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("button", {
      name: `Correct alias ${alias} corrected`,
      exact: true,
    }),
  ).toBeVisible();
  const references = await (
    await page.request.get("/api/v1/sources/reference")
  ).json();
  const latestYear = Math.max(
    ...references.years.map((year: { starts_on: string }) =>
      Number(year.starts_on.slice(0, 4)),
    ),
  );
  const starts = `${latestYear + 1}-07-01`;
  await page.goto("/admin/academic-years");
  await expect(page.getByLabel("Reference type")).toHaveValue("year");
  await page.getByLabel("Official academic year starts on").fill(starts);
  await source(page);
  await page.getByRole("button", { name: "Save official reference" }).click();
  await expect(
    page.getByRole("cell", { name: starts, exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Save official reference" }).click();
  await expect(page.getByRole("alert")).toContainText(
    /reference already exists/i,
  );
  await page.reload();
  await expect(
    page.getByRole("cell", { name: starts, exact: true }),
  ).toHaveCount(1);
  await page.goto("/admin/teaching-assignments");
  await expect(
    page.getByRole("heading", {
      name: "Teaching allocations",
      exact: true,
    }),
  ).toBeVisible();
});
