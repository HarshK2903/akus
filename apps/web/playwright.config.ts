import { defineConfig } from "@playwright/test";
export default defineConfig({
  globalSetup: "./e2e/setup.ts",
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: process.env.AKUS_E2E_URL ?? "http://127.0.0.1:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  reporter: [["list"], ["html", { open: "never" }]],
});
