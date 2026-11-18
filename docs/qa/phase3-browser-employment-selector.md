# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: people.spec.ts >> Admin creates source records, appoints a DRC, ends authority and sees immutable history
- Location: e2e/people.spec.ts:42:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByRole('cell', { name: '2026-07-01' })
Expected: visible
Error: strict mode violation: getByRole('cell', { name: '2026-07-01' }) resolved to 2 elements:
    1) <td>2026-07-01</td> aka getByRole('region', { name: 'Employment history' }).getByRole('cell', { name: '-07-01' })
    2) <td>2026-07-01</td> aka getByRole('region', { name: 'Department membership history' }).getByRole('cell', { name: '-07-01' })

Call log:
  - Expect "toBeVisible" getByRole('cell', { name: '2026-07-01' }) with timeout 5000ms
  - waiting for getByRole('cell', { name: '2026-07-01' })

```

# Page snapshot

```yaml
- generic [ref=f1e2]:
  - link "Skip to content" [ref=f1e3] [cursor=pointer]:
    - /url: "#main-content"
  - banner [ref=f1e4]:
    - generic [ref=f1e5]:
      - generic [ref=f1e6]: AKUS.
      - generic [ref=f1e7]: NPTEL
    - generic [ref=f1e8]: LOCAL / DEMO
    - generic [ref=f1e9]:
      - generic [ref=f1e10]:
        - text: Nila Shah
        - generic [ref=f1e11]: Admin
      - generic [ref=f1e12]: NS
  - complementary [ref=f1e13]:
    - generic [ref=f1e14]: WORKSPACE
    - navigation "Main navigation" [ref=f1e15]:
      - link "Overview" [ref=f1e16] [cursor=pointer]:
        - /url: /admin/home
      - link "Course catalog" [ref=f1e22] [cursor=pointer]:
        - /url: /app/catalog
      - link "Profile & access" [ref=f1e25] [cursor=pointer]:
        - /url: /app/profile
      - link "Policy guide" [ref=f1e29] [cursor=pointer]:
        - /url: /app/help
      - link "Staff directory" [ref=f1e32] [cursor=pointer]:
        - /url: /admin/staff
      - link "Office appointments" [ref=f1e36] [cursor=pointer]:
        - /url: /admin/appointments
      - link "Teaching allocations" [ref=f1e40] [cursor=pointer]:
        - /url: /people/teaching
      - link "Source imports" [ref=f1e43] [cursor=pointer]:
        - /url: /admin/imports
      - link "Reference setup" [ref=f1e46] [cursor=pointer]:
        - /url: /admin/reference
      - link "Account requests" [ref=f1e49] [cursor=pointer]:
        - /url: /admin/accounts
      - link "NPTEL provider sources" [ref=f1e53] [cursor=pointer]:
        - /url: /admin/nptel-sync
    - generic [ref=f1e56]:
      - strong [ref=f1e60]: A foundation for accountable decisions
      - paragraph [ref=f1e61]: Academic workflows will be added in verified implementation phases.
      - text: BUILD 0.2 · LOCAL
    - button "Sign out" [ref=f1e62] [cursor=pointer]
  - generic [ref=f1e66]:
    - region "Local demonstration notice" [ref=f1e67]:
      - text: Local demonstration
      - generic [ref=f1e69]: Fictional identities. Provider observations are labeled separately; no verified enrollment or certificate is implied.
    - main [ref=f1e70]:
      - generic [ref=f1e71]:
        - text: Workspace
        - generic [ref=f1e74]: Staff source management
      - generic [ref=f1e76]:
        - heading "Staff source management" [level=1] [ref=f1e77]
        - paragraph [ref=f1e78]: LOCAL E2E 7C283759 · Authorized corrections preserve source history.
      - generic [ref=f1e79]:
        - link "← Staff record" [ref=f1e80] [cursor=pointer]:
          - /url: /admin/staff/e9d96a33-47f6-4abb-aa0e-97e0987dc1a7
        - link "Record appointment" [ref=f1e81] [cursor=pointer]:
          - /url: /admin/appointments/new?person=e9d96a33-47f6-4abb-aa0e-97e0987dc1a7
      - generic [ref=f1e82]:
        - heading "Employment episode register" [level=2] [ref=f1e84]
        - region "Employment episode register" [ref=f1e85]:
          - table [ref=f1e86]:
            - rowgroup [ref=f1e87]:
              - row [ref=f1e88]:
                - columnheader "Start" [ref=f1e89]
                - columnheader "End before" [ref=f1e90]
                - columnheader "Classification" [ref=f1e91]
                - columnheader "Source" [ref=f1e92]
            - rowgroup [ref=f1e93]:
              - row [ref=f1e94]:
                - cell "2026-07-01" [ref=f1e95]
                - cell "Open-ended" [ref=f1e96]
                - cell "Faculty" [ref=f1e97]
                - cell "LOCAL_E2E_STAFF_ORDER" [ref=f1e98]
      - generic [ref=f1e99]:
        - generic [ref=f1e100]:
          - heading "Record or correct official facts" [level=2] [ref=f1e101]
          - generic [ref=f1e102]:
            - generic [ref=f1e103]: Source record type
            - combobox "Source record type" [ref=f1e104]:
              - option "Staff identity / access status"
              - option "Employment episode" [selected]
              - option "Home department membership"
              - option "Institutional email"
              - option "Replace mistaken office appointment"
          - generic [ref=f1e105]:
            - generic [ref=f1e106]: Existing record
            - combobox "Existing record" [ref=f1e107]:
              - option "Add a new official record" [selected]
              - option "2026-07-01 → Open-ended"
          - generic [ref=f1e108]:
            - generic [ref=f1e109]:
              - generic [ref=f1e110]: Effective start date
              - textbox "Effective start date" [ref=f1e111]
            - generic [ref=f1e112]:
              - generic [ref=f1e113]: Effective end before (exclusive)
              - textbox "Effective end before (exclusive)" [ref=f1e114]
            - generic [ref=f1e115]:
              - checkbox "Official faculty employment classification" [ref=f1e116]
              - text: Official faculty employment classification
            - generic [ref=f1e117]:
              - generic [ref=f1e118]: Official source reference
              - textbox "Official source reference" [ref=f1e119]
            - generic [ref=f1e120]:
              - text: Reason for this source change
              - textbox "Reason for this source change" [ref=f1e121]
            - button "Save source change" [ref=f1e122] [cursor=pointer]
        - generic [ref=f1e123]:
          - heading "Effective dates and source history" [level=2] [ref=f1e124]
          - paragraph [ref=f1e125]: A correction changes the current source projection and retains the original facts. An office replacement must pass employment, scope and HoD/DRC exclusion checks in the same transaction.
          - paragraph [ref=f1e126]: Before shortening an employment episode, correct dependent teaching, membership and office intervals. Genuine rehire is a new episode; a source typo is a correction to the existing episode.
          - paragraph [ref=f1e127]: Institutional email changes do not move a Google subject link. A verified replacement account requires explicit reconciliation.
          - paragraph [ref=f1e128]: Academic exemptions, retrospective credit and application closures remain separate policy-governed workflows. Admin source corrections grant none of those outcomes.
      - generic [ref=f1e129]:
        - generic [ref=f1e130]:
          - heading "Source revision history" [level=2] [ref=f1e131]
          - generic [ref=f1e132]: Immutable · latest 100
        - list [ref=f1e133]:
          - listitem [ref=f1e134]:
            - strong [ref=f1e135]: Source recorded
            - time [ref=f1e136]: 18 Nov 2026, 7:13:01 pm IST
            - paragraph [ref=f1e137]: Database source write; consult associated audit event or fixture provenance
            - group [ref=f1e138]:
              - generic "View recorded facts" [ref=f1e139] [cursor=pointer]
          - listitem [ref=f1e140]:
            - strong [ref=f1e141]: Source recorded
            - time [ref=f1e142]: 18 Nov 2026, 7:13:01 pm IST
            - paragraph [ref=f1e143]: Database source write; consult associated audit event or fixture provenance
            - group [ref=f1e144]:
              - generic "View recorded facts" [ref=f1e145] [cursor=pointer]
          - listitem [ref=f1e146]:
            - strong [ref=f1e147]: Source recorded
            - time [ref=f1e148]: 18 Nov 2026, 7:13:01 pm IST
            - paragraph [ref=f1e149]: Database source write; consult associated audit event or fixture provenance
            - group [ref=f1e150]:
              - generic "View recorded facts" [ref=f1e151] [cursor=pointer]
    - contentinfo [ref=f1e152]:
      - generic [ref=f1e153]: AKUS · NPTEL participation & compliance
      - generic [ref=f1e154]: Phase 2 / People & access
```

# Test source

```ts
  1   | import { expect, test, type Page } from "@playwright/test";
  2   | import AxeBuilder from "@axe-core/playwright";
  3   | import path from "node:path";
  4   | 
  5   | async function signIn(page: Page, identity = "admin") {
  6   |   await page.goto("/login");
  7   |   await page.getByLabel("Demo identity").selectOption(identity);
  8   |   await page.getByRole("button", { name: "Enter local workspace" }).click();
  9   |   await expect(
  10  |     page.getByRole("heading", {
  11  |       name: /Faculty workspace|DRC Head workspace|HoD department oversight|Principal institution overview|Administration workspace/,
  12  |     }),
  13  |   ).toBeVisible();
  14  | }
  15  | function istNow() {
  16  |   return new Date(Date.now() + 330 * 60_000).toISOString().slice(0, 19);
  17  | }
  18  | async function endOffice(page: Page, person: string) {
  19  |   await page.goto("/admin/appointments");
  20  |   const row = page
  21  |     .getByRole("row")
  22  |     .filter({ hasText: person })
  23  |     .filter({ has: page.getByRole("cell", { name: "current", exact: true }) });
  24  |   await row
  25  |     .getByRole("link", { name: "View appointment", exact: true })
  26  |     .click();
  27  |   await expect(
  28  |     page.getByRole("heading", { name: "Office appointment record" }),
  29  |   ).toBeVisible();
  30  |   await page
  31  |     .getByLabel("Reason and source reference")
  32  |     .fill("LOCAL_E2E: formal end of demonstration appointment");
  33  |   await page
  34  |     .getByLabel("I confirm this source appointment must end now.")
  35  |     .check();
  36  |   await page
  37  |     .getByRole("button", { name: "End appointment now", exact: true })
  38  |     .click();
  39  |   await expect(page.getByRole("status")).toContainText("Appointment ended");
  40  | }
  41  | 
  42  | test("Admin creates source records, appoints a DRC, ends authority and sees immutable history", async ({
  43  |   page,
  44  | }) => {
  45  |   const errors: string[] = [];
  46  |   page.on("pageerror", (e) => errors.push(e.message));
  47  |   const suffix = crypto.randomUUID().slice(0, 8).toUpperCase();
  48  |   const name = `LOCAL E2E ${suffix}`;
  49  |   await signIn(page);
  50  |   await page
  51  |     .getByRole("link", { name: "Staff directory", exact: true })
  52  |     .click();
  53  |   await page.getByRole("link", { name: "Add staff record" }).click();
  54  |   await expect(
  55  |     page.getByRole("heading", { name: "Add staff record", exact: true }),
  56  |   ).toBeVisible();
  57  |   await page
  58  |     .getByLabel("Permanent staff key", { exact: true })
  59  |     .fill(`E2E-${suffix}`);
  60  |   await page.getByLabel("Display name").fill(name);
  61  |   await page
  62  |     .getByLabel("Home department")
  63  |     .selectOption({ label: "Electronics · DEMO" });
  64  |   await page.getByLabel("Employment starts on").fill("2026-07-01");
  65  |   await page
  66  |     .getByLabel("Official source reference")
  67  |     .fill("LOCAL_E2E_STAFF_ORDER");
  68  |   await page
  69  |     .getByLabel("Reason for creating this record")
  70  |     .fill("Browser workflow demonstration source record");
  71  |   await page.getByRole("button", { name: "Create staff record" }).click();
  72  |   await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  73  |   const personUrl = page.url();
  74  |   await page.reload();
  75  |   await expect(page.getByText("STAFF CREATED", { exact: true })).toBeVisible();
  76  |   await page
  77  |     .getByRole("link", { name: "Employment history", exact: true })
  78  |     .click();
  79  |   await expect(page).toHaveURL(/\/employment$/);
> 80  |   await expect(page.getByRole("cell", { name: "2026-07-01" })).toBeVisible();
      |                                                                ^ Error: expect(locator).toBeVisible() failed
  81  |   await page
  82  |     .getByRole("link", { name: "Record appointment", exact: true })
  83  |     .click();
  84  |   await page.getByLabel("Office", { exact: true }).selectOption("DRC_HEAD");
  85  |   await page
  86  |     .getByLabel("Scope", { exact: true })
  87  |     .selectOption({ label: "Electronics · DEMO" });
  88  |   await page.getByLabel("Effective from (IST)", { exact: true }).fill(istNow());
  89  |   await page
  90  |     .getByLabel("Official source reference")
  91  |     .fill("LOCAL_E2E_OFFICE_ORDER");
  92  |   await page
  93  |     .getByLabel("Appointment rationale")
  94  |     .fill("Demonstrate faculty office authority with a real source command");
  95  |   await page
  96  |     .getByRole("button", { name: "Record appointment", exact: true })
  97  |     .click();
  98  |   await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
  99  |   try {
  100 |     await expect(
  101 |       page.getByText("OFFICE APPOINTED", { exact: true }),
  102 |     ).toBeVisible();
  103 |   } finally {
  104 |     await endOffice(page, name);
  105 |   }
  106 |   await page.goto(personUrl);
  107 |   await expect(page.getByText("OFFICE ENDED", { exact: true })).toBeVisible();
  108 |   await expect(
  109 |     page.getByRole("cell", { name: "ended", exact: true }),
  110 |   ).toBeVisible();
  111 |   await page.screenshot({
  112 |     path: path.resolve("../../docs/qa/phase2-completion-staff-history.png"),
  113 |     fullPage: true,
  114 |   });
  115 |   expect(errors).toEqual([]);
  116 | });
  117 | 
  118 | test("overlapping DRC and cross-department acting HoD is visibly rejected without losing inputs", async ({
  119 |   page,
  120 | }) => {
  121 |   await signIn(page);
  122 |   await page.goto("/admin/appointments/new");
  123 |   await page
  124 |     .getByLabel("Staff member", { exact: true })
  125 |     .selectOption({ label: "Arun Sen · DEMO-DRC" });
  126 |   await page.getByLabel("Office", { exact: true }).selectOption("ACTING_HOD");
  127 |   await page
  128 |     .getByLabel("Scope", { exact: true })
  129 |     .selectOption({ label: "Institution administration · DEMO" });
  130 |   await page.getByLabel("Effective from (IST)", { exact: true }).fill(istNow());
  131 |   await page.getByLabel("Official source reference").fill("LOCAL_E2E_CONFLICT");
  132 |   await page
  133 |     .getByLabel("Appointment rationale")
  134 |     .fill("Test rejected overlapping appointment");
  135 |   await page
  136 |     .getByRole("button", { name: "Record appointment", exact: true })
  137 |     .click();
  138 |   await expect(page.getByRole("alert")).toContainText("overlap");
  139 |   await expect(page.getByLabel("Official source reference")).toHaveValue(
  140 |     "LOCAL_E2E_CONFLICT",
  141 |   );
  142 |   await page.screenshot({
  143 |     path: path.resolve("../../docs/qa/phase2-completion-conflict.png"),
  144 |     fullPage: true,
  145 |   });
  146 | });
  147 | 
  148 | test("Principal reads all departments with no source write controls; Faculty cannot bypass route guards", async ({
  149 |   page,
  150 | }) => {
  151 |   await signIn(page, "principal");
  152 |   await page.goto("/people/staff");
  153 |   await expect(
  154 |     page.getByRole("link", { name: "Omar Das (acting HoD)", exact: true }),
  155 |   ).toBeVisible();
  156 |   await expect(
  157 |     page.getByRole("link", { name: "Mira Rao", exact: true }),
  158 |   ).toBeVisible();
  159 |   await expect(
  160 |     page.getByRole("link", { name: "Add staff record" }),
  161 |   ).toHaveCount(0);
  162 |   await page.goto("/people/appointments");
  163 |   await expect(
  164 |     page.getByRole("heading", { name: "Office appointments", exact: true }),
  165 |   ).toBeVisible();
  166 |   await expect(
  167 |     page.getByRole("button", { name: "End appointment" }),
  168 |   ).toHaveCount(0);
  169 |   await page.goto("/admin/staff/new");
  170 |   await expect(
  171 |     page.getByRole("heading", { name: "Access is not available" }),
  172 |   ).toBeVisible();
  173 |   await signIn(page, "faculty");
  174 |   await page.goto("/admin/appointments");
  175 |   await expect(
  176 |     page.getByRole("heading", { name: "Access is not available" }),
  177 |   ).toBeVisible();
  178 |   expect((await page.request.get("/api/v1/people/staff")).status()).toBe(403);
  179 | });
  180 | 
```