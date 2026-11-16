import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";

async function signIn(page: Page, identity = "admin") {
  await page.goto("/login");
  await page.getByLabel("Demo identity").selectOption(identity);
  await page.getByRole("button", { name: "Enter local workspace" }).click();
  await expect(
    page.getByRole("heading", {
      name: /Faculty workspace|DRC Head workspace|HoD department oversight|Principal institution overview|Administration workspace/,
    }),
  ).toBeVisible();
}
function istNow() {
  return new Date(Date.now() + 330 * 60_000).toISOString().slice(0, 19);
}
async function endOffice(page: Page, person: string) {
  await page.goto("/admin/appointments");
  const row = page
    .getByRole("row")
    .filter({ hasText: person })
    .filter({ has: page.getByRole("cell", { name: "current", exact: true }) });
  await row
    .getByRole("link", { name: "View appointment", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Office appointment record" }),
  ).toBeVisible();
  await page
    .getByLabel("Reason and source reference")
    .fill("LOCAL_E2E: formal end of demonstration appointment");
  await page
    .getByLabel("I confirm this source appointment must end now.")
    .check();
  await page
    .getByRole("button", { name: "End appointment now", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("Appointment ended");
}

test("Admin creates source records, appoints a DRC, ends authority and sees immutable history", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const suffix = crypto.randomUUID().slice(0, 8).toUpperCase();
  const name = `LOCAL E2E ${suffix}`;
  await signIn(page);
  await page
    .getByRole("link", { name: "Staff directory", exact: true })
    .click();
  await page.getByRole("link", { name: "Add staff record" }).click();
  await expect(
    page.getByRole("heading", { name: "Add staff record", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Permanent staff key", { exact: true })
    .fill(`E2E-${suffix}`);
  await page.getByLabel("Display name").fill(name);
  await page
    .getByLabel("Home department")
    .selectOption({ label: "Electronics · DEMO" });
  await page.getByLabel("Employment starts on").fill("2026-07-01");
  await page
    .getByLabel("Official source reference")
    .fill("LOCAL_E2E_STAFF_ORDER");
  await page
    .getByLabel("Reason for creating this record")
    .fill("Browser workflow demonstration source record");
  await page.getByRole("button", { name: "Create staff record" }).click();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  const personUrl = page.url();
  await page.reload();
  await expect(page.getByText("STAFF CREATED", { exact: true })).toBeVisible();
  await page
    .getByRole("link", { name: "Employment history", exact: true })
    .click();
  await expect(page).toHaveURL(/\/employment$/);
  await expect(page.getByRole("cell", { name: "2026-07-01" })).toBeVisible();
  await page
    .getByRole("link", { name: "Record appointment", exact: true })
    .click();
  await page.getByLabel("Office", { exact: true }).selectOption("DRC_HEAD");
  await page
    .getByLabel("Scope", { exact: true })
    .selectOption({ label: "Electronics · DEMO" });
  await page.getByLabel("Effective from (IST)", { exact: true }).fill(istNow());
  await page
    .getByLabel("Official source reference")
    .fill("LOCAL_E2E_OFFICE_ORDER");
  await page
    .getByLabel("Appointment rationale")
    .fill("Demonstrate faculty office authority with a real source command");
  await page
    .getByRole("button", { name: "Record appointment", exact: true })
    .click();
  await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  try {
    await expect(
      page.getByText("OFFICE APPOINTED", { exact: true }),
    ).toBeVisible();
  } finally {
    await endOffice(page, name);
  }
  await page.goto(personUrl);
  await expect(page.getByText("OFFICE ENDED", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "ended", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: path.resolve("../../docs/qa/phase2-completion-staff-history.png"),
    fullPage: true,
  });
  expect(errors).toEqual([]);
});

test("overlapping DRC and cross-department acting HoD is visibly rejected without losing inputs", async ({
  page,
}) => {
  await signIn(page);
  await page.goto("/admin/appointments/new");
  await page
    .getByLabel("Staff member", { exact: true })
    .selectOption({ label: "Arun Sen · DEMO-DRC" });
  await page.getByLabel("Office", { exact: true }).selectOption("ACTING_HOD");
  await page
    .getByLabel("Scope", { exact: true })
    .selectOption({ label: "Institution administration · DEMO" });
  await page.getByLabel("Effective from (IST)", { exact: true }).fill(istNow());
  await page.getByLabel("Official source reference").fill("LOCAL_E2E_CONFLICT");
  await page
    .getByLabel("Appointment rationale")
    .fill("Test rejected overlapping appointment");
  await page
    .getByRole("button", { name: "Record appointment", exact: true })
    .click();
  await expect(page.getByRole("alert")).toContainText("overlap");
  await expect(page.getByLabel("Official source reference")).toHaveValue(
    "LOCAL_E2E_CONFLICT",
  );
  await page.screenshot({
    path: path.resolve("../../docs/qa/phase2-completion-conflict.png"),
    fullPage: true,
  });
});

test("Principal reads all departments with no source write controls; Faculty cannot bypass route guards", async ({
  page,
}) => {
  await signIn(page, "principal");
  await page.goto("/people/staff");
  await expect(
    page.getByRole("link", { name: "Omar Das (acting HoD)", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Mira Rao", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Add staff record" }),
  ).toHaveCount(0);
  await page.goto("/people/appointments");
  await expect(
    page.getByRole("heading", { name: "Office appointments", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "End appointment" }),
  ).toHaveCount(0);
  await page.goto("/admin/staff/new");
  await expect(
    page.getByRole("heading", { name: "Access is not available" }),
  ).toBeVisible();
  await signIn(page, "faculty");
  await page.goto("/admin/appointments");
  await expect(
    page.getByRole("heading", { name: "Access is not available" }),
  ).toBeVisible();
  expect((await page.request.get("/api/v1/people/staff")).status()).toBe(403);
});

test("HoD sees only the office department, and rehire history retains two episodes", async ({
  page,
}) => {
  await signIn(page, "hod");
  await page.goto("/people/staff");
  await expect(
    page.getByRole("link", { name: "Mira Rao", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Omar Das (acting HoD)", exact: true }),
  ).toHaveCount(0);
  await page
    .getByLabel("Search name or permanent staff key", { exact: true })
    .fill("Tara");
  await page.reload();
  await expect(
    page.getByLabel("Search name or permanent staff key", { exact: true }),
  ).toHaveValue("Tara");
  await page.getByRole("link", { name: "Tara Bose", exact: true }).click();
  await expect(
    page
      .getByRole("region", { name: "Employment history", exact: true })
      .getByRole("row"),
  ).toHaveCount(3);
  await page.goto("/people/appointments");
  await page.getByRole("link", { name: "Arun Sen", exact: true }).click();
  await expect(
    page.getByRole("heading", {
      name: "Office appointment record",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "End appointment now" }),
  ).toHaveCount(0);
});

for (const width of [1440, 390, 320]) {
  test(`people workflows at ${width}px with accessible forms and tables`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 1000 });
    await signIn(page);
    for (const [route, title] of [
      ["/admin/staff", "Staff directory"],
      ["/admin/staff/new", "Add staff record"],
      ["/admin/appointments", "Office appointments"],
      ["/admin/appointments/new", "Record office appointment"],
    ]) {
      await page.goto(route);
      await expect(
        page.getByRole("heading", { name: title, exact: true }),
      ).toBeVisible();
      if (route.endsWith("/new"))
        await expect(
          page.getByLabel("Official source reference"),
        ).toBeVisible();
      else await expect(page.getByRole("table")).toBeVisible();
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
          `../../docs/qa/phase2-completion-${route.slice(7).replaceAll("/", "-")}-${width}.png`,
        ),
        fullPage: true,
      });
    }
  });
}

test("existing browser session gains and loses office scope from source changes", async ({
  page,
  browser,
}) => {
  await signIn(page);
  const context = await browser.newContext({
    baseURL: new URL(page.url()).origin,
  });
  const faculty = await context.newPage();
  await signIn(faculty, "faculty");
  await page.goto("/admin/appointments/new");
  await page
    .getByLabel("Find staff by name or key", { exact: true })
    .fill("Mira");
  await page
    .getByLabel("Staff member", { exact: true })
    .selectOption({ label: "Mira Rao · DEMO-FACULTY" });
  await page.getByLabel("Office", { exact: true }).selectOption("HOD");
  await page
    .getByLabel("Scope", { exact: true })
    .selectOption({ label: "Institution administration · DEMO" });
  await page.getByLabel("Effective from (IST)", { exact: true }).fill(istNow());
  await page
    .getByLabel("Official source reference")
    .fill("LOCAL_E2E_TEMPORARY_OFFICE");
  await page
    .getByLabel("Appointment rationale")
    .fill("Demonstrate current authority changes without a new login");
  await page
    .getByRole("button", { name: "Record appointment", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Mira Rao", exact: true }),
  ).toBeVisible();
  try {
    await faculty.goto("/app/profile");
    await expect(
      faculty.getByText("Current roles: FACULTY, HOD", { exact: true }),
    ).toBeVisible();
    await expect(
      faculty.getByRole("link", { name: "Staff directory", exact: true }),
    ).toBeVisible();
  } finally {
    await endOffice(page, "Mira Rao");
  }
  await faculty.reload();
  await expect(
    faculty.getByText("Current roles: FACULTY", { exact: true }),
  ).toBeVisible();
  await expect(
    faculty.getByRole("link", { name: "Staff directory", exact: true }),
  ).toHaveCount(0);
  expect((await faculty.request.get("/api/v1/people/staff")).status()).toBe(
    403,
  );
  await context.close();
});
