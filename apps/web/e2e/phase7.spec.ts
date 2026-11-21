import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { apiLogin, post, signIn, source } from "./support/academic";

test("Admin previews source impact and records a rehire under the existing staff identity", async ({
  page,
}) => {
  const csrf = await apiLogin(page, "admin");
  const [dept] = await (
    await page.request.get("/api/v1/people/departments")
  ).json();
  const key = "LOCAL_P7_" + crypto.randomUUID().slice(0, 8).toUpperCase();
  const person = await post(page, csrf, "/admin/staff", {
    ...source,
    staff_key: key,
    display_name: "LOCAL E2E rehire " + key,
    department_id: dept.id,
    starts_on: "2020-07-01",
    is_faculty: true,
  });
  const staff = await (
    await page.request.get("/api/v1/people/staff/" + person.id + "/sources")
  ).json();
  for (const [kind, row, extra] of [
    [
      "department",
      staff.memberships[0],
      { episode_id: staff.episodes[0].id, department_id: dept.id },
    ],
    ["employment", staff.episodes[0], { is_faculty: true }],
  ] as const) {
    await post(page, csrf, "/admin/staff/" + person.id + "/sources", {
      ...source,
      kind,
      id: row.id,
      expected_version: row.source_version,
      values: { ...extra, starts_on: "2020-07-01", ends_before: "2025-07-01" },
    });
  }
  await signIn(page, "admin");
  const url = "/admin/staff/" + person.id + "/employment";
  await page.goto(url);
  await page.getByLabel("Proposed effective end date").fill("2025-07-01");
  await page.getByRole("button", { name: "Preview impact" }).click();
  await expect(
    page.getByText("No applications in this episode."),
  ).toBeVisible();
  await page.getByLabel("Rehire start date").fill("2026-07-01");
  await page.getByLabel("New home department").selectOption(dept.id);
  await page
    .getByLabel("New employment classification")
    .selectOption("faculty");
  await page.getByLabel("Rehire order reference").fill(key);
  await page
    .getByLabel("Reason for rehire entry")
    .fill("LOCAL E2E documented reappointment");
  await page
    .getByRole("button", { name: "Record rehire", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "New employment episode and home department recorded",
  );
  await page.reload();
  const table = page.getByRole("region", {
    name: "Employment episode register",
  });
  await expect(table.getByText("2025-07-01")).toBeVisible();
  await expect(table.getByText(key)).toBeVisible();
  await signIn(page, "principal");
  expect(
    (
      await page.request.get(
        "/api/v1/admin/employment-episodes/" +
          staff.episodes[0].id +
          "/impact?effective_on=2025-07-01",
      )
    ).status(),
  ).toBe(403);
});

test("Faculty and DRC read personal employment history and follow the episode to Silver", async ({
  page,
}) => {
  for (const role of ["faculty", "drc"]) {
    await signIn(page, role);
    await page.goto("/app/history");
    await expect(
      page.getByRole("heading", { name: "Employment record", exact: true }),
    ).toBeVisible();
    const eid = await page
      .getByLabel("Employment episode", { exact: true })
      .inputValue();
    await page.goto("/app/history?episode=" + eid);
    await page.reload();
    await expect(
      page.getByLabel("Employment episode", { exact: true }),
    ).toHaveValue(eid);
    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.screenshot({
      path: "../../docs/qa/phase7-" + role + "-history-mobile.png",
    });
    await page
      .getByRole("link", { name: "Subject-wise Silver assessment" })
      .click();
    await expect(
      page.getByRole("heading", { name: "Subject-wise Silver", exact: true }),
    ).toBeVisible();
    expect(new URL(page.url()).searchParams.get("episode")).toBe(eid);
    await page.setViewportSize({ width: 1280, height: 900 });
  }
});
