# AKUS NPTEL — Principal Product/UI Design Specification

Edition: UI/UX Handoff 1.0, 15 November 2026. Design scope: responsive LIGHT-THEME institutional NPTEL module of AKUS. This is a specification, not application code. The implementation handoff bundles the latest verified AKUS master implementation baseline V2.4 in full, so its recipient does not need this conversation.

## DELIVERABLE 1 — Project-to-UI requirements and authority reconciliation

**Project:** AKUS (Automated Knowledge Upgrade System), institutional faculty NPTEL participation, quota governance, approvals, evidence, annual compliance, subject-wise Silver compliance, separation and reproducible audits. Not a student ERP, a general-purpose HR suite, or an NPTEL provider website. Scale design target: college-sized multi-department institution; exact headcount is not a ratified deployment constraint.

**Precedence:** Latest explicit institutional amendments override incompatible older numbered Q-01–Q-50 decisions. Preserve old Q policies as historical versions but do not implement superseded role or quota paths as live functionality. In this UI, a role or action is enabled only if the server proves current authority and the applicable policy is confirmed.

### Currently active institutional role model

- **Faculty (F):** eligible NPTEL participant; draft/submit, view own applications, provide evidence, see annual/Silver compliance, request legitimate withdrawal, maintain historical view. Ordinary application review: DRC Head -> HoD.
- **DRC Head (D):** an eligible FACULTY member with all faculty responsibilities, plus independent academic review of OTHER faculty's applications in authorized department. The DRC Head's OWN application bypasses DRC self-review and goes DIRECTLY to HoD for final decision.
- **HoD / formally appointed acting HoD (H):** exempt from compulsory NPTEL participation in the office; not a personal NPTEL applicant in the current design. Authorized departmental final review, course-to-primary-topic mapping, annual topic quota publication/revision, failed-attempt outcome verification, eligible separation closure, ambiguity review and departmental reporting. Must never be simultaneously the DRC Head; validate effective-dated cross-department office non-overlap.
- **Principal (P):** top hierarchy with institutional-wide READ/oversight on quotas, decisions, compliance, audits, reports and unresolved cases. Exempt from compulsory NPTEL and no personal applicant workflow. Global oversight is not a general mutation or self-approval privilege. The old emerging-technology Principal approval route is an OPEN POLICY CONFLICT; do not turn it into a live button until ratified.
- **Admin (A):** authoritative, audited institutional staff/org/academic-year/teaching-assignment configuration and provider adapter operations. No academic approval or departmental quota write from Admin role alone; a person with other roles must separately satisfy those role grants. Faculty MOOC Coordinator is a scoped faculty designation, not a sixth universal RBAC role.

### Latest binding topic-quota rules

1. Exactly ONE department-specific, HoD-approved PRIMARY charging topic for each (department, canonical NPTEL course) across its offerings while that mapping version is effective. Original provider MULTI-CATEGORY labels remain visible; applicants cannot choose a convenient category. A different department may approve a different topic. Revisions are effective-dated, audited and evidence-backed. **Retroactive movement of active seats following mapping revision remains UNDECIDED**; show impact/read-only historical reservations without automatically migrating.
2. One published shared pool per (department, canonical charging topic, July-1-to-June-30 academic year); numerous courses/offerings may share it. Cap owned and editable by authorized HoD, but not reduced below currently counted occupancy. Unmapped course/topic or unpublished annual pool => draft and deduplicated mapping/quota intake, never a successful application submission or HELD seat.
3. At valid submit, provider's CURRENT officially PUBLISHED/SCHEDULED exam date determines INITIAL pool year; enrollment cutoff, exam-registration cutoff, duration and other eligibility are validated. Atomically reserve 1 counted seat with application creation/submission/audit. The published exam date is provisional; it does not prove exam attendance.
4. Verified provider reschedule crossing July–June boundary => atomically migrate a currently counted reservation to target published pool for same department/topic, only if capacity exists, preserving original/current pool history. If destination missing/unpublished/full, keep original seat counted and show a transparent transfer reconciliation case; no double count. Completion academic-year credit later follows ACTUAL verified exam date Q-35 regardless of whether transfer succeeded.
5. Distinguish category versus canonical course versus individual offering versus subject relevance; those are different records and decision contexts. Distinguish DRC/HOD academic REVIEW from HoD TOPIC MAPPING approval from quota publication from evidence verification.

### Invariant-first UX

Every submission, approval, rejection, quota revision, mapping revision, evidence verification, separation closure, historical reassessment and transfer must be represented as a server-authorized action with explicit after-state, immutable timeline and real error recovery. Never pretend that AKUS approval enrolls a person on the external NPTEL platform or validates an uploaded certificate automatically. Never expose 'switch topic' choice to faculty. Never hide an unresolved policy behind an automatic decision.

### Project-to-UI requirements traceability

| Requirement or policy | UI responsibility | Primary routes | Backend authority |
|---|---|---|---|
| Authenticated institutional access | Google sign-in, denied-provisioning screen, current role scope | `/login`, `/access-denied`, `/app/profile` | OIDC session + effective-dated RBAC/ABAC |
| Faculty catalog + provider dates | Exact offerings, course metadata provenance, stale-data notices | `/app/catalog`, `/app/catalog/:courseId`, `/app/offerings/:offeringId` | NPTEL adapter + catalog registry |
| Multi-category primary-topic mapping | Read-only mapping in faculty wizard, HoD mapping inbox/decision/history | `/app/offering...`, `/hod/topic-mappings...` | HoD-only mapping version engine |
| Annual shared topic quota | Pool details, HoD publish/revise, read-only public-to-department availability | `/hod/quotas`, `/hod/quotas/:poolId`, `/app/offerings/:offeringId` | PostgreSQL quota invariant |
| Q02 atomic submit | Draft, eligibility review, submit and receipt | `/app/applications/new/*`, `/app/applications/:id` | Submit transaction + idempotency |
| Faculty -> DRC -> HoD review | Dedicated DRC and HoD queues/details | `/drc/reviews`, `/hod/reviews`, `/app/applications/:id` | Current authority resolver |
| DRC applicant direct HoD | No self-review queue/task; explicit route explanation | `/app/applications/:id`, `/hod/reviews/:taskId` | Role-aware approval state machine |
| Q19–Q23 chronology/integrity | Enrollment status, warning, formal review and immutable findings | `/app/participation/:id`, `/hod/integrity...` | Evidence + integrity engine |
| Repeat eligibility Q27–Q34 | Prior-attempt verification, no-repeat warnings, correction cases | `/app/previous-attempts`, `/hod/outcome-verification` | Canonical course + verification |
| Q35–Q38 annual completion | Academic-year selector, 8-week vs 2x4-week evidence and pending states | `/app/compliance/annual`, `/principal/reports/annual` | Annual compliance engine |
| Q39–Q50 subject Silver | Subject deadlines, score/relevance, pre/post-separation history | `/app/compliance/silver`, `/app/compliance/silver/:obligationId` | Silver obligation engine |
| Q41–Q49 separation | Effective-event-date decisions, closure audit, retrospective credit | `/hod/separation-cases`, `/admin/employment`, `/app/history` | Employment + separation resolver |
| Cross-year exam rescheduling | Original/current/target pools, capacity-check transfer and failure case | `/hod/quota-transfers`, `/app/applications/:id/quota` | Serializable transfer transaction |
| Principal global oversight | Institution-wide read-only drilldowns | `/principal/*` | Read-scoped institutional permissions |
| Admin source-data governance | Staff, episodes, offices, assignment and subject sources | `/admin/*` | Versioned institutional source records |
| Audit/report reproducibility | As-of vs latest, immutable event timeline, export provenance | `/principal/audit`, `/hod/reports`, `/app/applications/:id/history` | Append-only audit and snapshots |
| Provider uncertainty and policy ambiguity | Provenance warnings, blocked controls and case state | Throughout | Verified state, policy-pending cases |

## DELIVERABLE 2 — Visual design research and selected direction

**Chosen aesthetic:** 'Institutional Operations' — restrained light enterprise SaaS with high-density but readable information, deliberate borders, one blue emphasis color, few status pills, sparse functional icons and well-aligned data tables. Not a financial trading dashboard, not university marketing, not a generic AI template. UI inspiration is LIMITED to public design principles, never brand copying.

- GitHub Primer: PageHeader, nested navigation/list detail, precise action hierarchy, contextual content separation: https://primer.style/product/components/ and https://primer.style/product/ui-patterns/navigation/ .
- Atlassian navigation system: globally consistent top navigation and app-specific collapsible side navigation: https://atlassian.design/components/navigation-system/migration-guide .
- IBM Carbon: searchable/filterable sortable operational data tables, with row detail pages when work becomes complex: https://v10.carbondesignsystem.com/components/data-table/usage/ .
- U.S. Web Design System: explicit step indicators for genuine linear multi-page forms: https://designsystem.digital.gov/components/step-indicator/ .
- WCAG 2.2: https://www.w3.org/TR/WCAG22/ ; meet AA, prioritize keyboard focus, understandable errors, target sizing and text contrast.

Only inspect these as documented design patterns; do not claim exact product visuals were copied or rights to proprietary assets. AKUS must have its own design tokens, type scale and identity.

### Product identity and visual voice

Working UI name: 'AKUS | NPTEL'. Top left a compact typographic AKUS mark and institutional label if provided by deployment configuration; do not fabricate an official crest. Tone: formal, plain English, explain blockers concretely. Use full labels 'Awaiting HoD review', 'Exam date unverified', 'Topic mapping pending', 'Quota transfer blocked' instead of ambiguous colors or cryptic acronyms.

### Visual anti-pattern exclusions

No giant gradient hero, emoji menu, stock photographs on dashboards, glassmorphism, purple/cyan neon, excessive rounded cards, huge KPI tiles, charts without decision value, dense modals for core tasks, skeletons that lie about loaded state, randomly chosen spacing, every page as repeated card grid, placeholder metrics or buttons without server action.

## DELIVERABLE 3 — Sitemap and role navigation

**Global shell:** Top bar (product, institution, breadcrumbs-compatible context, search, notifications, help, profile); left role-filtered side nav; content area; optional narrow contextual inspector only on pages where records benefit from linked evidence/history.

**Shared:** Home; NPTEL Catalog; My Applications; My Compliance; Tasks (scoped); Notifications; Profile; Help/Policy Glossary. HoD/Principal exemption removes 'My NPTEL' applicant/compliance actions; Admin role alone does not add personal NPTEL duties.

**Faculty:** Overview; Catalog (Courses -> Course -> Offering); My applications (List -> Draft workflow -> Submission receipt -> Detail / Evidence / Quota / History); Prior Attempts; Participation Evidence; Annual Compliance (Year detail); Subject-wise Silver (List -> Obligation detail); Notifications.

**DRC Head:** All Faculty navigation plus 'DRC Reviews' list -> Review detail -> Historic DRC decisions; own applications remain in My Applications and route directly HoD.

**HoD:** Department Overview; Application Reviews -> Decision detail; Topic Governance -> Mapping Queue / Mapping Detail / Mapping Review / Taxonomy; Annual Topic Quotas -> Pool List / Pool Detail / Publish or Revise / Ledger; Exception Work -> Blocked Quota Transfers / Transfer Detail / Outcome Verification / Integrity Reviews / Separation Reviews / Chronology Review; Reports -> Department Compliance / Quota / Applications; Decision History.

**Principal:** Institutional Overview; Departments -> Department Detail; Institution-wide Applications; Topics & Quotas; Compliance -> Annual / Silver; Exception Monitoring; Audit & Historical Reports. All default read-only; pending special-emerging-tech approval authority is not enabled until policy resolved.

**Admin:** Institutional Data -> Staff / Staff Detail / Employment Episodes / Role Appointments / Teaching Assignments / Departments / Subjects / Academic Years; NPTEL Reference Data -> Provider Sync / Offering Provenance / Canonical Topics / Course Identity; Operations -> Jobs / Notifications / Integration Health / Audit (restricted). No HoD topic mapping/quotas academic approval through Admin-only rights.

**Utilities:** `/login`, `/auth/callback`, `/access-denied`, `/system-unavailable`, `/not-found`. Notification links deep-link directly to authorized target and preserve filter/back context. Invalid/expired office appointments must remove actions and redirect/revalidate, not rely on cached navigation visibility.

## DELIVERABLE 4 — Complete page inventory and route architecture

Roles in route inventory: F=Faculty, D=DRC Head, H=HoD/acting HoD, P=Principal, A=Admin. D inherently has F self-service capabilities; scopes and the authority at action time are always determined on backend. 'R' = read-only role for this route. Dynamic IDs are opaque, never user-supplied grants. The following are meaningful routes, not an arbitrary page-count target.
| ID | Page | Route | Roles | Primary action | Parent |
|---|---|---|---|---|---|
| PUB-01 | Institutional sign-in | `/login` | All unauthed | Continue with Google -> server OIDC authorization | Public |
| PUB-02 | OAuth return | `/auth/callback` | Authenticated redirect | On success redirect to role-appropriate home or original safe in-app l | Sign-in |
| PUB-03 | Access denied / not provisioned | `/access-denied` | All | Sign out | Sign-in |
| PUB-04 | Service unavailable | `/system-unavailable` | All | Retry and return to login. | Global |
| PUB-05 | Not found | `/not-found` | All | Go to authorized home or back | Global |
| SHR-01 | Task inbox | `/app/tasks` | F,D,H,P(R),A(scope) | Open exact task detail | Home |
| SHR-02 | Notifications | `/app/notifications` | F,D,H,P,A | Open relevant record, mark read, filter, change personal notification  | Top bar |
| SHR-03 | Profile and authority | `/app/profile` | F,D,H,P,A | Sign out, open permitted history, request source correction via Admin  | Account menu |
| SHR-04 | Help and policy glossary | `/app/help` | F,D,H,P,A | Search term, open policy details, open relevant workflow. | Help |
| SHR-05 | Global search | `/app/search` | F,D,H,P,A | Search, filter by type/department where authorized, open result. | Top search |
| FAC-01 | Faculty overview | `/app/home` | F,D | Browse catalog, resume draft, open application, upload evidence, inspe | Home |
| FAC-02 | NPTEL course catalog | `/app/catalog` | F,D,H(R),P(R) | Select canonical course | Catalog |
| FAC-03 | Canonical course detail | `/app/catalog/:courseId` | F,D,H(R),P(R) | Select exact offering | Catalog |
| FAC-04 | Exact NPTEL offering | `/app/offerings/:offeringId` | F,D,H(R),P(R) | Start application draft if eligible | Course detail |
| FAC-05 | Application drafts and applications | `/app/applications` | F,D,H(R),P(R) | Open draft, detail, copy safe application link | My applications |
| FAC-06 | New application — offering | `/app/applications/new/offering` | F,D | Change offering, continue after eligibility preliminaries, save draft. | Applications |
| FAC-07 | New application — eligibility | `/app/applications/new/eligibility` | F,D | Save draft | Wizard |
| FAC-08 | New application — evidence | `/app/applications/new/evidence` | F,D | Upload/remove unsubmitted attachment, preview with permissions, save d | Wizard |
| FAC-09 | New application — review and submit | `/app/applications/new/review` | F,D | Submit once with idempotency | Wizard |
| FAC-10 | Application detail | `/app/applications/:applicationId` | F,D,H(scope),P(R) | Upload enrollment/cert proof, permitted withdraw, open quota history,  | Applications |
| FAC-11 | Application quota and movements | `/app/applications/:applicationId/quota` | F,D,H(scope),P(R) | Open transfer-case detail if authorized, link to quota glossary. | Application |
| FAC-12 | Application evidence | `/app/applications/:applicationId/evidence` | F,D,H(scope),P(R) | Upload, replace via new revision, request status, download authorized  | Application |
| FAC-13 | Application timeline and audit | `/app/applications/:applicationId/history` | F,D,H(scope),P(R) | Filter milestones, view permitted event details. | Application |
| FAC-14 | External participation evidence | `/app/participation/:applicationId` | F,D,H(scope),P(R) | Declare/enclose evidence, view verification, follow external provider  | Application |
| FAC-15 | Prior attempts and repeat eligibility | `/app/previous-attempts` | F,D | Open attempt detail | My compliance |
| FAC-16 | Prior-result verification request | `/app/previous-attempts/:attemptId` | F,D,H(scope) | Submit evidence, view outcome | Prior attempts |
| FAC-17 | Annual compliance overview | `/app/compliance/annual` | F,D,H(R),P(R) | Select year, open year detail, open certificate evidence. | My compliance |
| FAC-18 | Annual academic year detail | `/app/compliance/annual/:yearId` | F,D,H(R),P(R) | Open application/course/certificate | Annual |
| FAC-19 | Subject-wise Silver list | `/app/compliance/silver` | F,D,H(R),P(R) | Open subject obligation, filter overdue and evidence pending. | My compliance |
| FAC-20 | Silver subject obligation detail | `/app/compliance/silver/:obligationId` | F,D,H(scope),P(R) | Open evidence, view reassessment, request source correction. | Silver |
| FAC-21 | Certificate library | `/app/certificates` | F,D,H(R),P(R) | Upload permitted evidence through linked application, inspect result. | My compliance |
| DRC-01 | DRC review queue | `/drc/reviews` | D | Open review | DRC Reviews |
| DRC-02 | DRC application review | `/drc/reviews/:taskId` | D | Approve/reject with rationale and confirmation, return to queue on suc | Queue |
| DRC-03 | DRC decision history | `/drc/history` | D | Open review record read-only, filter dates. | DRC Reviews |
| HOD-01 | Department overview | `/hod/home` | H | Open review, quota pool, mapping request, blocked transfer. | Department |
| HOD-02 | Final approval queue | `/hod/reviews` | H | Open decision task | Approvals |
| HOD-03 | Final decision workspace | `/hod/reviews/:taskId` | H | Approve/reject with idempotent submission, view audit. | Approvals |
| HOD-04 | Primary topic mappings | `/hod/topic-mappings` | H | Open mapping detail, intake queue, propose authorized revision. | Topic governance |
| HOD-05 | Topic mapping requests | `/hod/topic-mappings/requests` | H | Open mapping decision | Topic governance |
| HOD-06 | Mapping detail and revisions | `/hod/topic-mappings/:courseId` | H | Open new mapping decision, view revision evidence, navigate quotas. | Topic governance |
| HOD-07 | Approve or revise mapping | `/hod/topic-mappings/:courseId/edit` | H | Approve/revise after confirmation | Mapping detail |
| HOD-08 | Canonical topic directory | `/hod/topics` | H,A(reference),P(R) | HoD open mapping or request catalog correction | Topic governance |
| HOD-09 | Annual quota pools | `/hod/quotas` | H | Open pool | Quotas |
| HOD-10 | Quota pool detail | `/hod/quotas/:poolId` | H | Publish/revise, inspect applicant/reservation and ledger. | Quotas |
| HOD-11 | Publish/revise annual quota | `/hod/quotas/:poolId/edit` | H | Publish or revise | Quota detail |
| HOD-12 | Quota allocation ledger | `/hod/quotas/:poolId/ledger` | H,P(R) | Open event/app, filter, export with as-of metadata. | Quota detail |
| HOD-13 | Quota transfer case inbox | `/hod/quota-transfers` | H | Open case | Exception work |
| HOD-14 | Quota transfer case detail | `/hod/quota-transfers/:caseId` | H,P(R) | Open target quota publish/revise | Transfer inbox |
| HOD-15 | Prior-result verification inbox | `/hod/outcome-verifications` | H | Open verification case | Exception work |
| HOD-16 | Prior-result decision | `/hod/outcome-verifications/:caseId` | H | Verify unsuccessful, verify certificate, mark unresolved | Verification inbox |
| HOD-17 | Integrity-review inbox | `/hod/integrity` | H,P(R) | Open case if authorized | Exception work |
| HOD-18 | Integrity-review detail | `/hod/integrity/:caseId` | H,P(R) | Authorized reviewer uphold/invalidate, view report | Integrity |
| HOD-19 | Separation-closure inbox | `/hod/separation-cases` | H | Open case | Exception work |
| HOD-20 | Separation chronology case | `/hod/separation-cases/:caseId` | H | Verify and formally close+release when authorized | Separation inbox |
| HOD-21 | Department annual report | `/hod/reports/annual` | H,P(R) | Filter by year/role/state, export if granted, open detail. | Reports |
| HOD-22 | Department Silver report | `/hod/reports/silver` | H,P(R) | Filter subject/status/AY, drill obligation. | Reports |
| HOD-23 | Department application report | `/hod/reports/applications` | H,P(R) | Filter, export, click row, inspect historical audit. | Reports |
| HOD-24 | HoD decision history | `/hod/decisions` | H | Open record readonly | Department |
| PRN-01 | Institution overview | `/principal/home` | P | Drill into department/report/application | Institution |
| PRN-02 | Departments overview | `/principal/departments` | P | Open department detail | Departments |
| PRN-03 | Department drilldown | `/principal/departments/:departmentId` | P | Open specific report/app/case. | Departments |
| PRN-04 | Institution-wide applications | `/principal/applications` | P | Open application details and permitted evidence | Institution |
| PRN-05 | Institution topic quotas and mappings | `/principal/topics-quotas` | P | Open mapping revision or quota ledger in read-only mode. | Institution |
| PRN-06 | Institution annual compliance | `/principal/reports/annual` | P | Filter, export provenance, navigate staff. | Compliance |
| PRN-07 | Institution Silver compliance | `/principal/reports/silver` | P | Open specific detail, export as-of vs latest. | Compliance |
| PRN-08 | Institution exception monitoring | `/principal/exceptions` | P | Open detail | Oversight |
| PRN-09 | Institution audit and as-of reporting | `/principal/audit` | P | Search, inspect event, export authorized evidence. | Oversight |
| ADM-01 | Administration overview | `/admin/home` | A | Open staff/appointment/sync correction pages. | Admin |
| ADM-02 | Staff directory | `/admin/staff` | A | Open staff detail | Staff |
| ADM-03 | Staff detail | `/admin/staff/:staffId` | A | Add authorized episode, office or assignment via dedicated page. | Staff |
| ADM-04 | Employment episodes | `/admin/staff/:staffId/employment` | A | Add/correct episode, view impact preview for applications and Silver. | Staff detail |
| ADM-05 | Office appointments | `/admin/appointments` | A | Create/revise authorized appointment with reason | Institutional data |
| ADM-06 | Teaching assignments | `/admin/teaching-assignments` | A | Add/correct authorized assignment, inspect impacted obligation. | Academic data |
| ADM-07 | Departments and canonical subjects | `/admin/academic-reference` | A | Create/correct references, view impacted courses or teaching. | Academic data |
| ADM-08 | Academic years | `/admin/academic-years` | A | Create period, review published year | Academic data |
| ADM-09 | NPTEL provider synchronization | `/admin/nptel-sync` | A | Run authorized refresh, inspect details, retry worker job. | Reference data |
| ADM-10 | Provider metadata versions | `/admin/nptel-offerings` | A | Open offering, flag ambiguous data, run authorized reconciliation. | Reference data |
| ADM-11 | Work-ledger operations | `/admin/operations` | A | Retry authorized safe job, inspect history | Operations |
| ADM-12 | Notifications configuration | `/admin/notifications` | A | Edit approved template settings, send test if safe. | Operations |
| ADM-13 | Administrative audit | `/admin/audit` | A | Search, inspect, export within authorization. | Operations |

## DELIVERABLE 5 — Production design system: exact implementable tokens

### Color tokens (all light theme)

| Token | Hex | Use |
|---|---|---|
| canvas | `#F7F9FC` | Main application background |
| surface | `#FFFFFF` | Page/side navigation surfaces |
| surface-subtle | `#F3F6FA` | Neutral grouped metadata, hover surfaces |
| surface-selected | `#EDF4FF` | Selected nav, row focus |
| brand-primary | `#1D4ED8` | Main action, selected link, focus association |
| brand-hover | `#1E40AF` | Interactive hover |
| brand-pressed | `#1E3A8A` | Pressed |
| text-strong | `#111827` | Titles and essential data |
| text-primary | `#243247` | Body and table cells |
| text-secondary | `#536176` | Supporting descriptions |
| text-muted | `#66758C` | Dates and metadata on white |
| border | `#DCE3EC` | Hairlines, table separation |
| border-subtle | `#E9EDF3` | Inset sections |
| focus | `#2563EB` | Focus outline, with 2px exterior gap |
| success-text | `#065F46` | Verified/fulfilled text |
| success-bg | `#ECFDF5` | Restrained verified state background |
| warning-text | `#92400E` | Attention/pending text |
| warning-bg | `#FFFBEB` | Pending evidence/transfer background |
| danger-text | `#991B1B` | Rejected/blocker text |
| danger-bg | `#FEF2F2` | Critical validation feedback |
| info-text | `#1E40AF` | Neutral information callout |
| info-bg | `#EFF6FF` | Verified explanation if useful |
| disabled-bg | `#F1F4F8` | Disabled controls |
| disabled-text | `#8793A6` | Disabled text |

Do not use semantically colored badges as visual decoration; use muted state treatment only where operational. Charts use accessible contrasts and textual equivalent tables.

### Typography, scale, spatial system

- Prefer Inter or a licensing-safe system sans stack `Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif`. Do not bundle proprietary font files. Weights 400, 500, 600, 700.
- Desktop main title: 26px/34px weight 650; compact page title 24px/32px; section title 17px/24px weight 600; data subheading 15px/22px weight 600; body 14px/21px; table 13px/19px; small metadata 12px/18px; never body below 13px in dense screens without explicit accessibility fallback.
- Spacing tokens: 2, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64px. Do not invent one-off spacing without component justification. Thin borders 1px. Radii: 4px inputs/table row indicators, 6px buttons, 8px panels/dialogs, 12px only for rare overview grouping. Never use giant 24px cards.
- Shadow popover: `0 8px 24px rgba(18,32,52,0.12)`; raised dialog: `0 18px 56px rgba(18,32,52,0.18)`; normal cards have no shadow or very thin neutral border.
- Component widths: single long form 720–800px; editorial/detail reading column 840px; operational detail and tables max 1440px; default body main width 1220–1360px according to route; left/right rail 280–320px where applicable.

### Global shell dimensions and behavior

- Top bar height **60px**, white background, 1px bottom border, fixed only if keyboard focus isn't obscured; product label left, global search 320px at ≥1280px, right notifications/help/profile. Sign out in account menu. Current role and department are accurate labels, not privileged self-selection.
- Sidebar width **248px** expanded, **64px** collapsed, white with 1px right border; logical section groups; nav row **38–40px**; icon 18px; active row `#EDF4FF` with blue 3px inset; text 13–14px weight 500. Persist expansion preference locally only, not authorization. App-specific navigation belongs here; top bar contains global actions.
- Main desktop page gutter **32px** at ≥1280, **24px** on laptop, **16px** on mobile; top content padding **24px**; between major sections 24px; compact dense worklists instead of oversized overview cards.
- Default content reading width 1160px for mixed pages, data grids 1400px, forms 760px. Breadcrumb row 12px/18px above title; Page header 24–26px title left and maximum two primary actions right; supporting line 13px muted below.
- If a user clicks a row from filtered list, carry list filters in URL query parameters or navigation state and restore list scroll/focus on return. Deep links remain valid on reload, with server permission denial gracefully handled.
- Responsive: desktop ≥1280 sidebar 248; 1024–1279 sidebar collapsible 64/248; 768–1023 off-canvas nav with proper focus trap; <768 off-canvas nav, top bar condensed, forms one column, tables horizontal scroll/priority layouts. Do not hide audit/status fields; allow detail drilldown.

### Component dimensions and states

| Component | Specification | Behavior |
|---|---|---|
| Primary button | height 38px (44px touch), 14px medium, radius 6px, blue white text | Loading disables duplicates; pending label; never claim success before API |
| Secondary button | height 38px, white background, 1px border `#CAD4E0` | Hover neutral; focused outline; minimal icon |
| Destructive decision | outlined danger by default; red only at final confirmation | Explain effects: release quota, audit permanence, non-reversible outcome |
| Input/select | height 38–40px, 1px border, radius 5px, label above | Error text under field, associated accessible description and aria-invalid |
| Date field | explicit local date format and timezone/precision label | Never invent 00:00 from date-only source |
| File upload | bordered 100% width, document type and size, status timeline | Pending scan/verification clearly separate |
| Table | header 40px, rows 46px normal/40px dense, 12–16px horizontal padding | Server pagination, multi-criteria filters, sticky header only if useful, keyboard row links |
| Status indicator | small inline text and minimal pill background where risk significant | Text conveys meaning without dependence on color |
| Drawer | 360px desktop, contextual only, close Esc | Not for critical multi-step approvals |
| Dialog | 480–560px max, 8px radius, explicit action consequences | Keyboard trap/restored focus; only brief confirmations |
| Tabs | underline style, 40px height | URL route/subroute on record detail pages; arrow keyboard semantics |
| Toast | subtle, max 1–2 stacked, 5–7s noncritical | Error persists near affected task; action results sourced from server |
| Timeline | slim vertical rule, dated events and actor-office labels | Effective time and recorded time visibly distinct |
| Empty state | concise title, why, valid next step | No decorative oversized illustration |
| Skeleton | exact geometry of awaited content | Respect reduced motion; error fallback available |
| Filters | Search+quick filters in toolbar; advanced in collapsible panel | Query state persisted; Clear filters resets result count |

### Keyboard and accessibility contract

Use semantic landmarks and headings, labels, real table headers and accessible name for every action. WCAG 2.2 AA minimum: normal text ≥4.5:1 contrast, non-text essential visual cues ≥3:1, reflow without lost function at 320 CSS px where applicable, keyboard focus visible and not obscured, adequate target dimensions/spacing, proper error announcement, no hover-only information, reduced motion respected, screen reader stage announcement after async server transitions. Prefer 40–44px controls for touch even where WCAG minimum is smaller. Test zoom at 200% and 400%, focus restoration after dialogs, keyboard-only form submission, status text clarity and colorblind use.

### Form and data-table common behavior

Each long wizard step has one h1, an explicit step label, Save Draft and Back, field errors and keyboard navigable Continue. On submit, display the exact quota topic, expected exam year, current published capacity, and authoritative warning that AKUS does not enroll on NPTEL. Drafts do not reserve seats. Use three confirmation patterns only: ordinary save toast, consequential submit confirmation with substantive context, destructive action dialog with consequences and rationale. Tables support server search, sort, pagination, empty filters, and URL persistence; use dedicated detail route instead of cramming case workflows into expanded rows.

## DELIVERABLE 6 — Full page-by-page UX and interaction specifications
Each page has the complete design contract below. The shared application shell, design tokens, accessibility rules, error patterns, and role-gated navigation are inherited by all pages. These shared rules are not substitutes for the page-specific content. The descriptions name actual AKUS data sources and actions rather than decorative mockups.
### PAGE PUB-01: Institutional sign-in
**Route and navigation:** `/login`; section **Public/Auth**; parent **Public**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** All unauthed. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Give authorized institutional staff one clear login entry point.
**Complete visual structure:** Centered narrow white sign-in panel, typographic AKUS mark, restrained institution label, short explanation, Google SSO action and privacy/support footnote; no fake testimonials or faculty signup.
**Actual project data:** Configured institution label, auth provider availability, maintenance notice.
**Interactions and destinations:** Continue with Google -> server OIDC authorization; link Support policy.
**Expected loading/empty/error/read-only states:** Sign-in loading, provider error, blocked browser cookie, expired callback. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /auth/login. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Never collect institutional Google passwords in AKUS.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PUB-02: OAuth return
**Route and navigation:** `/auth/callback`; section **Public/Auth**; parent **Sign-in**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** Authenticated redirect. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Explain the security handoff while processing OIDC.
**Complete visual structure:** Small neutral loading message centered; subtle spinner; accessible status narration; no marketing hero.
**Actual project data:** Auth callback session outcome, mapped staff identity, current allowed contexts.
**Interactions and destinations:** On success redirect to role-appropriate home or original safe in-app link.
**Expected loading/empty/error/read-only states:** Expired state, nonce rejection, account mismatch, network error and retry link. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /auth/google/callback. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No client-trusted role assignments.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PUB-03: Access denied / not provisioned
**Route and navigation:** `/access-denied`; section **Public/Auth**; parent **Sign-in**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** All. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Explain why Google login does not imply institutional authorization.
**Complete visual structure:** Titled explanation, reference-safe error code, signed-in account label if safe, admin contact mechanism; no app sidebar.
**Actual project data:** Provisioning failure cause code, support contact configuration.
**Interactions and destinations:** Sign out; try institutional account; submit support request only if configured.
**Expected loading/empty/error/read-only states:** Unprovisioned, revoked, disabled, missing home department, conflicting roles. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /me. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Never leak staff registry details to unprovisioned users.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PUB-04: Service unavailable
**Route and navigation:** `/system-unavailable`; section **Public/Auth**; parent **Global**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** All. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Provide honest recovery during maintenance or server failure.
**Complete visual structure:** Service status title, neutral illustration-free typography, Retry and operational support, optional service notice timestamp.
**Actual project data:** Health status if public safe, correlation ID.
**Interactions and destinations:** Retry and return to login.
**Expected loading/empty/error/read-only states:** Planned outage versus unexpected failure; offline no false success. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /health. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not leak deployment paths, tokens or stack traces.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PUB-05: Not found
**Route and navigation:** `/not-found`; section **Public/Auth**; parent **Global**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** All. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Recover from invalid links.
**Complete visual structure:** Compact left-aligned error and clear Back/Home navigation.
**Actual project data:** Current safe navigation context.
**Interactions and destinations:** Go to authorized home or back; sign-in when required.
**Expected loading/empty/error/read-only states:** 404 versus unauthorized 403 distinct. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** Router + server resource lookup. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not reveal existence of unauthorized records.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE SHR-01: Task inbox
**Route and navigation:** `/app/tasks`; section **Shared**; parent **Home**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H,P(R),A(scope). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Show authorized personal actions and reviews in one consistent entry point.
**Complete visual structure:** Title, count by actionable stage, source-filter toolbar, dense table with task, subject, deadline, assigned capacity, linked record and date; right supplementary urgency legend.
**Actual project data:** Scoped tasks, authority appointments, case types, due dates, versions.
**Interactions and destinations:** Open exact task detail; dismiss personal notification (not task); filter.
**Expected loading/empty/error/read-only states:** Empty, stale assignment, pending authority transfer, deleted task, permission changed. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /tasks. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Tasks never imply approval rights outside active office.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE SHR-02: Notifications
**Route and navigation:** `/app/notifications`; section **Shared**; parent **Top bar**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H,P,A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Show delivery and action history with read/unread without replacing domain state.
**Complete visual structure:** Two-column on desktop unread/all filter and message list, right detail preview; mobile single column; real date/time.
**Actual project data:** Notification ID, target URL, type, read state, sent timestamp.
**Interactions and destinations:** Open relevant record, mark read, filter, change personal notification preferences.
**Expected loading/empty/error/read-only states:** Delivery pending, inaccessible target, duplicate message, retry. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /me/notifications. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No personal secrets in notification summaries.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE SHR-03: Profile and authority
**Route and navigation:** `/app/profile`; section **Shared**; parent **Account menu**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H,P,A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Explain authoritative identity, department, role grants and employment period.
**Complete visual structure:** Two-column profile details and effective-dated appointments; read-only sourced fields with correction-request guidance; sign out separate.
**Actual project data:** Stable staff ID, display name, home department, appointment validity, episode, email.
**Interactions and destinations:** Sign out, open permitted history, request source correction via Admin workflow.
**Expected loading/empty/error/read-only states:** No active appointment, identity mismatch, rehire, multi-role constraints. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /me /me/roles. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No local self-service role toggles that grant privileges.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE SHR-04: Help and policy glossary
**Route and navigation:** `/app/help`; section **Shared**; parent **Help**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H,P,A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Explain AKUS vs external NPTEL and common policy terms.
**Complete visual structure:** Searchable left glossary index, right article panel with examples, direct anchors and support contact.
**Actual project data:** Versioned approved policy summaries, provider limitations, support info.
**Interactions and destinations:** Search term, open policy details, open relevant workflow.
**Expected loading/empty/error/read-only states:** Unratified policy content clearly labeled pending; missing help. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /policy/help. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No policy statement outside approved source.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE SHR-05: Global search
**Route and navigation:** `/app/search`; section **Shared**; parent **Top search**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H,P,A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Locate permitted applications, offerings, topics and documents quickly.
**Complete visual structure:** Compact search header, result types sidebar, grouped dense list with safe excerpts, actions as links.
**Actual project data:** Server-scoped result sets with type, excerpt, timestamp, canonical ID.
**Interactions and destinations:** Search, filter by type/department where authorized, open result.
**Expected loading/empty/error/read-only states:** No matches, no permission, pagination, partial provider data. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /search. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Never return metadata for records outside scope.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-01: Faculty overview
**Route and navigation:** `/app/home`; section **Faculty**; parent **Home**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Prioritize faculty obligations and active NPTEL actions.
**Complete visual structure:** At top 3 compact horizontal text metrics: current AY annual state, active applications, approaching Silver deadlines; below two-column actionable applications/obligations; recent timeline at bottom.
**Actual project data:** Annual status, application stages, counts, deadlines, evidence blockers.
**Interactions and destinations:** Browse catalog, resume draft, open application, upload evidence, inspect Silver obligation.
**Expected loading/empty/error/read-only states:** No offerings, new staff, overdue, pending certificate, separated/revoked. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /dashboard/faculty. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No unrelated decorative graphs.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-02: NPTEL course catalog
**Route and navigation:** `/app/catalog`; section **Faculty**; parent **Catalog**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(R),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Search legitimate provider canonical courses and inspect offerings.
**Complete visual structure:** Search bar, left filters for duration/provider category/status, right compact list/table with canonical title, run count, area, data freshness, upcoming exam year.
**Actual project data:** Course identity, aliases, provider categories, offering count.
**Interactions and destinations:** Select canonical course; filter, search, sort; open stale-data explanation.
**Expected loading/empty/error/read-only states:** Provider unavailable, no results, stale snapshots; visible no-fake availability state. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /nptel/courses. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Catalog browsing does not reserve seats.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-03: Canonical course detail
**Route and navigation:** `/app/catalog/:courseId`; section **Faculty**; parent **Catalog**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(R),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Explain one underlying course and its distinct runs.
**Complete visual structure:** Header course title/canonical ID, content summary left, tabular offering list below, provider categories and mapped departmental primary topic right.
**Actual project data:** Canonical course, run IDs, duration variations, provider labels, departmental mapping revision.
**Interactions and destinations:** Select exact offering; view provider citation; view accepted relevance if authorized.
**Expected loading/empty/error/read-only states:** Unmapped course, no runs, alias collision, archived course. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /nptel/courses/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Provider category tags are not individual quota reservations.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-04: Exact NPTEL offering
**Route and navigation:** `/app/offerings/:offeringId`; section **Faculty**; parent **Course detail**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(R),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Give complete eligibility facts for one specific run before draft.
**Complete visual structure:** Title + run ID + source freshness, date-detail table of course start/end, enrollment cutoff, exam registration cutoff, scheduled exam, duration; topic/quota panel to side; evidence caveat below.
**Actual project data:** Metadata version/source, date precision, mapped topic, charged AY, current cap/count, age.
**Interactions and destinations:** Start application draft if eligible; open exact provider page; request topic mapping; view why blocked.
**Expected loading/empty/error/read-only states:** Expired enrollment, no approved mapping, unpublished quota, provider uncertain, wrong exam year. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /nptel/offerings/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Disclose tentative exam and hall-ticket correction risk.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-05: Application drafts and applications
**Route and navigation:** `/app/applications`; section **Faculty**; parent **My applications**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(R),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** See all own cases by canonical course and current lifecycle.
**Complete visual structure:** Search/filter toolbar and table: course/run, submission, DRC/HoD stage, charging topic, initial AY, current charged pool, enrollment, status; saved filter URL.
**Actual project data:** Own application and draft list with server versions and timestamps.
**Interactions and destinations:** Open draft, detail, copy safe application link; start new from catalog.
**Expected loading/empty/error/read-only states:** Empty, no matches, policy suspension, stale data. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /applications. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not conflate AKUS submission with external enrollment.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-06: New application — offering
**Route and navigation:** `/app/applications/new/offering`; section **Faculty**; parent **Applications**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Choose exact offering with no ambiguity.
**Complete visual structure:** Narrow 760px wizard page, 4-step indicator, catalog-backed selected course card with run dates, warnings below.
**Actual project data:** Selected offering, canonical ID, exam year, time-sensitive metadata.
**Interactions and destinations:** Change offering, continue after eligibility preliminaries, save draft.
**Expected loading/empty/error/read-only states:** Provider unknown, course repeated, exam missing, loading. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /nptel/offerings + POST /applications/drafts. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No quota reservation in draft.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-07: New application — eligibility
**Route and navigation:** `/app/applications/new/eligibility`; section **Faculty**; parent **Wizard**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Capture honest required declarations and evidence without redundant profile entry.
**Complete visual structure:** Left stacked sections: subject relevance, score sharing Yes, prior attempt, enrollment chronology, special-course classification; right nonsticky contextual policy note and verified source facts.
**Actual project data:** Canonical identity, teaching subjects, prior certified outcomes, date snapshots.
**Interactions and destinations:** Save draft; continue; review current eligibility issues.
**Expected loading/empty/error/read-only states:** Invalid date, not yet verified prior outcome, unapproved mapping; field-specific errors. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** PATCH /applications/drafts/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Applicant never selects charging topic or approval chain.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-08: New application — evidence
**Route and navigation:** `/app/applications/new/evidence`; section **Faculty**; parent **Wizard**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Attach required proofs with status and provenance.
**Complete visual structure:** Document list with file dropzone, type selector, filename/size, verification status, privacy notice; continue button.
**Actual project data:** Files, type, checksum, source, scanned status, policy-required evidence flags.
**Interactions and destinations:** Upload/remove unsubmitted attachment, preview with permissions, save draft.
**Expected loading/empty/error/read-only states:** Scan failed, oversized file, unsupported type, offline retry. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** POST /evidence + PATCH /drafts. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Upload not automatically genuine evidence.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-09: New application — review and submit
**Route and navigation:** `/app/applications/new/review`; section **Faculty**; parent **Wizard**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Make valid binding submission transparent and intentional.
**Complete visual structure:** Two-column review summary and locked quota forecast showing department/topic/year/pool, DRC vs direct-HoD route; declarations checklist; prominent single Submit with confirmation dialog.
**Actual project data:** Validated draft, published quota version, scheduled exam metadata version, eligibility checklist.
**Interactions and destinations:** Submit once with idempotency; edit section; confirm internal-not-external enrollment.
**Expected loading/empty/error/read-only states:** Last-seat contention, mapper revision race, full quota, expired deadline, duplicate canonical active app. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** POST /applications/{id}/submit. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Only server success gives submitted ID and HELD seat.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-10: Application detail
**Route and navigation:** `/app/applications/:applicationId`; section **Faculty**; parent **Applications**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(scope),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Present complete single-case operational truth and actions.
**Complete visual structure:** Page header with course/run, stage, one narrow right action panel, main overview with stages, required actions, provider chronology and source link; lower tabs for evidence, quota, timeline.
**Actual project data:** Applicant, route, approvals, topic mapping revision, initial/current pool, enrollment, deadlines, exceptions.
**Interactions and destinations:** Upload enrollment/cert proof, permitted withdraw, open quota history, view decision.
**Expected loading/empty/error/read-only states:** Closed, under review, rejection, integrity hold, separation, mapping and transfer caveats. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /applications/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Historical decisions never overwritten.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-11: Application quota and movements
**Route and navigation:** `/app/applications/:applicationId/quota`; section **Faculty**; parent **Application**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(scope),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Explain original versus current reservation and transfer issues.
**Complete visual structure:** Side-by-side initial/current pool cards, movement ledger table, event-date provenance, pending target transfer case callout.
**Actual project data:** Original topic/year at submit, current topic/pool, movement records, failure reason.
**Interactions and destinations:** Open transfer-case detail if authorized, link to quota glossary.
**Expected loading/empty/error/read-only states:** Failed cross-year move shows original counted and target NOT reserved. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /applications/{id}/quota-transfer-history. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not fabricate available capacity from future pools.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-12: Application evidence
**Route and navigation:** `/app/applications/:applicationId/evidence`; section **Faculty**; parent **Application**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(scope),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Organize enrollment, exam, certificate, correction evidence by status.
**Complete visual structure:** Evidence list grouped by claim type, verification status, provenance and uploaded-at; large preview via separate pane; upload action for applicant if eligible.
**Actual project data:** Evidence ID, source, checksum, claims, revisions, reviewer findings.
**Interactions and destinations:** Upload, replace via new revision, request status, download authorized attachment.
**Expected loading/empty/error/read-only states:** Pending scan, unresolved genuine source, corrected doc, expired access. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /applications/{id}/evidence. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No silent replacement of evidence version.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-13: Application timeline and audit
**Route and navigation:** `/app/applications/:applicationId/history`; section **Faculty**; parent **Application**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(scope),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Explain every consequential lifecycle and quota event chronologically.
**Complete visual structure:** Vertical subdued dated audit timeline grouped by stage with actor capacity, policy code, old/new states, evidence links and as-of selector.
**Actual project data:** Audit events, timestamps with precision, actor role snapshots, event cause.
**Interactions and destinations:** Filter milestones, view permitted event details.
**Expected loading/empty/error/read-only states:** Partial redaction for restricted reviews; late metadata correction. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /applications/{id}/timeline. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Every event shows effective time separately from recorded time when different.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-14: External participation evidence
**Route and navigation:** `/app/participation/:applicationId`; section **Faculty**; parent **Application**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(scope),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Explicitly differentiate AKUS submission from provider enrollment and exam.
**Complete visual structure:** Date-driven checklist: external enrollment, exam registration, actual exam, hall ticket, certificate; evidence blocks with status; provider link.
**Actual project data:** Verified external chronology, provider run, exam date status, certificate outcome.
**Interactions and destinations:** Declare/enclose evidence, view verification, follow external provider link.
**Expected loading/empty/error/read-only states:** Enrollment earlier than submit, missing hall ticket, exam rescheduled, contradictory proof. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** POST /applications/{id}/enrollment-evidence /exam-evidence. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** AKUS cannot complete NPTEL actions.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-15: Prior attempts and repeat eligibility
**Route and navigation:** `/app/previous-attempts`; section **Faculty**; parent **My compliance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** View canonical-course attempt history and unresolved outcomes.
**Complete visual structure:** Table by canonical course, runs, verified certificate/no-certificate/unknown; right explainer for why draft/submission blocked and review link.
**Actual project data:** Prior outcomes, canonical mappings, evidence, resolution status.
**Interactions and destinations:** Open attempt detail; initiate proof verification.
**Expected loading/empty/error/read-only states:** Unknown result -> no new same-course submission; already certified -> no repeat. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /previous-attempts. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not equate no PDF with verified failure.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-16: Prior-result verification request
**Route and navigation:** `/app/previous-attempts/:attemptId`; section **Faculty**; parent **Prior attempts**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(scope). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Provide documentary failed-attempt evidence and track HoD determination.
**Complete visual structure:** Top outcome explanation; evidence list, request form, verifications timeline; clear no-reservation notice.
**Actual project data:** Prior attempt, certificate source, evidence, authorized HoD decision.
**Interactions and destinations:** Submit evidence, view outcome; authorized HoD review outside faculty view.
**Expected loading/empty/error/read-only states:** Disputed provider correction, incomplete proof, reviewer absent. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** POST /outcome-verifications. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Only verified no-certificate unlocks consideration of a fresh app.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-17: Annual compliance overview
**Route and navigation:** `/app/compliance/annual`; section **Faculty**; parent **My compliance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(R),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Separate annual obligation from subject Silver.
**Complete visual structure:** Academic-year selector over full-width summary strip; pathway explanation, achievements table, current vs as-of report selector.
**Actual project data:** Exam dates, annual assignments, >=8wk or 2x4wk, valid certificates, outstanding requirements.
**Interactions and destinations:** Select year, open year detail, open certificate evidence.
**Expected loading/empty/error/read-only states:** Pending result, late verification, review hold, no historic credit. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /compliance/annual. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Actual verified exam date anchors credit year.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-18: Annual academic year detail
**Route and navigation:** `/app/compliance/annual/:yearId`; section **Faculty**; parent **Annual**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(R),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Show exact evidence satisfying or failing one annual obligation.
**Complete visual structure:** Narrow summary at top, two explicit pathway panels with certificates and qualifying exam dates, dated reason codes, historic/latest tabs.
**Actual project data:** Annual obligation, evidence allocations, evaluated source versions, decision time.
**Interactions and destinations:** Open application/course/certificate; view report history.
**Expected loading/empty/error/read-only states:** Cross-year 4wk pairing prohibited; duplicated course, later certificate. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /compliance/annual/{year}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Below-Silver valid certificate can satisfy annual course standard.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-19: Subject-wise Silver list
**Route and navigation:** `/app/compliance/silver`; section **Faculty**; parent **My compliance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(R),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Monitor separate canonical subject obligations and deadlines.
**Complete visual structure:** Dense table grouped by active/historically closed: subject, initial teaching date, original deadline, latest Silver evidence, state, days remaining; compact legend.
**Actual project data:** Obligation per person+canonical subject+employment episode, scores, statuses.
**Interactions and destinations:** Open subject obligation, filter overdue and evidence pending.
**Expected loading/empty/error/read-only states:** Reassignment does not reset; separation closes monitoring. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /compliance/silver. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not treat Silver as prerequisite for annual completion.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-20: Silver subject obligation detail
**Route and navigation:** `/app/compliance/silver/:obligationId`; section **Faculty**; parent **Silver**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(scope),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Trace one canonical subject obligation academic evidence and deadline.
**Complete visual structure:** Header subject/deadline; dual history timelines teaching vs Silver evidence; visible relevance decision, score and exam date; as-of separation pane.
**Actual project data:** Assignment episode, relevant course, exam date, 75% score, verification time, assessments.
**Interactions and destinations:** Open evidence, view reassessment, request source correction.
**Expected loading/empty/error/read-only states:** Certificate after deadline but exam timely; post-separation retrospective recognition. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /compliance/silver/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Original as-of-separation status remains immutable.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE FAC-21: Certificate library
**Route and navigation:** `/app/certificates`; section **Faculty**; parent **My compliance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** F,D,H(R),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** List authentic certificate claims and their verification outcomes.
**Complete visual structure:** Searchable table certificate ID, course, exam date, score, Silver, issue/verification state; details open evidence.
**Actual project data:** Certificate artifacts, authenticity, revisions, provider corrections.
**Interactions and destinations:** Upload permitted evidence through linked application, inspect result.
**Expected loading/empty/error/read-only states:** Invalid, unverified, revoked, duplicate document. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /certificates. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** A valid cert is not proof of institutional participation eligibility.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE DRC-01: DRC review queue
**Route and navigation:** `/drc/reviews`; section **DRC**; parent **DRC Reviews**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** D. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Give DRC only independent academic reviews of other faculty.
**Complete visual structure:** Header with scope/current designation, filters by subject/new/returned, dense table faculty, course, relevance, pending age and expiry risk.
**Actual project data:** DRC tasks, applicant identity, course, documents, stage, effective office.
**Interactions and destinations:** Open review; approve/reject only for others.
**Expected loading/empty/error/read-only states:** Own application excluded, revoked appointment, missing source evidence. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reviews?stage=drc. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Never show DRC self-review.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE DRC-02: DRC application review
**Route and navigation:** `/drc/reviews/:taskId`; section **DRC**; parent **Queue**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** D. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Conduct academic relevance and evidence review of another faculty.
**Complete visual structure:** Two-column dense case dossier: left course, syllabus/subject, policy checklist, evidence; right sticky 300px decision rail with remarks and confirm.
**Actual project data:** Task, applicant role snapshot, mapping read-only, review history, evidence.
**Interactions and destinations:** Approve/reject with rationale and confirmation, return to queue on success.
**Expected loading/empty/error/read-only states:** Reviewer office expired, decision raced, enrollment chronology discrepancy. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /reviews/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Only current independent authorized DRC may act.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE DRC-03: DRC decision history
**Route and navigation:** `/drc/history`; section **DRC**; parent **DRC Reviews**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** D. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Audit previously completed independent reviews.
**Complete visual structure:** Compact sortable table decisions, dates, applicants, course/run, rationale indicator, current downstream stage.
**Actual project data:** Prior decisions and effective reviewer authority.
**Interactions and destinations:** Open review record read-only, filter dates.
**Expected loading/empty/error/read-only states:** Revoked designation retains historical authorship. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reviews/history. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Decision immutability visible.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-01: Department overview
**Route and navigation:** `/hod/home`; section **HoD**; parent **Department**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Prioritize actual departmental governance workload.
**Complete visual structure:** 3 text metrics in one flat summary strip: HoD pending, annual topic quota alerts, unresolved cases; four worklist panels with clear navigate links; no personal NPTEL cards.
**Actual project data:** Scoped department, office validity, queues, occupancy/risk.
**Interactions and destinations:** Open review, quota pool, mapping request, blocked transfer.
**Expected loading/empty/error/read-only states:** No current appointment, office change, empty worklist. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /dashboard/hod. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not show HoD personal application controls.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-02: Final approval queue
**Route and navigation:** `/hod/reviews`; section **HoD**; parent **Approvals**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Review eligible Faculty after DRC, DRC applicants directly.
**Complete visual structure:** Filters applicant role, pending/risk, exam year, topic; table with applicant, route, submission, enrollment, policy blockers.
**Actual project data:** Server tasks, applicant role snapshot, stage, risk flags.
**Interactions and destinations:** Open decision task; filters persisted.
**Expected loading/empty/error/read-only states:** DRC self case routed to HoD, former HoD denied. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reviews?stage=hod. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No automatic Principal ordinary approval.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-03: Final decision workspace
**Route and navigation:** `/hod/reviews/:taskId`; section **HoD**; parent **Approvals**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Make final institutional academic determination.
**Complete visual structure:** Left case summary and DRC history, right evidence tabs and fixed decision rail with required reason for reject, large confirm warning; clear separate external enrollment proof.
**Actual project data:** Task, office, policy checklist, reserved topic pool, evidence, DRC route.
**Interactions and destinations:** Approve/reject with idempotent submission, view audit.
**Expected loading/empty/error/read-only states:** Missing authorization, enrollment window expired, conflict with separation. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** POST /reviews/{id}/decision. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Q06 reject releases exactly once.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-04: Primary topic mappings
**Route and navigation:** `/hod/topic-mappings`; section **HoD**; parent **Topic governance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Show approved per-department canonical-course mapping and mapping gaps.
**Complete visual structure:** Wide searchable table course ID/title, provider categories, approved primary, effective revision, active reservations, missing status; filter review status.
**Actual project data:** Course mapping versions, department, provider category labels.
**Interactions and destinations:** Open mapping detail, intake queue, propose authorized revision.
**Expected loading/empty/error/read-only states:** Conflicting provider tags, no mapping, deleted provider category. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /departments/{id}/topic-mappings. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Current mapping not picked by applicant.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-05: Topic mapping requests
**Route and navigation:** `/hod/topic-mappings/requests`; section **HoD**; parent **Topic governance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Triage deduplicated faculty-triggered missing-mapping requests.
**Complete visual structure:** Narrow filter column and central table: course, requested by count, source category candidates, first seen, urgency; grouped by canonical course.
**Actual project data:** Dedup request IDs, provider labels, affected draft count.
**Interactions and destinations:** Open mapping decision; defer with rationale; return to queue.
**Expected loading/empty/error/read-only states:** Duplicate intake, source data unavailable, academic conflict. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /departments/{id}/primary-topic-mapping-requests. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** A request is not a successful application submission.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-06: Mapping detail and revisions
**Route and navigation:** `/hod/topic-mappings/:courseId`; section **HoD**; parent **Topic governance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Document original and current mapping with impact.
**Complete visual structure:** Split page: left current mapping/revision and all provider tags; below dated revisions; right existing allocation-impact summary, references to topic quotas.
**Actual project data:** Canonical course, mapping history, reviewer, effective time, affected reservations.
**Interactions and destinations:** Open new mapping decision, view revision evidence, navigate quotas.
**Expected loading/empty/error/read-only states:** Mapping pending, pending revised category, live reservations impacted. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /departments/{id}/.../history. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Never auto migrate old topic reservations under unresolved policy.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-07: Approve or revise mapping
**Route and navigation:** `/hod/topic-mappings/:courseId/edit`; section **HoD**; parent **Mapping detail**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Select one academically justified canonical topic among provider candidates.
**Complete visual structure:** Focused 760px form, radio topic candidates with provider tag explanations, rationale textarea, evidence provenance, effective change summary and existing-seat warning.
**Actual project data:** Source categories, canonical taxonomy, mapping revision, current office.
**Interactions and destinations:** Approve/revise after confirmation; request data correction.
**Expected loading/empty/error/read-only states:** Concurrent edit, no source evidence, already published version, policy pending retroactive movement. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** POST /.../approve or /revise. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Review is HoD write only; Principal read only.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-08: Canonical topic directory
**Route and navigation:** `/hod/topics`; section **HoD**; parent **Topic governance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H,A(reference),P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Inspect normalized canonical provider topics and alias proposals.
**Complete visual structure:** Searchable taxonomy list + right alias details, source count, courses per topic; action only if currently permitted.
**Actual project data:** Canonical topic IDs, provider category labels, aliases, approval state.
**Interactions and destinations:** HoD open mapping or request catalog correction; Admin maintain nonacademic reference as authorized.
**Expected loading/empty/error/read-only states:** Duplicate aliases, version conflicts, category collisions. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /nptel/topics. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Differentiate taxonomy maintenance from academic mapping approval.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-09: Annual quota pools
**Route and navigation:** `/hod/quotas`; section **HoD**; parent **Quotas**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Govern pool maxima per canonical topic and July–June year.
**Complete visual structure:** Academic-year selector, flat table topic, published/draft, max, HELD, confirmed, retained, available, active apps; overall summary banner only for urgent risk.
**Actual project data:** Department-topic-year pools, occupancy and revisions.
**Interactions and destinations:** Open pool; create draft for approved topic/year; filter.
**Expected loading/empty/error/read-only states:** No published pool, full, stale projection, missing year. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /departments/{id}/quotas. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Counted occupancy derived/validated by authoritative ledger.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-10: Quota pool detail
**Route and navigation:** `/hod/quotas/:poolId`; section **HoD**; parent **Quotas**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Understand exactly who consumes a shared pool.
**Complete visual structure:** Header topic/AY/max and occupancy fraction; below allocations table by course/run/app, status and holder; right revision log.
**Actual project data:** Pool cap, occupant refs, locks, amendments, chronological sources.
**Interactions and destinations:** Publish/revise, inspect applicant/reservation and ledger.
**Expected loading/empty/error/read-only states:** Full pool, allocation retained after withdrawal, exam reschedule. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /quotas/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No inferred seat from course-specific quota.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-11: Publish/revise annual quota
**Route and navigation:** `/hod/quotas/:poolId/edit`; section **HoD**; parent **Quota detail**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Make audited numeric cap decision.
**Complete visual structure:** Narrow modal-free form with current occupancy, new max numeric input, justification, effective date, read-only impact preview, save/confirm.
**Actual project data:** Pool version, occupancy count, eligible topic, appointment.
**Interactions and destinations:** Publish or revise; cancel to detail.
**Expected loading/empty/error/read-only states:** New max below occupancy, stale version, concurrently submitted last-seat. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** POST/PATCH /.../quota. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Server serializes with submission/transfer.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-12: Quota allocation ledger
**Route and navigation:** `/hod/quotas/:poolId/ledger`; section **HoD**; parent **Quota detail**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H,P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Prove exact reservations and releases for disputes.
**Complete visual structure:** Full-width audit-grade ledger table: timestamp, application, event, source/target, delta, actor, reason, policy; filters and export if permitted.
**Actual project data:** Immutable quota ledger, reversal linkage, counted state.
**Interactions and destinations:** Open event/app, filter, export with as-of metadata.
**Expected loading/empty/error/read-only states:** Multiple transactions, migrations, release after commencement. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /quotas/{id}/ledger. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Never allow direct ledger edit.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-13: Quota transfer case inbox
**Route and navigation:** `/hod/quota-transfers`; section **HoD**; parent **Exception work**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Find blocked verified cross-year exam-date migration cases.
**Complete visual structure:** Compact summary + table source/target AY, target pool status, failure reason, queued since, relevant course; highlighted read-only current count.
**Actual project data:** Case, evidence, target publish/cap, current pool occupancy.
**Interactions and destinations:** Open case; open target pool to publish/increase cap; request recheck.
**Expected loading/empty/error/read-only states:** Full or unpublished pool, stale provider update, transfer already resolved. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /quota-transfer-cases. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No priority/forced override absent policy.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-14: Quota transfer case detail
**Route and navigation:** `/hod/quota-transfers/:caseId`; section **HoD**; parent **Transfer inbox**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H,P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Explain failed migration and safe remediation.
**Complete visual structure:** Before/after year comparison, original/current pool cards, verified exam schedule versions, exact blocking reason; audit timeline and safe actions at right.
**Actual project data:** Reschedule source, applicant, current source, target pool, capacity and task state.
**Interactions and destinations:** Open target quota publish/revise; Recheck transfer; view history.
**Expected loading/empty/error/read-only states:** Target full, target unpublished, race with rejection, repeat reschedule, no permission. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /quota-transfer-cases/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Recheck is idempotent and capacity-checked.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-15: Prior-result verification inbox
**Route and navigation:** `/hod/outcome-verifications`; section **HoD**; parent **Exception work**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Verify proof that prior attempt earned no valid certificate.
**Complete visual structure:** Table faculty, canonical course, offered evidence, old exam, deadline risk, request age; evidence badge.
**Actual project data:** Outcome verification tasks and provider corrections.
**Interactions and destinations:** Open verification case; filter and sort.
**Expected loading/empty/error/read-only states:** Incomplete evidence, previous cert correction, role conflict. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /outcome-verifications. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No applicant self-verification.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-16: Prior-result decision
**Route and navigation:** `/hod/outcome-verifications/:caseId`; section **HoD**; parent **Verification inbox**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Record evidence-supported no-certificate or certified determination.
**Complete visual structure:** Focused dossier with source docs and time snapshots; right decision panel with finding, rationale, identity and confirm.
**Actual project data:** Prior attempt, provider result, certificate history, reviewer office.
**Interactions and destinations:** Verify unsuccessful, verify certificate, mark unresolved; return to queue.
**Expected loading/empty/error/read-only states:** Evidence conflict, original HoD replaced, repeated event. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** POST /outcome-verifications/{id}/decision. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Verification alone never submits new application.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-17: Integrity-review inbox
**Route and navigation:** `/hod/integrity`; section **HoD**; parent **Exception work**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H,P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Locate suspected chronology violations or retroactive certificate conflicts.
**Complete visual structure:** Data table review type, affected app, suspended compliance, allocated pool, status, raised date and authority.
**Actual project data:** Q22/Q33 case, evidence, suspension and quota.
**Interactions and destinations:** Open case if authorized; Principal read only.
**Expected loading/empty/error/read-only states:** Unresolved reviewer authority, corrected provider evidence. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /integrity-cases. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Never infer fraud solely from late provider correction.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-18: Integrity-review detail
**Route and navigation:** `/hod/integrity/:caseId`; section **HoD**; parent **Integrity**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H,P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Support formal case investigation and authorized conflict-free final determination.
**Complete visual structure:** Three pane on desktop: evidence chronology, old/new decisions, final outcome rail; on mobile sections; suspended recognition warning above.
**Actual project data:** Application validity, enrollment timestamps, prior failed-result verification, source corrections.
**Interactions and destinations:** Authorized reviewer uphold/invalidate, view report; if reviewer not authorized only read.
**Expected loading/empty/error/read-only states:** Q22/Q33 pending, reversal, disputed source, missing authority. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /integrity-cases/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Q23 release only on valid formal invalidation.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-19: Separation-closure inbox
**Route and navigation:** `/hod/separation-cases`; section **HoD**; parent **Exception work**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Review pre-commencement enrolled separations Q44.
**Complete visual structure:** Table faculty, offering, separation effective date, start date, enrolled proof, current pool, pending age.
**Actual project data:** Q44 cases and authority; closed application state.
**Interactions and destinations:** Open case; apply authorized verification and closure.
**Expected loading/empty/error/read-only states:** Course began after separation, office vacancy, HR correction. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /separation-cases. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Event time governs, not task processing time.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-20: Separation chronology case
**Route and navigation:** `/hod/separation-cases/:caseId`; section **HoD**; parent **Separation inbox**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Resolve Q44/Q47 without invented same-day event order.
**Complete visual structure:** Chronology comparison with DATE ONLY labels, evidence source cards, original/current pool, explicit findings selector before/after/indeterminate, rationale and confirmation.
**Actual project data:** Employment date precision, provider commencement precision, enrollment, audit.
**Interactions and destinations:** Verify and formally close+release when authorized; request more evidence.
**Expected loading/empty/error/read-only states:** No reliable ordering, no officeholder, dual events, already closed. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** POST /separation-cases/{id}/decision. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Indeterminate Q47 must never be presented as proven before/after.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-21: Department annual report
**Route and navigation:** `/hod/reports/annual`; section **HoD**; parent **Reports**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H,P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Evaluate department faculty annual compliance by July–June period.
**Complete visual structure:** Title with AY and as-of date, summary counts, sortable table staff, pathway, exam date, certificate confirmation, suspended statuses; export provenance.
**Actual project data:** Departmental historical current annual assessments, role exemption.
**Interactions and destinations:** Filter by year/role/state, export if granted, open detail.
**Expected loading/empty/error/read-only states:** Late certificate, former faculty, Q22/Q33 suspension. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reports/annual. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not include HoD as mandatory annual participant.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-22: Department Silver report
**Route and navigation:** `/hod/reports/silver`; section **HoD**; parent **Reports**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H,P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** See subject obligations and teaching context.
**Complete visual structure:** Table staff, subject, original assignment date, original deadline, fulfillment, overdue-at-separation, latest/as-of tabs.
**Actual project data:** Silver obligations per employment episode, accepted relevance, scores.
**Interactions and destinations:** Filter subject/status/AY, drill obligation.
**Expected loading/empty/error/read-only states:** Rehire, reassignment, late certificate. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reports/silver. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Keep closed-at-separation versus latest historical distinction.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-23: Department application report
**Route and navigation:** `/hod/reports/applications`; section **HoD**; parent **Reports**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H,P(R). A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Summarize submissions/approvals/withdrawals/releases by offering/topic.
**Complete visual structure:** Filter panel by year/topic/status and wide table, grouped outcome counts, drill to applications/ledger.
**Actual project data:** App events, review times, quota occupancy and transfers.
**Interactions and destinations:** Filter, export, click row, inspect historical audit.
**Expected loading/empty/error/read-only states:** Cross-year rescheduling, retro mapping revision pending. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reports/applications. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not confuse externally enrolled with institutionally approved.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE HOD-24: HoD decision history
**Route and navigation:** `/hod/decisions`; section **HoD**; parent **Department**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** H. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Provide accountable view of past HoD decisions.
**Complete visual structure:** Searchable table decision type (approval, quota, topic, verification, closure), date, rationale indicator, object.
**Actual project data:** Effective officeholder, decisions and evidence refs.
**Interactions and destinations:** Open record readonly; filtered exports where allowed.
**Expected loading/empty/error/read-only states:** Former office appointment shows historical authorship only. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /decisions. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Audit is append-only.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PRN-01: Institution overview
**Route and navigation:** `/principal/home`; section **Principal**; parent **Institution**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** P. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Monitor total AKUS institutional health without granting blanket write powers.
**Complete visual structure:** Large content width with plain KPI row: eligible Faculty, pending reviews, quota transfer cases, annual/Silver attainment; below department comparison table and risk list.
**Actual project data:** Institution-wide aggregate scoped counts and issue trends.
**Interactions and destinations:** Drill into department/report/application; export read-only report.
**Expected loading/empty/error/read-only states:** No data, partial provider freshness, policy pending. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /dashboard/principal. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No personal NPTEL application buttons.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PRN-02: Departments overview
**Route and navigation:** `/principal/departments`; section **Principal**; parent **Departments**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** P. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Compare departments and find operational bottlenecks.
**Complete visual structure:** Dense searchable table: department, assigned HoD/DRC, active eligible faculty, pending reviews, quota full topics, compliance state.
**Actual project data:** Effective office assignments, aggregated scoped counts.
**Interactions and destinations:** Open department detail; filter by academic year.
**Expected loading/empty/error/read-only states:** Missing HoD, invalid DRC+HoD overlap, inactive department. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /departments/overview. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No office-edit action in Principal oversight UI.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PRN-03: Department drilldown
**Route and navigation:** `/principal/departments/:departmentId`; section **Principal**; parent **Departments**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** P. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Trace why a departmental indicator is red or pending.
**Complete visual structure:** Header department and appointment status, read-only tabs Applications, Quotas, Mapping, Compliance, Exception Cases, Audit with links to dedicated details.
**Actual project data:** Department staff, quotas, mapping revisions, cases and reports.
**Interactions and destinations:** Open specific report/app/case.
**Expected loading/empty/error/read-only states:** Vacant HoD, partial sources, historical source changes. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /departments/{id}/overview. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Read-only institutional oversight.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PRN-04: Institution-wide applications
**Route and navigation:** `/principal/applications`; section **Principal**; parent **Institution**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** P. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Investigate approval delays without changing decisions.
**Complete visual structure:** Wide filters by department, year, course, stage, topic, risk; table with DRC/HoD status, dates and assigned office.
**Actual project data:** All app states, approval timelines, risk labels.
**Interactions and destinations:** Open application details and permitted evidence; export.
**Expected loading/empty/error/read-only states:** Late case, archived history, sensitive evidence redaction. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /applications?scope=institution. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No general Approve button.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PRN-05: Institution topic quotas and mappings
**Route and navigation:** `/principal/topics-quotas`; section **Principal**; parent **Institution**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** P. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Monitor consistent HoD topic choices, occupancy and reschedule cases across departments.
**Complete visual structure:** Two route tabs Quotas / Mappings, table grouped by dept/topic/year or dept/course/topic, last decision provenance; drill history.
**Actual project data:** Versioned HoD approvals, published pool caps/occupancy, case list.
**Interactions and destinations:** Open mapping revision or quota ledger in read-only mode.
**Expected loading/empty/error/read-only states:** Unmapped multi-category course, quota full, pending retroactive mapping policy. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reports/topics-quotas. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Principal cannot edit mappings or quotas by oversight role.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PRN-06: Institution annual compliance
**Route and navigation:** `/principal/reports/annual`; section **Principal**; parent **Compliance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** P. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Compare annual NPTEL outcomes across departments and cohorts.
**Complete visual structure:** Academic-year and as-of selectors; stacked department table, historical/latest toggle, drill to faculty evidence.
**Actual project data:** Q35 exam-date results, Q48 retrospective credits, eligible denominators.
**Interactions and destinations:** Filter, export provenance, navigate staff.
**Expected loading/empty/error/read-only states:** Late certificate, pending result, invalidation. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reports/institution/annual. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Faculty and DRC only counted as required NPTEL actors.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PRN-07: Institution Silver compliance
**Route and navigation:** `/principal/reports/silver`; section **Principal**; parent **Compliance**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** P. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** View subject obligations across depts with history.
**Complete visual structure:** Subject/status/episode filters, table faculty, assignment date, deadline, current/history classification, related certificate.
**Actual project data:** Silver claims, relevance, pre/post separation, Q49 findings.
**Interactions and destinations:** Open specific detail, export as-of vs latest.
**Expected loading/empty/error/read-only states:** Rehire and old overdue separation. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reports/institution/silver. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No direct manual award of Silver credit.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PRN-08: Institution exception monitoring
**Route and navigation:** `/principal/exceptions`; section **Principal**; parent **Oversight**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** P. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Track unresolved integrity, quota transfer, missing office, mapping and separation cases.
**Complete visual structure:** Severity-neutral worklist with type, department, issue, age, responsible office and recent event; read-only drill.
**Actual project data:** Cross-module case statuses and role assignment.
**Interactions and destinations:** Open detail; export oversight snapshot.
**Expected loading/empty/error/read-only states:** No current authorized HoD; mapping policy pending. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /reports/exceptions. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Escalation visibility does not grant final decision power.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE PRN-09: Institution audit and as-of reporting
**Route and navigation:** `/principal/audit`; section **Principal**; parent **Oversight**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** P. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Provide reproducible evidence chain for governance.
**Complete visual structure:** Audit search form with entity IDs, event time, recorded time, actor office; compact immutable table; as-of filter and exports.
**Actual project data:** Audit ledger, versions, provenance and report snapshot metadata.
**Interactions and destinations:** Search, inspect event, export authorized evidence.
**Expected loading/empty/error/read-only states:** Redacted personal documents, immutable original snapshots. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /audit. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No edit/delete UI.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-01: Administration overview
**Route and navigation:** `/admin/home`; section **Admin**; parent **Admin**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Surface data-source health and authority-record exceptions.
**Complete visual structure:** Flat four status text counters: staff reconciliation, conflicting offices, academic-years, provider integration; task list of missing source records.
**Actual project data:** Org references, sync versions, alerts.
**Interactions and destinations:** Open staff/appointment/sync correction pages.
**Expected loading/empty/error/read-only states:** Connector offline, stale imports, appointment overlap. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /dashboard/admin. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No academic approval or quota-edit link.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-02: Staff directory
**Route and navigation:** `/admin/staff`; section **Admin**; parent **Staff**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Manage institutional identity reference and discover duplicates.
**Complete visual structure:** Table staff ID, name, department, employment status, office assignments, last verified; search/filter and Add authorized record action.
**Actual project data:** Permanent person ID, authoritative staff roster, identity mappings.
**Interactions and destinations:** Open staff detail; start new managed record when authorized.
**Expected loading/empty/error/read-only states:** Duplicate staff, mismatched Google subject, incomplete roster. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /admin/staff. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No direct editing of certificate or compliance decisions.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-03: Staff detail
**Route and navigation:** `/admin/staff/:staffId`; section **Admin**; parent **Staff**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Trace stable person identity and effective-dated history.
**Complete visual structure:** Header identity status, tabs Employment, Offices, Departments, Teaching, Audit; detailed rows, source provenance and authorized correction actions.
**Actual project data:** Staff, Google subject link, episodes, dated assignments, corrections.
**Interactions and destinations:** Add authorized episode, office or assignment via dedicated page.
**Expected loading/empty/error/read-only states:** Rehire, identity merge requires special controlled workflow. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /admin/staff/{id}. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Preserve permanent identity across rehire.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-04: Employment episodes
**Route and navigation:** `/admin/staff/:staffId/employment`; section **Admin**; parent **Staff detail**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Create/correct authorized joining and permanent separation facts.
**Complete visual structure:** Timeline and tabular episodes, edit/source correction drawer with effective and recorded timestamps, evidence attachments.
**Actual project data:** Episode IDs, dates precision, cause, historical corrections.
**Interactions and destinations:** Add/correct episode, view impact preview for applications and Silver.
**Expected loading/empty/error/read-only states:** Separation backdated, overlap, revoked termination, rehire. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /admin/employment. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Employment change triggers domain reconciliation but not a fabricated completed HoD task.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-05: Office appointments
**Route and navigation:** `/admin/appointments`; section **Admin**; parent **Institutional data**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Maintain current and historical Principal/HoD/acting HoD/DRC roles.
**Complete visual structure:** Wide table person, department, office, valid-from/until, source, conflict indicator; focused edit page with overlap preview.
**Actual project data:** Effective-dated appointment records and institution scope.
**Interactions and destinations:** Create/revise authorized appointment with reason; inspect affected pending work.
**Expected loading/empty/error/read-only states:** DRC+HoD overlap across depts forbidden; stale office rights. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /admin/appointments. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Enforce non-overlap server/DB-side, not by datepicker UI alone.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-06: Teaching assignments
**Route and navigation:** `/admin/teaching-assignments`; section **Admin**; parent **Academic data**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Maintain source records that create Silver obligations.
**Complete visual structure:** Course/subject and faculty/semester filters, date-ordered table, teaching duty source and effective date; change preview of obligation deadlines.
**Actual project data:** Canonical subject, teaching allocation, effective date, episode, source revision.
**Interactions and destinations:** Add/correct authorized assignment, inspect impacted obligation.
**Expected loading/empty/error/read-only states:** Late import, subject alias, duplicate, invalid department episode. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /admin/teaching-assignments. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not restart first-assignment clock on semester rollover.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-07: Departments and canonical subjects
**Route and navigation:** `/admin/academic-reference`; section **Admin**; parent **Academic data**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Manage necessary institutional reference dimensions only.
**Complete visual structure:** Tabbed departmental catalog and canonical subject registry with versioned aliases and guarded edits.
**Actual project data:** Department IDs, subject codes, versions, relationships.
**Interactions and destinations:** Create/correct references, view impacted courses or teaching.
**Expected loading/empty/error/read-only states:** Merges affect obligations; require audit/impact review. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /admin/reference. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Taxonomy governance distinct from academic relevance approval.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-08: Academic years
**Route and navigation:** `/admin/academic-years`; section **Admin**; parent **Academic data**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Define official July–June calendar periods and missing-year prevention.
**Complete visual structure:** Table label/start/end/status, opening/closing states, source version, no accidental duplicate; managed creation panel.
**Actual project data:** Academic year IDs, July1/June30 boundaries, records.
**Interactions and destinations:** Create period, review published year; inspect connected quotas.
**Expected loading/empty/error/read-only states:** Missing academic year blocks new quota, cross-year transfer pending. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /admin/academic-years. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No silent implicit reset of reserved seats on July 1.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-09: NPTEL provider synchronization
**Route and navigation:** `/admin/nptel-sync`; section **Admin**; parent **Reference data**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Observe external preview ingestion and canonicalization safely.
**Complete visual structure:** Source status strip, recent sync jobs table, failure reasons, provider contract/freshness panel, authorized manual refresh with confirmation.
**Actual project data:** Provider adapter health, fetch source/version, sync timestamps and validation.
**Interactions and destinations:** Run authorized refresh, inspect details, retry worker job.
**Expected loading/empty/error/read-only states:** Provider 500, schema drift, rate limiting, stale schedule, mismatch. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /admin/nptel-sync. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Preview API does not prove individual enrollment or certificate.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-10: Provider metadata versions
**Route and navigation:** `/admin/nptel-offerings`; section **Admin**; parent **Reference data**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Inspect and correct source mapping errors with audit provenance.
**Complete visual structure:** Searchable offering table with current schedule, raw tags and verification status; detail side timeline of versions/sources.
**Actual project data:** Course run metadata, exam date versions, source URLs, approved evidence.
**Interactions and destinations:** Open offering, flag ambiguous data, run authorized reconciliation.
**Expected loading/empty/error/read-only states:** Exam rescheduling across year, conflict with uploaded hall ticket. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /admin/nptel-offerings. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** Do not silently rewrite submitted application snapshot.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-11: Work-ledger operations
**Route and navigation:** `/admin/operations`; section **Admin**; parent **Operations**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Diagnose durable worker, sync, notification and reconciliation processing.
**Complete visual structure:** Tabbed queue table type, idempotency key, attempts, last error, next attempt, correlation ID; side health notes.
**Actual project data:** Outbox jobs, retries, safe checkpoints, system state.
**Interactions and destinations:** Retry authorized safe job, inspect history; never directly mutate application quota.
**Expected loading/empty/error/read-only states:** Retry exhaustion, database outage, duplicate delivery. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /admin/operations. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** A successful job send is not proof of a completed academic state.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-12: Notifications configuration
**Route and navigation:** `/admin/notifications`; section **Admin**; parent **Operations**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Manage delivery templates/routes without policy decisions.
**Complete visual structure:** Template list, type/recipient scope, preview of redacted sample, version history, test-send permission.
**Actual project data:** Notification templates, outbox state, source events.
**Interactions and destinations:** Edit approved template settings, send test if safe.
**Expected loading/empty/error/read-only states:** Email provider offline, no contact, repeated failures. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET/POST /admin/notifications. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No approval via email link absent proper authenticated server authorization.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.

### PAGE ADM-13: Administrative audit
**Route and navigation:** `/admin/audit`; section **Admin**; parent **Operations**; deep links must load with authenticated refresh and browser back/forward, preserving list filter query params.
**Authorized roles:** A. A displayed button never substitutes for server-side role, department, own-case and effective-office authorization.
**Business purpose:** Trace admin-managed source changes without academic content edits.
**Complete visual structure:** Immutable table source, actor, effective/recorded dates, old/new redacted fields, source path and reason.
**Actual project data:** Staff/source audit and operational jobs; separate restricted academic audit.
**Interactions and destinations:** Search, inspect, export within authorization.
**Expected loading/empty/error/read-only states:** Historical corrections, merge review. Include meaningful skeleton or compact in-place progress for network loading; empty-state next step; specific field errors; 403 with safe navigation; idempotency/conflict response; and final success acknowledgement ONLY after server confirmation.
**Relevant backend contract:** GET /admin/audit. All entity IDs and role scopes resolved/verified server-side; status after mutation re-fetched or returned as authoritative response.
**Page-specific trust and quality criterion:** No delete/update audit button.
**Responsive composition:** Desktop uses the declared split, rail or full-width dense table. On tablet collapse supplemental rails below the main record; on mobile replace wide tables with accessible horizontal scroll plus priority fields/row detail, keep the main action visible and fully labeled, preserve breadcrumbs as back-navigation. No task is modal-only.


## DELIVERABLE 7 — Complete role-based journeys and transitions

**J1 Faculty ordinary first application:** Sign in -> Faculty overview -> Catalog search -> Course detail -> Exact offering (source dates/provider multi-category displayed) -> New wizard choose -> Eligibility -> Evidence -> Review & submit (read-only HoD-approved topic, scheduled exam AY, published shared pool) -> server atomic reserve receipt -> My applications detail with DRC pending -> DRC review -> HoD final review -> distinct enrollment evidence page -> exam/cert evidence -> annual/Silver assessment. On a missing mapping or quota, do NOT display success: save draft and open HoD mapping/quota intake. On no-seat race, show refreshed published occupancy and safe 'Return to draft'.

**J2 DRC Head own application:** DRC signs in -> Faculty overview (all faculty duties) -> Draft/submit -> final review route states 'HoD final review — DRC Head applicant, DRC self-review bypassed' -> HoD decision -> own application timeline. DRC cannot open their own case in DRC review queue, even via direct URL. A DRC review of another faculty remains available only when office effective.

**J3 Independent DRC review:** DRC queue -> review detail -> inspect relevance, provider dates, evidence, prior outcome, application submitted before actual enrollment -> enter required decision rationale -> Approve or Reject -> server revalidates appointment and policy -> confirmation -> updated queue and audited timeline. If reject, quota release is atomic. If HoD vacancy, DRC-approved task remains pending and seat HELD.

**J4 HoD final approval:** HoD queue -> task detail -> DRC decision where appropriate or direct DRC applicant path -> inspect published shared topic pool and actual external evidence -> approve/reject -> server transitions and audit -> task disappears from queue; former HoD cannot act. No HoD applicant workflow.

**J5 Multi-category topic mapping setup:** Faculty offering detail sees provider multiple category labels and missing mapping -> Save draft / Request mapping -> deduplicated HoD inbox -> mapping request detail -> HoD selects one academically justified canonical topic, evidence and rationale -> approval -> faculty draft now has read-only primary topic -> if annual pool not published, HoD quota creation -> faculty can then submit. Principal sees read-only mapping history.

**J6 Topic quota publication:** HoD annual pool listing -> choose FY July–June and approved topic -> draft cap -> publish with rationale -> concurrency-safe occupancy validation -> pool detail/ledger. Increasing published cap permitted; decreasing below occupancy blocked. No direct seat editing.

**J7 Cross-year schedule change:** Authorized provider adapter verifies new published exam date -> case moved from 2026–27 into 2027–28 target year -> transaction checks published target same department/topic pool, locks both and atomically migrates counted seat when available -> application detail shows original vs current and movement history. If missing/full: existing 2026–27 seat stays counted, application warns 'Target pool not reserved', HoD transfer case created -> HoD can publish/raise lawfully then Recheck -> decision from backend. Q35 final annual compliance still uses actual verified exam date independently.

**J8 Mapping revision with active reservations:** HoD mapping detail -> Revise mapping -> explain affected old reservations and preserve versioned history -> new submissions use approved revised topic as of effective policy -> old counted allocations and impact case remain visible; NEVER auto-migrate old pools because this is still unratified. User sees exact original charged topic in application history.

**J9 Outcome verification and repeat attempt:** Faculty previous attempts -> course outcome unresolved -> upload documentary result -> HoD verification case -> documented no-certificate result or valid cert or unresolved. No seat until later fresh application passes rules. A corrected old result after later approval opens Q33 integrity case and pauses only newer compliance credit; quota preserved during review; Q23 release if invalidated; Q34 normal evaluation if upheld.

**J10 Integrity chronology conflict:** Current approved app -> evidence reveals actual enrollment earlier than AKUS submission -> formal Q22 integrity case -> suspended application compliance recognition, counted quota retained -> independent authorized decision uphold/invalidate -> invalidate Q23 atomic release with historical audit; do not silently remove external certificate.

**J11 Annual compliance:** Faculty or authorized reviewer -> annual year selector -> server groups achievements by ACTUAL verified exam date -> one qualifying >=8wk or 2 distinct 4wk same-year courses, valid certificates below Silver okay -> confirmation only when verified -> as-of versus latest historical view if late certificate. Exclude HoD/Principal from mandatory denominator.

**J12 Silver lifecycle and rehire:** Admin records effective-dated teaching assignment -> obligation per faculty+canonical subject+episode, deadline two calendar years later -> faculty Silver table shows original start/deadline; ending teaching does not reset -> permanent separation closes active monitoring preserving status snapshot -> rehire new episode and new assignment creates new obligation -> late valid relevant Silver result from pre-separation exam can establish retrospective historical fulfillment without reopening monitoring. Timeliness uses actual qualifying exam date vs original deadline; verification never backdated.

**J13 Three separation paths:** Admin authorized effective separation record -> application reconciliation -> Q43 pre-enrollment pre-commencement auto close/release, Q44 enrolled pre-commencement review with seat counted until HoD final close, Q45 after commencement auto close/release; Q46 uses actual event time not processing; Q47 same date-only ambiguity -> HoD chronology review, counted seat pending, documented Q47 close/release if still unprovable. No silent retroactive classification.

**J14 Principal oversight:** Principal home -> department comparative table -> read-only application detail/decision history -> topics/quotas and transfer alerts -> as-of compliance reports and audit export. No personal compliance widget, no edit or approve buttons; a future special emerging technology exception cannot be silently granted.

**J15 Admin effective-dated source correction:** Admin staff detail -> employment episodes or teaching assignments -> show effective vs recorded dates -> preview affected Silver deadlines, separation app cases and current offices -> authorized versioned correction -> server reconciles without deleting original audit -> affected HoD/Principal dashboards show updated status. Overlap between DRC and HoD/acting HoD across any valid interval hard-blocked.

**J16 Error recovery:** Network failure before submit -> draft remains, retry with same idempotency key -> exactly one app/seat if first request committed; if authorization revoked mid-review -> 403, action removed; if provider metadata stale -> safe pending status; if external provider inaccessible -> no fabricated exam/enrollment; if two faculty race last topic seat -> one success, one conflict and no negative occupancy.

## DELIVERABLE 8 — Backend/API/data integration map (conceptual)

Backend stack and trust boundary: React 19 + TypeScript + Vite + React Router + TanStack Query served same-origin via Caddy; FastAPI on Python 3.13 using SQLAlchemy synchronous sessions with Psycopg 3 and PostgreSQL. Use Google OIDC to institutional roster, server-side RBAC/ABAC and effective-dated office grants. PostgreSQL is source of truth for all quotas, apps, approvals, evidence metadata, audit, compliance and work ledger. NPTEL preview is informational metadata; no individual proof. Optional Google Shared Drive archive is async evidence mirror, not transaction authority. No Kafka/Redis/Kubernetes/microservice expansion by default. Adapt minor library version updates only if demonstrated compatible.

### Data/API mapping by route family

| UI route family | API contract family | Domain-owned records and security |
|---|---|---|
| `/login`, `/app/profile` | `/auth/*`, `/me`, `/me/roles` | OIDC, stable staff, offices, effective authority; token/session security |
| `/app/catalog`, `/app/offerings/*` | `/nptel/courses`, `/nptel/offerings`, `/.../metadata-history` | Canonical course, offering, schedule/source version, provider categories |
| `/app/applications/new/*` | `/applications/drafts`, `/applications/{id}/submit` | Snapshots, server-resolved mapping/pool, atomic seat, idempotency |
| `/app/applications/*` | `/applications`, `/.../timeline`, `/.../quota-transfer-history` | ACL-scoped record, immutable timelines, current/original pool |
| `/app/participation`, `/app/certificates` | `/.../enrollment-evidence`, `/.../exam-evidence`, `/.../certificate-evidence` | Scanned documents, claim type, authenticity and timestamp provenance |
| `/app/previous-attempts` | `/previous-attempts`, `/outcome-verifications` | Canonical no-repeat Q27–Q30; HoD independent verification |
| `/app/compliance/annual` | `/compliance/annual`, `/reports/annual` | Q35–Q38 + Q48, actual exam year, as-of version |
| `/app/compliance/silver` | `/compliance/silver`, `/reports/silver` | Q39–Q50, employment episodes, relevant Silver evidence |
| `/drc/reviews`, `/hod/reviews` | `/reviews`, `/reviews/{id}/decision` | Current independent office, decision history, quota release |
| `/hod/topic-mappings` | `/.../primary-topic-mapping*/...` | HoD one primary per dept/course, evidence and versions |
| `/hod/quotas` | `/departments/{id}/topics/{id}/academic-years/{id}/quota`, `/.../ledger` | Year/topic pool with count, occupancy invariant |
| `/hod/quota-transfers` | `/quota-transfer-cases` and `/.../recheck` | Reschedule verified transfer and failure reconciliation |
| `/hod/integrity`, `/hod/separation-cases` | `/integrity-cases`, `/separation-cases` | Conflict-free current authority, Q22/Q33/Q43–Q47 |
| `/principal/*` | Read-only `/reports/institution/*`, `/audit` | Institutional scope; no mutation by Principal oversight role |
| `/admin/*` | `/admin/staff`, `/admin/appointments`, `/admin/academic-years`, `/admin/nptel-sync`, `/admin/operations` | Official reference data, no academic approval |

### Error and server response requirements

Use typed, stable error codes such as `AUTHORITY_EXPIRED`, `NO_APPROVED_TOPIC`, `POOL_UNPUBLISHED`, `QUOTA_FULL`, `COURSE_ALREADY_CERTIFIED`, `ACTIVE_CANONICAL_DUPLICATE`, `EVIDENCE_PENDING`, `EXAM_YEAR_TRANSFER_BLOCKED`, `OFFERING_METADATA_STALE`, `DEADLINE_EXPIRED`, `APPLICANT_IS_REVIEWER`, `POLICY_UNDECIDED`, `OPTIMISTIC_LOCK_CONFLICT`, `EXTERNAL_PROVIDER_UNAVAILABLE`. These code names are technical design proposals, not institutional policies. Error UI must provide correct recovery, preserve draft inputs, not expose unauthorized records and never claim a transaction succeeded unless it did. Attach correlation IDs where safe.

### Permission enforcement matrix

| Capability | F | D | H | P | A |
|---|---:|---:|---:|---:|---:|
| Submit own NPTEL app (current eligible faculty office) | Yes | Yes | No | No | Only if separately faculty-eligible |
| DRC academic review of another faculty | No | Yes | No | No | No |
| HoD final approval and evidence outcome review | No | No | Yes | No | No |
| Approve departmental primary topic mapping | No | No | Yes | No | No |
| Publish/revise department topic-year quota | No | No | Yes | No | No |
| Read own annual/Silver compliance | Yes | Yes | Historical-only if applicable | Historical-only if applicable | Separately eligible only |
| Read own departmental aggregate | Own only | DRC authorized scope | Department | All | Operational scope only |
| Read all institutional reports and mapping decisions | No | No | Department | Yes | Operational as authorized |
| Edit employment, offices, teaching assignments | No | No | Only if separate authority explicitly provisioned | No by oversight role | Yes by authorized Admin grants |
| Read institutional audit | Own relevant | Scoped review audit | Department | Institution | Scoped operational audit |

Do not use the UI to mutate role claims. For any admin who is ALSO a separately eligible Faculty by official appointment, calculate duties from that eligible status; `Admin` alone never grants NPTEL applicant participation rights.

### State distinctions critical for design

- Application: DRAFT, SUBMITTED, DRC_PENDING, HOD_PENDING, APPROVED, REJECTED, WITHDRAWN, under integrity review, under Q44/Q47 separation review, closed by Q43/Q45 separation, INVALIDATED and historical terminal. These are conceptual states, not a license for unsupported transitions.
- Reservation: HELD, CONFIRMED, RETAINED counted after voluntary withdrawal commencement, RELEASED, and audited MOVED to another annual topic-year pool on verified reschedule. Distinguish historical movement from current counted allocation.
- Evidence: UNUPLOADED, UPLOADED, SCAN_PENDING, REVIEW_PENDING, VERIFIED, REJECTED, CORRECTED, REVOKED, UNRESOLVED. Enrollment and exam cannot become verified from course preview alone.
- Compliance: OUTSTANDING, AWAITING_RESULT, FULFILLED, OVERDUE, SUSPENDED_BY_INTEGRITY, HISTORICALLY_CLOSED, RETROSPECTIVELY_FULFILLED, with as-of/report versions.
- Mapping: MISSING, REQUESTED, APPROVED, REVISED; binding subject of current mapping is department+canonical course, not individual offering.
- Quota-transfer case: DETECTED, TRANSFERRED, TARGET_UNPUBLISHED, TARGET_FULL, REVIEW_PENDING, CLOSED; never imply migration when source occupancy remains retained.

## DELIVERABLE 9 — Production design review and correction log

1. **Avoid template dashboard syndrome:** Dashboard uses a compact priority strip and real work lists rather than cloned giant cards and stock charts. Topic/quota and audit pages use full-width tables; forms use narrow reading widths.
2. **Avoid false authority:** HoD and Principal are exempt; no personal NPTEL form. DRC personal case bypasses own review. DRC and HoD never overlap. Principal global read-only; special emerging-technology approval route remains policy pending.
3. **Avoid domain conflation:** Topic mapping is not course tagging, quota pool is not per-offering quota, provider metadata is not enrollment proof, verification is not automatically credit, exam date at submission is not actual exam date.
4. **Avoid quota lies:** Faculty submission UI shows current published pool and seat availability as of read, but repeats server validation on commit; after a transfer block UI explicitly shows original seat retained and target NOT reserved.
5. **Avoid destructive history:** Every record has detail/history and effective time versus recorded time; no silent changes to closed applications, old mapping versions, old report snapshots or separated faculty status.
6. **Avoid navigational shortcuts:** Complex applications, outcome review, mapping review and evidence management have dedicated routes. Small confirmation actions use dialogs; core decisions are not performed in generic dropdown modals.
7. **Avoid role mixing:** Global role indicator is information, not an authorization switch; deep links validate on backend. Separate Admin source management from HoD academic judgments.
8. **Avoid premature policy choices:** Open Q51 one Silver certificate across multiple subjects, map-revision retroactivity, indefinite failed quota transfer remediation, faculty promotion-to-HoD active-app behavior, emerging technology Principal route and other unresolved items must be visible as pending where relevant, never silently resolved.
9. **Avoid decorative analytics:** Only charts showing meaningful time trends; provide accessible tables and clear source dates. No percent metrics lacking denominator definition.
10. **Security/accessibility:** WCAG AA contrast and keyboard navigation, no hidden-only validation, no unauthorized record existence leak, reviewed error/empty/skeleton/mobile states.

### Visual and functional acceptance matrix

| Test ID | Acceptance test | Pass condition |
|---|---|---|
| UX-01 | Light theme and design tokens | No out-of-token color/radius/layout divergence in sampled pages |
| UX-02 | Route completeness | All inventory routes load or correctly deny access via server grant |
| UX-03 | Role-specific home | F/D get personal NPTEL; H gets departmental decisions; P gets oversight; A gets source ops |
| UX-04 | DRC self-review | DRC self case never actionable in DRC queue or direct URL |
| UX-05 | HoD/Principal exempt | No current compulsory NPTEL application/annual/Silver prompts |
| UX-06 | Dynamic canonical topic | Multiple provider categories visible; only HoD-approved topic charged |
| UX-07 | Missing mapping | Draft/intake only, no submitted status, no seat |
| UX-08 | Annual quota UI | Shared department/topic/year occupancy shown across courses, not per offering |
| UX-09 | Quota editing | Cannot publish cap below counted occupancy; concurrent submit handles conflict |
| UX-10 | Quota transfer | Correct original/current/target pools; blocked target shows no phantom target hold |
| UX-11 | Submission error | Retry safe; preserves draft; exactly one committed seat |
| UX-12 | Application status terminology | Submitted != externally enrolled != approved != completed != verified |
| UX-13 | Outcome verification | No-certificate evidence review separate from new application approval |
| UX-14 | Silver date logic | Timely actual exam credited after later verified Silver certificate |
| UX-15 | Separation | Q43/Q44/Q45/Q47 pathways distinct in timelines and quotas |
| UX-16 | As-of reporting | Same historical subject can be unresolved at separation and later recognized, without overwriting snapshot |
| UX-17 | Table usability | Filters, sort, pagination, row links, keyboard navigation, empty state |
| UX-18 | Forms | Save draft, conditional validation, unsaved warning, meaningful submit confirmation |
| UX-19 | Mobile/tablet | No clipped primary actions, usable overflow and touch targets |
| UX-20 | WCAG AA | Automated axe checks + manual keyboard/screen-reader smoke tests |
| UX-21 | No dead UI | Every action either performs authorized operation or is explicitly disabled with reason |
| UX-22 | Design regression | Automated screenshots for representative routes at 1440, 1024, 768, 390 widths |
| UX-23 | Data provenance | Every critical date, certificate verification and mapping revision has source/time affordance |
| UX-24 | Deep links | Reload/back/forward/filter context preserved and unauthorized direct links rejected |
| UX-25 | User feedback | Never display successful academic/quota mutation prior to server commit |

## DELIVERABLE 10 — Coding-model final prompt package contract

The completely self-contained MODEL 2 implementation prompt is a distinct file. It embeds (A) this entire UI/UX specification and (B) the full verified AKUS master implementation baseline Version 2.4 without omission. The UI specification takes priority on visual/page structure; the latest ratified policy amendments and Q-register in Version 2.4 take priority for domain rules. Both documents explicitly prohibit guessing the unresolved mapping-revision retroactivity. Model 2 must implement actual source files, tests, migrations, fixtures and deployment instructions and truthfully disclose absent external credentials. Deliver stable vertical slices, not a static screenshot or decorative prototype.

