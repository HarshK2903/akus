# Source and academic security boundary; remaining deployment work

Implemented and locally tested: Google-only discovery/code exchange, S256 PKCE,
browser-bound one-use expiring state, nonce, RS256 trusted JWKS, issuer/audience/time,
verified email and hd=cmrit.ac.in. No email-prefix roles, auto-created staff or first
visitor Admin. Stable issuer+sub cannot move across people; duplicates require audited
reconciliation and exact prior-link revocation. Verified email observations never
rewrite official source email history. Operator bootstrap requires approved facts and
creates no authenticated session. Live Google integration is still NOT VERIFIED.

Opaque random session tokens are hashed in PostgreSQL, rotated and bounded to eight
hours. HTTPS cookies are Secure; localhost HTTP is explicitly limited to loopback.
Exact Origin and CSRF protect mutations. Current employment/enabled/office/grant/link
facts authorize requests and are rechecked after source transaction locks. Disabling
or separating staff denies access; Principal read scope does not grant writes. Source
and identity transaction serialization plus DB constraints cover competing writers.
The review endpoint rechecks effective office, next review stage and applicant identity in the decision transaction. See the final security review and admission regressions.

Uploads are bounded before multipart parsing (5 MiB request, 4 MiB file), with 500
rows/20 columns, bounded expanded XLSX contents and defusedxml. Formulas, macros,
external workbook links and malformed inputs are rejected. Explicit previews and
all-or-nothing commits prevent partial authoritative imports. Immutable before/after
history, audit and receipts protect traceability. General evidence uploads, malware
scanning and private object storage are not implemented by this import parser.

Google/network calls do not hold DB transactions. Provider tokens are not persisted.
JSON responses are no-store. Access logs omit callback queries; structured logs omit
bodies/credentials. Complete secret configuration is fail-closed and Pydantic hides
input values in settings errors. Caddy retains CSP/nosniff/frame restrictions.

The fixture selector intentionally grants access to fictional local people only.
Demo mode cannot coexist with configured Google OIDC; Google linking rejects demo
people. Real UAT must use a separate protected dataset with demo off. The running
Compose database uses public demo credentials; it is not a production environment.
Docker operators and DB superusers are trusted local operators, not application roles.

Remaining gates: actual Google/Workspace/participant verification, production TLS,
trusted proxy/rate-limit tuning (current limiter is conservative per observed proxy
IP), least-privilege DB accounts, secret manager/key rotation, institutional retention,
security monitoring, evidence storage/scanning, export controls and tested backup/PITR.
No penetration-test, full security audit or production-readiness claim is made.

Phase 3: public NPTEL adapter pins HTTPS host/path, refuses redirects, bounds timeout
and bytes, checks exact offering identity/schema, strips markup and ignores personal
participation flags. Source conflicts/staleness block admission. Current HoD scope and
no-self-review apply after locks. CSRF/idempotency/version checks protect all commands.
Shared authority gate vs source writers, deterministic allocation/pool locking and
PostgreSQL deferred count/balance guards protect races. Personal schedule evidence
is immutable and exact-application bound; manual findings never imply certificates.
Case detail authorizes current HoD department or Principal read-only scope. Faculty
only sees own allocation detail; Admin cannot grant academic approvals.
