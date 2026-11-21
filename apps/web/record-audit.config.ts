import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./qa",
  testMatch: "record-pages.audit.ts",
  workers: 1,
  outputDir: "../../.local/system-record-audit",
  use: { baseURL: process.env.AKUS_E2E_URL },
  reporter: "list",
});
