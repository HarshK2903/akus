import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { apiLogin, fixture, post, signIn } from "./support/academic";

test("Principal follows department records, exports filtered rows and returns to the same filter", async ({
  page,
}) => {
  await signIn(page, "principal");
  await page.goto("/principal/departments");
  await page.getByLabel("Search records").fill("CSE");
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(page).toHaveURL(/search=CSE/);
  const link = page.locator("tbody a").first();
  await expect(link).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export CSV" }).click();
  expect((await download).suggestedFilename()).toBe("akus-departments.csv");
  await link.click();
  await expect(
    page.getByRole("navigation", { name: "Department reports" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Applications", exact: true }),
  ).toBeVisible();
  await page.goBack();
  await expect(page.getByLabel("Search records")).toHaveValue("CSE");
  for (const url of ["applications", "topics-quotas", "audit", "exceptions"]) {
    await page.goto("/principal/" + url);
    await expect(
      page.getByRole("heading", { name: "Records", exact: true }),
    ).toBeVisible();
  }
});

test("Admin test delivery appears only in the personal inbox and supports read acknowledgement", async ({
  page,
}) => {
  await signIn(page, "admin");
  await page.goto("/admin/notifications");
  await page.getByRole("button", { name: "Send preview to my inbox" }).click();
  await page.getByRole("link", { name: "Open my notifications" }).click();
  await page.getByLabel("Search records").fill("In-app test");
  await page.getByLabel("Status", { exact: true }).selectOption("UNREAD");
  await page.getByRole("button", { name: "Apply filters" }).click();
  await page
    .getByRole("button", { name: /^Inspect / })
    .first()
    .click();
  await page.getByRole("button", { name: "Mark read" }).click();
  await expect(page.getByRole("status")).toContainText("Change recorded");
  for (const url of ["audit", "operations"]) {
    await page.goto("/admin/" + url);
    await expect(
      page.getByRole("heading", { name: "Records", exact: true }),
    ).toBeVisible();
  }
});

test("Scoped search, task inbox and office histories remain usable on a narrow viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page, "faculty");
  await page.goto("/app/search");
  await page.getByLabel("Search records").fill("LOCAL");
  await page.getByRole("button", { name: "Apply filters" }).click();
  await expect(
    page.getByRole("heading", { name: "Search results" }),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Search records")).toHaveValue("LOCAL");
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({
    path: "../../docs/qa/phase8-mobile-search.png",
    fullPage: true,
  });
  await page.goto("/app/tasks");
  await expect(page.getByRole("heading", { name: "Records" })).toBeVisible();
  await page.goto("/principal/audit");
  await expect(page.getByRole("alert")).toBeVisible();
  for (const [role, urls] of [
    ["drc", ["/drc/history"]],
    ["hod", ["/hod/decisions", "/hod/reports/applications"]],
  ] as const) {
    await signIn(page, role);
    for (const url of urls) {
      await page.goto(url);
      await expect(
        page.getByRole("heading", { name: "Records", exact: true }),
      ).toBeVisible();
    }
  }
});

test("Admin flags the accepted offering source, and eligible applicants see the resulting blocker", async ({
  page,
}) => {
  const f = await fixture(page);
  await signIn(page, "admin");
  await page.goto("/app/offerings/" + f.offering.id);
  await page.getByText("Flag ambiguous metadata", { exact: true }).click();
  const form = page.locator("details").filter({
    has: page.getByRole("button", { name: "Flag source ambiguity" }),
  });
  await form
    .getByLabel("Official source reference", { exact: true })
    .fill("LOCAL_PHASE8_TEST");
  await form
    .getByLabel("Reason for this source change")
    .fill("LOCAL browser source ambiguity review");
  await form.getByRole("button", { name: "Flag source ambiguity" }).click();
  await expect(form.getByRole("status")).toHaveText(
    "Source flagged for review.",
  );
  await signIn(page, "faculty");
  await page.goto("/app/offerings/" + f.offering.id);
  await expect(
    page.getByText(/SOURCE CONFLICT REVIEW REQUIRED/i).first(),
  ).toBeVisible();
  await expect(
    page.getByText("Flag ambiguous metadata", { exact: true }),
  ).toHaveCount(0);
});

test("Faculty uploads and removes a quarantined draft PDF with an immutable revision history", async ({
  page,
}) => {
  const f = await fixture(page);
  const csrf = await apiLogin(page, "faculty");
  const a = await post(page, csrf, "/applications", {
    offering_id: f.offering.id,
    declarations: {
      academic_relevance: "LOCAL workshop",
      acknowledgement: true,
      score_sharing_yes: true,
      not_yet_enrolled: true,
      prior_attempt: "NONE_DECLARED",
    },
  });
  await signIn(page, "faculty");
  const url = "/app/applications/new/evidence?draft=" + a.id;
  await page.goto(url);
  const files = page.getByRole("region", { name: "Private application files" });
  await files.getByText("Add or replace a PDF").click();
  await files.getByLabel("Application PDF").setInputFiles({
    name: "local-proof.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4\nLOCAL evidence\n%%EOF"),
  });
  await files.getByLabel("Official source reference").fill("LOCAL_PHASE8");
  await files
    .getByLabel("Reason for this source change")
    .fill("LOCAL controlled browser attachment");
  await files.getByRole("button", { name: "Save attachment" }).click();
  await expect(
    files.getByText("local-proof.pdf · version 1 · quarantined"),
  ).toBeVisible();
  await page.reload();
  const row = files.getByText("local-proof.pdf · version 1 · quarantined");
  await row.click();
  const detail = files.locator("details[open]");
  await detail.getByLabel("Official source reference").fill("LOCAL_PHASE8");
  await detail
    .getByLabel("Reason for this source change")
    .fill("Remove the unsubmitted test attachment");
  await detail.getByRole("button", { name: "Remove from draft" }).click();
  await expect(
    files.getByText("local-proof.pdf · version 2 · removed"),
  ).toBeVisible();
  await expect(files.getByRole("link", { name: "Download PDF" })).toHaveCount(
    0,
  );
  await page.setViewportSize({ width: 320, height: 800 });
  await files.getByText("local-proof.pdf · version 2 · removed").click();
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
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    fullPage: true,
    path: "../../docs/qa/phase8-private-files-mobile.png",
  });
});

test("A faculty member can find a private attachment and navigate distinct record pages", async ({
  page,
}) => {
  const f = await fixture(page);
  const csrf = await apiLogin(page, "faculty");
  const draft = await post(page, csrf, "/applications", {
    offering_id: f.offering.id,
    declarations: {},
  });
  const pdf = Buffer.from("%PDF-1.4\nLOCAL navigation fixture\n%%EOF");
  const filename = "LOCAL-" + draft.id + ".pdf";
  const { createHash } = await import("node:crypto");
  await post(page, csrf, "/applications/" + draft.id + "/attachments", {
    expected_version: 1,
    kind: "ACADEMIC_RELEVANCE",
    filename,
    document_digest: createHash("sha256").update(pdf).digest("hex"),
    attachment: {
      media_type: "application/pdf",
      base64_data: pdf.toString("base64"),
    },
    reason: "LOCAL audit of own draft navigation",
    source_reference: "LOCAL_SYSTEM_AUDIT",
  });
  await signIn(page, "faculty");
  await page.goto("/app/search?search=" + filename);
  await page.getByRole("link", { name: filename }).click();
  await expect(
    page.getByRole("heading", { name: "Application evidence", exact: true }),
  ).toBeVisible();
  const nav = page.getByRole("navigation", { name: "Application record" });
  for (const [link, title, proof] of [
    ["Quota history", "Allocation and quota movements", "Annual quota facts"],
    ["Audit timeline", "Application timeline", "Decision and source history"],
    [
      "External participation",
      "External participation",
      "External enrollment evidence",
    ],
  ]) {
    await nav.getByRole("link", { name: link }).click();
    await page.reload();
    await expect(
      page.getByRole("heading", { level: 1, name: title, exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: proof, exact: true }),
    ).toBeVisible();
  }
});
