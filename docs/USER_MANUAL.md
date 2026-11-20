# Phase 2 local walkthrough

Open **http://127.0.0.1:8080**. The current dataset is LOCAL/DEMO. Google shows
configuration required until securely configured; no real person can be signed in
through the fixture selector. Institutional instructions: GOOGLE_OIDC_SETUP.md.

## Staff, employment and office sources

1. Choose **Nila Shah · Admin**. Administration workspace shows actual staff, staged
   import and account-request counts. Staff directory → Add staff record records
   permanent identity, first employment and department with source/reason. It does
   not create a Google account or infer an office.
2. Open a staff detail to inspect episodes, offices, department/email history and
   teaching. **Manage source records** allows person, employment, department, email
   and office correction with expected version and source/reason. Employment history
   is a dedicated episode register; rehire creates another non-overlapping episode
   under the same permanent person. Dates are explicit; ends_before is exclusive.
3. **Record appointment** uses approved role/scope/effective dates. DRC must be faculty;
   DRC/HoD overlap is forbidden globally, including acting HoD. Current offices must
   fit employment. End a temporary office on its dedicated detail page with reason,
   source and confirmation. Correcting an issued office preserves and supersedes the
   original; source history shows both facts. Changing authority affects existing
   sessions without a fresh login.
4. If an episode change would exclude dependent department, teaching or office records,
   correct those source facts first. No source command silently waives academic
   obligations or decides role-transition/separation policy.

## Official CSV/XLSX imports

1. Create needed departments/subjects/academic years in **Reference setup** first.
2. **Source imports** → choose Staff roster or Teaching assignments, enter source
   reference, upload UTF-8 CSV or one-worksheet XLSX. Maximum 4 MiB, 500 data rows,
   20 columns; formulas, macros/external links and malformed/oversized files are
   rejected. Headers must match the displayed column names. Dates use YYYY-MM-DD;
   email validity uses timezone-aware ISO datetime.
3. Review normalized rows and every error on the persisted preview. A failed row
   prevents the entire commit. Correct the source file and stage a new job. Existing
   staff keys/teaching allocation keys require explicit source correction instead of
   silently overwriting data. Reloading the preview preserves its result.
4. Check the authorization confirmation and **Commit validated import**. The server
   rechecks all rows and current Admin permission in one transaction. Retrying a
   committed import returns its recorded result; it does not create duplicate staff.

Staff columns:
`staff_key,display_name,department_code,starts_on,ends_before,is_faculty,email,email_valid_from`.
Use explicit true/false classification. Email is optional; if present it must be
@example.test in demo, @cmrit.ac.in in institutional mode, with valid-from. There is
no role column. Example fictional CSV (choose a new unique key on each demonstration):

```csv
staff_key,display_name,department_code,starts_on,ends_before,is_faculty
LOCAL-IMPORT-001,Synthetic colleague,CSE,2020-07-01,,true
```

Teaching columns:
`external_key,staff_key,episode_starts_on,subject_code,department_code,academic_year_start,term,starts_on,ends_before`.
The episode, subject, department and year must already exist. The true teaching
interval must fit its episode and configured year. No invented teaching is loaded
for the five named real participants. Backend tests cover XLSX teaching imports;
browser tests cover CSV staging/commit and manual teaching correction.

## Teaching and academic reference

Reference setup creates departments, canonical subjects, aliases and official July 1
academic years. Stable codes/IDs are retained on name corrections. Alias corrections
cannot merge distinct subjects; that governance remains pending. A year ends June 30
and does not publish quotas or reset/carry capacity.

**Teaching allocations** filters by staff name, department, subject, year and term.
Admin records a source allocation, inspects its detail, and uses **Correct source
record** for date/term/source correction or an explicit void. Before/after history is
retained. The timeline uses the earliest non-voided official date for the same canonical
subject and employment episode; repeating a semester does not reset it, rehire does.
It shows a provisional two-year anniversary only where calculable. IO-02 acceptance
and P-54 leap-day handling remain pending; this is not a compliance assessment.

## Five role workspaces

- Mira Rao, **Faculty**: personal source profile/teaching; application route readiness
  DRC → HoD and compliance dependency. Other staff/source writes denied.
- Arun Sen, **DRC Head**: distinct faculty responsibilities and independent review
  navigation; own application readiness directly HoD. No self-review decision exists.
- Leela Iyer, **HoD**: CSE source oversight/teaching, review/quota dependency links;
  no applicant route. Omar Das demonstrates acting HoD limited to ECE.
- Nila Shah, **Admin**: imports, reference/setup, source corrections and controlled
  pending-account reconciliation; Admin alone grants no academic reviewer powers.
- Dev Mehta, **Principal**: institution-wide source overview and registers with no
  source writes or applicant route. Academic reports are later work.

Policy guide keeps confirmed/pending decisions separate. **System connections &
academic calendar** opens actual readiness/worker/year data. Academic services show
NOT_IMPLEMENTED where Phases 3–7 are required; no quota/submission/review/certificate
result is fabricated. On mobile use Open navigation; Escape restores focus. Sign out
revokes the server session. Protected deep links then return to sign-in.

## Real account acceptance

All five user-named real accounts remain **BLOCKED / NOT VERIFIED**. The tracked roster
template contains intended roles and blank facts only. An authorized operator must
supply approved private roster/office facts, configure the real Web OAuth client,
bootstrap the first Admin in a protected separate dataset and have EACH participant
voluntarily sign in with Google. Follow GOOGLE_OIDC_SETUP.md; never use demo fixtures
to claim these cases passed and never save auth codes/tokens in screenshots.

## Phase 3 academic workflow

Course discovery, exact provider sources, topic proposals/HoD mappings, annual quota
publication, draft/submission, ordinary reviews, withdrawal, ledger and transfer cases
now have working pages. The earlier phase description above is retained for source
workflows; these academic integrations are no longer placeholders. Follow
[NPTEL_PROVIDER_SETUP.md](NPTEL_PROVIDER_SETUP.md) for exact roles, steps, current
manual hall-ticket verification and evidence/compliance boundaries.

## Phase 6 certificate evidence and compliance reports

Faculty and DRC Head can open **Certificate library** from the navigation or **Exam and certificate dossier** from a submitted application. Record the actual sitting, observation time in local time, source and reason. Supply either a private PDF up to 2 MiB or an official archive reference and its SHA-256. Each revision retains the original. The certificate dossier distinguishes applicant assertions, independent exam attendance, verification, rejection and official revocation. A confirmed attendance finding can remain pending a result.

Independent verification requires a current application-specific institutional designation. Its source order must cover examination, issuer credential, numerical score and score-sharing checks. Subject relevance additionally requires a designation covering that canonical subject. The applicant and original application reviewers cannot verify their own case. No reviewer grants are seeded. An issuer correction should cite the corrected source, preserve the precision of the actual exam date and explain the change. The catalog preview cannot verify any personal result.

**Compliance reports** opens the personal, departmental or institutional register appropriate to the signed-in office. Choose an employment episode, then an academic year or subject to inspect the contributing records. Annual credit uses one eligible course of at least eight weeks or two distinct four-week courses examined in the same July–June period. The subject detail shows first official assignment, original two-calendar-year deadline, score, relevance, monitoring and any frozen separation finding. A raw teaching import remains pending IO-02.

The latest view recalculates from current authoritative records. **Save current observation** retains a dated copy for a participant or authorized department. Credential writes and teaching-source changes also capture observations in their database transactions. The Principal can read saved observations and filter the institution register by year or knowledge cutoff. A missing observation is displayed explicitly. An observation does not constitute formal institutional publication under P-53.

### Private evidence storage

PDF bytes are stored in PostgreSQL behind the authenticated API. AKUS checks the declared PDF type, bounded request size, PDF signature/end marker and SHA-256. Optional malware scanning uses an operator-provided local clamd Unix socket via AKUS_CLAMD_SOCKET, mounted into the existing API container. The client cannot set the scanner address. A missing daemon, timeout or unrecognized response quarantines the upload. An infected response rejects it. Only an upload cleared by the scanner can be downloaded, by the owner or independent case designee, as a fixed-name attachment with a download audit event. Scoped oversight may see the dossier metadata. The default Docker demo has no live scanner or NPTEL credential API. Independent review uses an official source the reviewer can actually authenticate.

The isolated reviewer browser run uses fictional source records and case-specific appointments stored only in a test database. Run scripts/check-phase5-cases.sh against the compiled local stack to exercise it. The operational Google acceptance gate still requires approved configuration and participating real account holders.
