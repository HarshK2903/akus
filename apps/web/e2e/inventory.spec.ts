import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { signIn } from "./support/academic";

const inventory: { id: string; route: string }[] = JSON.parse(
  readFileSync("../../docs/route-inventory.json", "utf8"),
);
const areas = {
  faculty: ["SHR", "FAC"],
  drc: ["DRC"],
  hod: ["HOD"],
  principal: ["PRN"],
  admin: ["ADM"],
};
for (const [role, prefixes] of Object.entries(areas)) {
  test(
    role + " can refresh every fixed workspace page assigned to that role",
    async ({ page }) => {
      test.setTimeout(120000);
      await signIn(page, role);
      const pages = inventory.filter(
        (p) => prefixes.includes(p.id.split("-")[0]) && !p.route.includes(":"),
      );
      const errors: string[] = [];
      page.on("pageerror", (err) => errors.push(err.message));
      for (const entry of pages) {
        await test.step(entry.id + " " + entry.route, async () => {
          const resp = await page.goto(entry.route);
          expect(resp?.status()).toBe(200);
          await expect(page.getByRole("main")).toBeVisible();
          await expect(
            page
              .locator("main h1")
              .filter({ hasNotText: /^(Loading|Opening)/ }),
          ).toBeVisible();
          await expect(page).toHaveURL(new RegExp(entry.route + "(?:\\?|$)"));
          await expect(
            page.getByRole("heading", {
              name: /Page not found|Access is not available|Unable to load this information/,
            }),
          ).toHaveCount(0);
        });
      }
      expect(errors).toEqual([]);
    },
  );
}
