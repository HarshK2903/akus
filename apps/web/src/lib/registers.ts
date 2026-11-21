export const registers = {
  tasks: [
    "/app/tasks",
    "Task inbox",
    "Open drafts and work awaiting your current office.",
  ],
  notifications: [
    "/app/notifications",
    "My notifications",
    "Read updates about your records and manage your inbox.",
  ],
  search: [
    "/app/search",
    "Workspace search",
    "Find courses, offerings, people and applications within your access.",
  ],
  "drc-history": [
    "/drc/history",
    "DRC decision history",
    "Review your recorded decisions and their application histories.",
    "DRC_HEAD",
  ],
  "hod-history": [
    "/hod/decisions",
    "Department decisions",
    "Trace reviews, quota changes, topic approvals and findings.",
    "HOD",
  ],
  "department-applications": [
    "/hod/reports/applications",
    "Department application report",
    "Inspect application status, review stage and counted quota.",
    "HOD",
  ],
  departments: [
    "/principal/departments",
    "Departments",
    "Inspect office coverage, pending reviews and full annual pools.",
    "PRINCIPAL",
  ],
  applications: [
    "/principal/applications",
    "Institution applications",
    "Trace application progress across departments.",
    "PRINCIPAL",
  ],
  "topics-quotas": [
    "/principal/topics-quotas",
    "Institution topics and quotas",
    "Inspect current primary mappings and department topic pools.",
    "PRINCIPAL",
  ],
  exceptions: [
    "/principal/exceptions",
    "Institution exceptions",
    "Trace reconciliation cases to the application and its evidence.",
    "PRINCIPAL",
  ],
  audit: [
    "/principal/audit",
    "Institution audit",
    "Filter recorded events by identifier, action and time.",
    "PRINCIPAL",
  ],
  operations: [
    "/admin/operations",
    "Worker operations",
    "Review queue attempts, worker health and eligible retries.",
    "ADMIN",
  ],
  "source-audit": [
    "/admin/audit",
    "Administrative audit",
    "Inspect source changes and operational decisions.",
    "ADMIN",
  ],
  settings: [
    "/admin/notifications",
    "Notification settings",
    "Configure in-app application headings and inspect version history.",
    "ADMIN",
  ],
} satisfies Record<string, [string, string, string, string?]>;
export type Register = keyof typeof registers;
