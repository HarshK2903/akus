import { matchRoutes } from "react-router-dom";
import { expect, test } from "vitest";
import { readFileSync } from "node:fs";
const inventory: { route: string }[] = JSON.parse(
  readFileSync("../../docs/route-inventory.json", "utf8"),
);
import { routes } from "./routes";
test("all 80 specification paths resolve to explicit application routes", () => {
  expect(inventory).toHaveLength(80);
  for (const page of inventory) {
    const url = page.route.replace(
      /:\w+/g,
      "f7138d5e-f1f7-40d8-b72d-279bf316f224",
    );
    const matched = matchRoutes(routes, url)?.at(-1)?.route;
    expect(matched?.element, page.route).toBeTruthy();
    expect(matched?.path, page.route).not.toContain("*");
  }
});
