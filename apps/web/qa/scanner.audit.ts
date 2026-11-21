import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { signIn } from "../e2e/support/academic";

test("a faculty member downloads the clean certificate revision while the original remains quarantined", async ({
  page,
}) => {
  const database = process.env.AKUS_BROWSER_TEST_DB || "";
  expect(database).toMatch(/^akus_[a-z0-9_]+_test$/);
  expect(process.env.AKUS_E2E_URL).toBe("http://127.0.0.1:18086");
  // Locate the synthetic real-engine case created by scripts/check-clamd.sh.
  const query = `SELECT json_build_object('staff', d.key, 'aid', c.application_id,
    'digest', c.facts->>'document_digest', 'revision', c.id)
    FROM credential_events c JOIN credential_events q ON q.document_id = c.document_id
    JOIN persons p ON p.id = c.actor_id JOIN demo_identities d ON d.id = p.demo_identity_id
    WHERE c.facts->>'document_scan' = 'CLEAN' AND q.facts->>'document_scan' = 'QUARANTINED'
    AND c.version = q.version + 1 AND c.facts->>'scanner_version' LIKE 'ClamAV %'
    ORDER BY c.recorded_at DESC LIMIT 1`;
  const fixture = JSON.parse(
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
        database,
        "-c",
        query,
      ],
      { encoding: "utf8" },
    ),
  );
  await signIn(page, fixture.staff);
  await page.goto("/app/certificates/" + fixture.aid);
  await expect(page.getByText(/Private PDF · quarantined/i)).toBeVisible();
  const clean = page.getByRole("link", { name: "Download PDF" });
  await expect(clean).toHaveCount(1);
  const href = await clean.getAttribute("href");
  expect(href).toContain("?revision=" + fixture.revision);
  const received = page.waitForEvent("download");
  await clean.click();
  const file = await received;
  expect(file.suggestedFilename()).toBe("certificate.pdf");
  const digest = createHash("sha256");
  const stream = await file.createReadStream();
  expect(stream).toBeTruthy();
  for await (const bytes of stream!) digest.update(bytes);
  expect(digest.digest("hex")).toBe(fixture.digest);
  await signIn(page, "admin");
  expect((await page.request.get(href!)).status()).toBe(403);
});
