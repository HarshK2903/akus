import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";
const screenshotDir = path.resolve("../../docs/qa");
test("sign-in, DB-backed navigation, reload, policy search, logout and denied deep link", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/app/profile");
  await expect(page).toHaveURL(/\/login(?:\?|$)/);
  await expect(
    page.getByRole("button", { name: "Continue with Google" }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Enter local workspace" }).click();
  await expect(
    page.getByRole("heading", {
      name: /Faculty workspace|DRC Head workspace|HoD department oversight|Principal institution overview|Administration workspace/,
    }),
  ).toBeVisible();
  await page
    .getByRole("link", { name: "System connections & academic calendar" })
    .click();
  await expect(page.getByRole("cell", { name: "2026–27" })).toBeVisible();
  await page
    .getByRole("link", { name: "Profile & access", exact: true })
    .click();
  await page.reload();
  await expect(
    page.getByText("Mira Rao", { exact: true }).last(),
  ).toBeVisible();
  await page.getByRole("link", { name: "Policy guide", exact: true }).click();
  await page.getByLabel("Find a policy or term").fill("P-51");
  await expect(page.getByText("Policy pending", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Find a policy or term")).toHaveValue("P-51");
  for (const code of ["IO-02", "P-54"]) {
    await page.getByLabel("Find a policy or term").fill(code);
    await expect(page.getByRole("article")).toHaveCount(1);
    await expect(page.getByRole("article")).toContainText("Policy pending");
    await expect(page.getByRole("article")).toContainText(code);
  }
  await page.goto("/hod/home");
  await expect(
    page.getByRole("heading", { name: "Access is not available" }),
  ).toBeVisible();
  await page.goto("/app/profile");
  await page
    .getByRole("button", { name: "Sign out", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(/\/login(?:\?|$)/);
  await page.goto("/app/profile");
  await expect(page).toHaveURL(/\/login(?:\?|$)/);
  expect(errors).toEqual([]);
});
for (const width of [1440, 1024, 768, 390, 320]) {
  test(`responsive foundation at ${width}px with accessibility`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 1000 });
    await page.goto("/login");
    await page.getByRole("button", { name: "Enter local workspace" }).click();
    await page
      .getByRole("link", { name: "System connections & academic calendar" })
      .click();
    await expect(page.getByRole("cell", { name: "2027–28" })).toBeVisible();
    await expect(page.getByText("Connected", { exact: true })).toHaveCount(2);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    ).toBeTruthy();
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
    await page.screenshot({
      path: path.join(screenshotDir, `phase2-completion-system-${width}.png`),
      fullPage: true,
    });
    if (width < 1024) {
      await page.getByRole("button", { name: "Open navigation" }).click();
      await expect(page.getByRole("dialog")).toBeVisible();
      await page.keyboard.press("Escape");
      await expect(page.getByRole("dialog")).not.toBeVisible();
      await expect(
        page.getByRole("button", { name: "Open navigation" }),
      ).toBeFocused();
    }
  });
}
for (const [identity, home] of [
  ["drc", "/drc/home"],
  ["hod", "/hod/home"],
  ["principal", "/principal/home"],
  ["admin", "/admin/home"],
  ["acting-hod", "/hod/home"],
]) {
  test(`${identity} demo uses appropriate home without academic actions`, async ({
    page,
  }) => {
    await page.goto("/login");
    await page.getByLabel("Demo identity").selectOption(identity);
    await page.getByRole("button", { name: "Enter local workspace" }).click();
    await expect(page).toHaveURL(home);
    await expect(
      page.getByRole("heading", {
        name: /Faculty workspace|DRC Head workspace|HoD department oversight|Principal institution overview|Administration workspace/,
      }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", {
        name: /Submit application|Approve|Publish quota/,
      }),
    ).toHaveCount(0);
  });
}
test("backend failure and unknown URL are recoverable", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Enter local workspace" }).click();
  await expect(page).toHaveURL("/app/home");
  await page.route("**/api/v1/academic-years", (r) =>
    r.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ error: { code: "DATABASE_UNAVAILABLE" } }),
    }),
  );
  await page.goto("/app/system");
  await expect(page.getByRole("alert")).toContainText("Unable to load");
  await page.goto("/missing");
  await expect(
    page.getByRole("heading", { name: "Page not found" }),
  ).toBeVisible();
});
