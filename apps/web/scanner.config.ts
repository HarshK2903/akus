import { defineConfig } from "@playwright/test";
import recordAudit from "./record-audit.config";

export default defineConfig({
  ...recordAudit,
  testMatch: "scanner.audit.ts",
  outputDir: "../../.local/scanner-browser-results",
});
