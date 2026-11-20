import { expect, test } from "@playwright/test";
import { signIn } from "../e2e/support/academic";
const fixture = JSON.parse(process.env.AKUS_PHASE6_FIXTURE || "{}");
const local = (stamp: string) =>
  new Date(new Date(stamp).getTime() + 330 * 60000).toISOString().slice(0, 23);
test("case-appointed independent verifier confirms a 65% certificate and the participant compares the two dated reports", async ({
  page,
}) => {
  await signIn(page, "acting-hod");
  await page.goto("/app/certificates/" + fixture.aid);
  const form = page.locator("form").filter({
    has: page.getByRole("heading", {
      name: "Verify official certificate",
      exact: true,
    }),
  });
  await form.getByLabel("Official document SHA-256").fill("e".repeat(64));
  await form
    .getByLabel("Exam sitting or session")
    .fill("LOCAL_TEST official sitting");
  const exam = local(
    new Date(
      Math.ceil(Date.parse(fixture.exam_at) / 1000) * 1000,
    ).toISOString(),
  ).slice(0, 19);
  await form.getByLabel("Actual examination date").fill(exam.slice(0, 10));
  await form.getByLabel("Issuer certificate identifier").fill(fixture.key);
  await form.getByLabel("Certificate issue date").fill(exam.slice(0, 10));
  await form.getByLabel("Exact local exam time, if sourced").fill(exam);
  await form.getByLabel("Score percentage").fill("65");
  await form.getByLabel(/I independently verified/).check();
  await form.getByLabel(/I verified actual exam/).check();
  await form
    .getByLabel("Evidence observed at (local time)")
    .fill(local(new Date().toISOString()).slice(0, 19));
  await form
    .getByLabel("Official source reference")
    .fill("LOCAL_TEST issuer archive");
  await form
    .getByLabel("Reason for this source change")
    .fill("LOCAL_TEST independent credential verification");
  await form
    .getByRole("button", { name: "Record independent verification" })
    .click();
  await expect(page.getByText("Revision 2 · verified")).toBeVisible();
  await signIn(page, fixture.staff);
  await page.goto("/app/compliance/annual?episode=" + fixture.episode);
  await expect(
    page.getByText("verified fulfilled", { exact: true }),
  ).toBeVisible();
  await page.getByLabel("Report observation").selectOption({ index: 2 });
  await expect(
    page.getByText("exam reported pending verification", { exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByText("exam reported pending verification", { exact: true }),
  ).toBeVisible();
});
