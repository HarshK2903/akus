import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import path from "node:path";
import { signIn } from "../e2e/support/academic";
const fixture = JSON.parse(process.env.AKUS_PHASE5_FIXTURE || "{}");
const local = (t: string) =>
  new Date(new Date(t).valueOf() + 330 * 60000).toISOString().slice(0, 23);
async function proof(form: ReturnType<Page["locator"]>) {
  await form
    .getByLabel("Official source reference", { exact: true })
    .fill("LOCAL_TEST archived official source");
  await form
    .getByLabel("Reason for this source change")
    .fill("LOCAL_TEST independent archived evidence review");
  await form.getByLabel("Official document SHA-256").fill("e".repeat(64));
  await form
    .getByLabel("Source observed at (local time)")
    .fill(local(new Date().toISOString()).slice(0, 19));
  await form.getByRole("checkbox").last().check();
}
test("Q47 reviewer documents unknown order and releases exactly one seat in the isolated Docker database", async ({
  page,
}) => {
  await signIn(page, "principal");
  const url = "/hod/separation-cases/" + fixture.pending + "?status=OPEN";
  await page.goto(url);
  await expect(page.getByText("HELD", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Record case decision" }),
  ).toHaveCount(0);
  await signIn(page, "hod");
  await page.goto(url);
  const form = page.locator("form").filter({
    has: page.getByRole("button", { name: "Record case decision" }),
  });
  await form.getByLabel("Documented finding").selectOption("INDETERMINATE");
  await proof(form);
  await form.getByRole("button", { name: "Record case decision" }).click();
  await expect(page.getByText("RELEASED", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText("SEPARATED", { exact: true })).toBeVisible();
  await page.setViewportSize({ width: 320, height: 900 });
  await expect(
    page.getByRole("heading", { name: "Historical certificate assessment" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: path.resolve("../../docs/qa/phase5-q47-detail-320.png"),
    fullPage: true,
  });
});
test("formally designated test reviewer verifies an archived result then restores the pre-verification report", async ({
  page,
}) => {
  await signIn(page, "acting-hod");
  const url = "/hod/separation-cases/" + fixture.historical;
  await page.goto(url);
  const before = local(new Date().toISOString()).slice(0, 19);
  const form = page.locator("form").filter({
    has: page.getByRole("button", { name: "Record historical finding" }),
  });
  await form
    .getByLabel("Official certificate identifier")
    .fill("LOCAL_TEST_" + crypto.randomUUID());
  await form
    .getByLabel("Actual examination date", { exact: true })
    .fill(fixture.exam_on);
  await form
    .getByLabel("Exact examination time if documented")
    .fill(local(fixture.exam_at));
  await form.getByLabel("Certificate issue date").fill(fixture.exam_on);
  await form.getByLabel("Verified percentage").fill("74");
  await proof(form);
  await form.getByRole("button", { name: "Record historical finding" }).click();
  await expect(
    page.getByText("VERIFIED_FULFILLED", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("RELEASED", { exact: true })).toBeVisible();
  await page.getByLabel("Records known by (local time)").fill(before);
  await page.getByRole("button", { name: "View historical report" }).click();
  await expect(
    page.getByText(
      "No authenticated certificate for this application at this time.",
    ),
  ).toBeVisible();
});

test("HoD closes Q44 from a late, date-only enrollment record and the timeline keeps its precision", async ({
  page,
}) => {
  await signIn(page, "hod");
  await page.goto("/hod/separation-cases/" + fixture.date_only);
  const form = page.locator("form").filter({
    has: page.getByRole("button", { name: "Record case decision" }),
  });
  await form.getByLabel("Documented finding").selectOption("Q44");
  await form
    .getByLabel("Enrollment date when the source gives only a date")
    .fill(fixture.enrolled_on);
  await expect(
    form.getByLabel("Verified enrollment time (if established)"),
  ).toHaveValue("");
  await proof(form);
  await form.getByRole("button", { name: "Record case decision" }).click();
  await expect(page.getByText("RELEASED", { exact: true })).toBeVisible();
  await page.reload();
  const decision = page
    .locator("details")
    .filter({ has: page.locator("summary").filter({ hasText: /^Q44 ·/ }) });
  await decision.locator("summary").click();
  await expect(
    decision.getByText("enrollment on", { exact: true }),
  ).toBeVisible();
  await expect(
    decision.getByText(fixture.enrolled_on, { exact: true }),
  ).toBeVisible();
  await expect(
    decision.getByText("enrollment at", { exact: true }),
  ).toHaveCount(0);
});
