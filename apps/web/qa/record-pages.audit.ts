import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { signIn } from "../e2e/support/academic";

// Run after the standard browser journeys against their dedicated synthetic database.
// SQL selects fixture IDs only; all record reads below go through normal browser access.
test("reload each parameterized record with its actual authorized data", async ({
  page,
}) => {
  test.setTimeout(150000);
  expect(process.env.AKUS_E2E_URL).toBe("http://127.0.0.1:18086");
  const db = process.env.AKUS_BROWSER_TEST_DB || "akus_system_browser_test";
  expect(db).toMatch(/^akus_[a-z0-9_]+_test$/);
  const query = `SELECT json_build_object('aid',a.id,'course',a.course_id,'offering',a.offering_id,
  'label',c.title,'pool',alloc.pool_id,'dept',a.department_id,'person',a.person_id,
  'attempt',(SELECT id FROM nptel_attempts WHERE person_id=a.person_id ORDER BY created_at DESC LIMIT 1),
  'transfer',(SELECT r.id FROM academic_reconciliations r JOIN applications t ON t.id=r.application_id WHERE t.department_id=a.department_id AND r.kind='QUOTA_TRANSFER' LIMIT 1),
  'integrity',(SELECT r.id FROM academic_reconciliations r JOIN applications t ON t.id=r.application_id WHERE t.department_id=a.department_id AND r.kind='INTEGRITY' AND r.status='OPEN' LIMIT 1))
  FROM applications a JOIN quota_allocations alloc ON alloc.application_id=a.id
  JOIN nptel_courses c ON c.id=a.course_id JOIN persons p ON p.id=a.person_id
  JOIN demo_identities d ON d.id=p.demo_identity_id WHERE d.key='faculty' ORDER BY a.submitted_at DESC LIMIT 1`;
  const f: Record<string, string> = JSON.parse(
    execFileSync(
      "docker",
      [
        "compose",
        "exec",
        "-T",
        "db",
        "psql",
        "-XAt",
        "-v",
        "ON_ERROR_STOP=1",
        "-U",
        "akus_demo",
        "-d",
        db,
        "-c",
        query,
      ],
      { encoding: "utf8" },
    ),
  );
  for (const value of Object.values(f)) expect(value).toBeTruthy();
  await signIn(page, "faculty");
  const episodes = await page.request.get(
    "/api/v1/compliance/episodes?scope=personal",
  );
  expect(episodes.ok()).toBeTruthy();
  const eid = (await episodes.json()).items[0].id;
  const report = await page.request.get(
    "/api/v1/compliance/episodes/" + eid + "?scope=personal",
  );
  expect(report.ok()).toBeTruthy();
  const { annual, silver } = await report.json();
  expect(annual.length).toBeGreaterThan(0);
  expect(silver.length).toBeGreaterThan(0);
  const app = "/app/applications/" + f.aid;
  const map = "/hod/topic-mappings/" + f.course;
  const pool = "/hod/quotas/" + f.pool;
  const param = "?department=" + f.dept;
  const pages = [
    ["FAC-03", "faculty", "/app/catalog/" + f.course, "Course identity"],
    [
      "FAC-04",
      "faculty",
      "/app/offerings/" + f.offering,
      "Department charging decision",
    ],
    ["FAC-10", "faculty", app, "Application status"],
    ["FAC-11", "faculty", app + "/quota", "Annual quota facts"],
    ["FAC-12", "faculty", app + "/evidence", "Application attachments"],
    ["FAC-13", "faculty", app + "/history", "Decision and source history"],
    [
      "FAC-14",
      "faculty",
      "/app/participation/" + f.aid,
      "External enrollment evidence",
    ],
    [
      "FAC-16",
      "faculty",
      "/app/previous-attempts/" + f.attempt,
      "Repeat eligibility",
    ],
    [
      "FAC-18",
      "faculty",
      "/app/compliance/annual/" + annual[0].id + "?episode=" + eid,
      annual[0].year,
    ],
    [
      "FAC-20",
      "faculty",
      "/app/compliance/silver/" + silver[0].id + "?episode=" + eid,
      silver[0].subject,
    ],
    ["DRC-02", "drc", "/drc/reviews/" + f.aid, "Application status"],
    ["HOD-03", "hod", "/hod/reviews/" + f.aid, "Application status"],
    ["HOD-06", "hod", map + param, "Current charging decision"],
    ["HOD-07", "hod", map + "/edit" + param, "Approve or revise primary topic"],
    ["HOD-10", "hod", pool, ""],
    ["HOD-11", "hod", pool + "/edit", "Publish or revise annual quota"],
    ["HOD-12", "hod", pool + "/ledger", "Quota allocation ledger"],
    [
      "HOD-14",
      "hod",
      "/hod/quota-transfers/" + f.transfer,
      "Quota transfer case",
    ],
    [
      "HOD-16",
      "hod",
      "/hod/outcome-verifications/" + f.attempt,
      "Repeat eligibility",
    ],
    ["HOD-18", "hod", "/hod/integrity/" + f.integrity, "Case timeline"],
    ["PRN-03", "principal", "/principal/departments/" + f.dept, "Applications"],
    ["ADM-03", "admin", "/admin/staff/" + f.person, "Institutional record"],
    [
      "ADM-04",
      "admin",
      "/admin/staff/" + f.person + "/employment",
      "Employment episode register",
    ],
  ];
  let current = "faculty";
  for (const [id, role, path, heading] of pages)
    await test.step(id, async () => {
      if (role !== current) {
        await signIn(page, role);
        current = role;
      }
      if (id === "HOD-18") {
        const response = await page.request.get(
          "/api/v1/quota-transfer-cases/" + f.integrity,
        );
        expect(response.status()).toBe(404);
      }
      const endpoint = path.startsWith(pool)
        ? "/api/v1/quotas/" + f.pool
        : null;
      await page.goto(path);
      const loaded = endpoint
        ? page.waitForResponse(
            (r) => new URL(r.url()).pathname === endpoint && r.ok(),
          )
        : null;
      await page.reload();
      if (loaded) await loaded;
      await expect(
        page.locator("main h1").filter({
          hasNotText: /Loading|Opening|denied|unavailable|not found/i,
        }),
      ).toBeVisible();
      if (heading)
        await expect(
          page.getByRole("heading", { name: heading, exact: true }).first(),
        ).toBeVisible();
      await expect(
        page.getByRole("heading", {
          name: /Unable to load this information|Access is not available|Page not found/i,
        }),
      ).toHaveCount(0);
      console.log(id + " authorized record reloaded");
    });
});

test("all five public entries expose their anonymous recovery or sign-in state", async ({
  page,
}) => {
  for (const [url, heading] of [
    ["/login", "Sign in to AKUS"],
    ["/auth/callback", "Sign-in status"],
    ["/access-denied", "Access is not available"],
    ["/system-unavailable", "Service availability"],
    ["/not-found", "Page not found"],
  ]) {
    await page.goto(url);
    await expect(
      page.getByRole("heading", { name: heading, exact: true }),
    ).toBeVisible();
    if (url === "/system-unavailable") {
      await page.getByRole("button", { name: "Retry health check" }).click();
      await expect(page.getByText("ready", { exact: true })).toBeVisible();
    }
    console.log(url + " anonymous state verified");
  }
});
