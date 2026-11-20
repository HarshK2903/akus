import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./qa",
  workers: 1,
  outputDir: "../../.local/case-browser-results",
  use: {
    baseURL: process.env.AKUS_E2E_URL,
    timezoneId: "Asia/Kolkata",
    trace: "retain-on-failure",
  },
  reporter: "list",
});
