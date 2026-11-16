# Institutional Google sign-in: operator setup and live UAT

Code supports real Google authorization-code sign-in. **Live integration is NOT VERIFIED.**
No private OAuth client configuration or voluntary account-holder login was available
in this implementation. Automated tests use generated RSA keys and isolated HTTP
responses, never a runtime authentication bypass. No real institutional person has
been provisioned from the five email strings alone.

## External prerequisites

An authorized institution operator must supply an approved Google Cloud/Workspace
Web OAuth client, consent/access settings and official roster facts. Use an
organization-owned project; choose **Internal** audience when the project belongs
to the appropriate Workspace organization. Otherwise obtain institution approval
for the applicable testing audience and explicit test access. Do not weaken the
`hd == cmrit.ac.in` check if the organization differs: document the discrepancy for
authorized resolution. Request only `openid email profile`.

Register this exact local browser-reachable redirect URI:
`http://127.0.0.1:8080/api/v1/auth/google/callback`.
The corresponding origin is `http://127.0.0.1:8080`. Do not enter `api:8000`,
`db:5432`, localhost:5173, or the React `/auth/complete` route as the callback.
If Workspace blocks the application, its administrator must review the client in
Admin Console API controls and allow the necessary access. Codex has not created
or changed any Google Cloud/Workspace account, client or access policy.

References: [Google OIDC setup and claims](https://developers.google.com/identity/openid-connect/openid-connect),
[Google web-server OAuth clients and redirects](https://developers.google.com/identity/protocols/oauth2/web-server),
[Workspace app access controls](https://support.google.com/a/answer/7281227).

## Private local configuration

Keep secrets outside source and chat. Use ignored `.env` with mode 600 and an ignored
`.local/private` folder. Never run `docker compose config` without `-q` or print
container environment variables when secrets are configured. Docker administrators
can inspect container environment; this is a controlled local test configuration,
not a production secret manager.

1. Preserve the current demo DB and volume. Create a NEW empty `akus_uat` database
   inside the existing PostgreSQL service, only if it does not already exist:
   `docker compose exec -T db createdb -U akus_demo akus_uat`.
   If it exists, inspect/use it; do not reset it. Switch the same application stack
   to this protected dataset; do not start a second app.
2. Privately set these `.env` fields:

   | Field | Value |
   |---|---|
   | `AKUS_ENV` | `local` for loopback UAT |
   | `AKUS_DEMO_ENABLED` | `false` |
   | `AKUS_DATABASE_URL` | `postgresql+psycopg://akus_demo:akus_demo@db:5432/akus_uat` for this local Compose DB only |
   | `AKUS_PUBLIC_ORIGIN` | `http://127.0.0.1:8080` |
   | `AKUS_INSTITUTION_LABEL` | Approved institution display name |
   | `AKUS_GOOGLE_CLIENT_ID` | The approved Web OAuth client ID |
   | `AKUS_GOOGLE_CLIENT_SECRET` | The private Web OAuth secret |
   | `AKUS_GOOGLE_REDIRECT_URI` | Exact callback above |
   | `AKUS_SESSION_KEY` | Newly generated Fernet key, persisted privately |

   Generate a key directly into a private file without displaying it:
   `umask 077; mkdir -p .local/private; .venv/bin/python -c 'from cryptography.fernet import Fernet; from pathlib import Path; p=Path(".local/private/session-key"); p.open("xb").write(Fernet.generate_key())'`.
   Copy its value into `.env` in a private local editor. The exclusive creation
   fails if a key already exists; do not overwrite an in-use key casually.
3. `docker compose config -q`, then `docker compose up -d --build`.
   Migration advances the selected DB; institutional mode skips fictional seeding.
   Verify `http://127.0.0.1:8080/api/v1/health/ready` and `/api/v1/auth/config`.
   Partial OAuth settings fail startup; all blank settings show CONFIGURATION REQUIRED.

For HTTPS, set the corresponding HTTPS origin/callback and configure authorized
TLS hosting separately. Cookies become Secure automatically. Production configuration
rejects loopback HTTP, demo access and the public demonstration database credential.
This repository's current loopback Compose deployment is not production ready.

## Operator-only first Admin bootstrap

No first-visitor grant exists. Bootstrap requires a private approved JSON roster with
`staff_key`, `display_name`, `email`, `department_code`, `department_name`,
`employment_starts_on` (YYYY-MM-DD), `authorized_from` (timezone-aware ISO instant),
and `source_reference` (official authorization). Do not derive these from an email.
For this UAT, use the approved record for the intended Admin in the UAT template.
The bootstrap creates non-faculty employment and a separate Admin grant; use it only
when those are the approved source facts. No Google identity or session is invented.

Save the approved record as `.local/private/first-admin.json` (mode 600), then:

```sh
docker compose run --rm --no-deps \
  -v "$PWD/.local/private/first-admin.json:/run/first-admin.json:ro" \
  api python -m akus.identity.operator bootstrap \
  --roster /run/first-admin.json --operator-authorized
```

The grant is idempotent. Changed facts are rejected; a revoked bootstrap is not
silently restored. The account holder must then use **Continue with Google**.
Only a verified identity matching the approved active email can link. Successful
login leads to Administration workspace. The CLI never signs in as that person.

Emergency Admin grant revocation (explicit operator authorization required):

```sh
docker compose run --rm --no-deps api python -m akus.identity.operator revoke \
  --staff-key APPROVED_STAFF_KEY --reason 'Official revocation order reference' \
  --operator-authorized
```

Current permissions are re-resolved on requests and after source-command locks.
Revoking Admin removes its authority, not the permanent staff record. Disabling the
person or closing the effective employment episode denies institutional access.
To replace a Google account, review its verified pending request, select the approved
person and the exact old link to revoke, and record source/reason. An issuer+subject
can never move to another person. Revoked links and email observations remain.

## Five-person manual UAT — all currently BLOCKED / NOT VERIFIED

The exact user-specified addresses and blank approval fields are in
`docs/fixtures/phase2-uat-roster.json`. Keep that tracked template unfilled. Complete
a private copy from approved institutional sources. No real names, staff IDs,
departments, effective appointments or teaching allocations have been invented.

| Account | Intended UAT capacity | Required voluntary acceptance |
|---|---|---|
| faculty-harsh1.cse24@cmrit.ac.in | Faculty only | Google sign-in → Faculty workspace, own profile/teaching; no source writes or other staff records; ordinary route DRC → HoD |
| hod-ankit.cse24@cmrit.ac.in | HoD office only; NPTEL-exempt | Google sign-in → department oversight; only authorized departments; applicant route denied |
| DRC-awanish.cse24@cmrit.ac.in | Faculty + DRC Head; never HoD | Google sign-in → DRC workspace, own teaching, direct-to-HoD own-application readiness; no self-review action |
| admin-harsh.cse24@cmrit.ac.in | Admin only | Genuine bootstrap-linked login; roster/teaching staging, correction, account review; no academic decision grants |
| principle-nikshay.cse24@cmrit.ac.in | Principal only; NPTEL-exempt | Google sign-in → institution-wide read-only oversight; source commands and personal application denied |

After first Admin sign-in, use **Source imports** for approved staff CSV/XLSX, then
record approved office appointments and dates through the staff detail. The import
has no role column and never infers officeholding. Admin already provisioned by the
bootstrap must not be imported again. Use subject/teaching fixtures only if separately
authorized and conspicuously labeled synthetic, within this isolated UAT dataset.

For EACH participant: start with a fresh browser session, use Google consent, verify
its authorized source profile and intended capacity, test allowed read/action and
a denied direct API/UI path, reload, sign out, and confirm protected access is gone.
Record time, environment, approved staff reference and pass/fail privately. Do not
save auth URLs/codes/tokens/secrets in screenshots or reports. If consent is denied,
record the failure honestly. An email address alone never counts as a passed login.

Application submission, review decisions, quota publication and compliance credit
are future-phase dependencies, displayed as unavailable. UAT must not claim those
academic workflows passed. IO-02 teaching acceptance, P-54 leap-day deadlines and
other unratified policies remain pending.

## Implemented controls and limits

Authlib handles code exchange and S256 PKCE; joserfc verifies RS256/JWKS and required
issuer/audience/time/nonce/verified-email/domain claims. Discovery is Google-only.
State is server-side, browser-bound, expires after ten minutes and is consumed once.
No provider network request runs in an open DB transaction. Access/ID/refresh tokens
are not persisted. Sessions are opaque, hashed in PostgreSQL, eight-hour bounded,
rotated on login, HttpOnly/SameSite=Lax, Secure on HTTPS; mutations require exact
Origin and session CSRF. Logout deletes the server session. JSON responses are no-store.
Uvicorn access logs are disabled to avoid callback query-string leakage.

Local HTTP deliberately permits non-Secure cookies only on loopback. Institutional
mode disables demo login. Rate limiting is conservative per observed client/proxy IP;
production trusted-proxy configuration and broader deployment hardening remain a
later operational gate. Key rotation invalidates CSRF derivation and pending login
flows; coordinate session revocation/re-login with the operator. No external Google
logout, token revocation or account changes are claimed from local AKUS logout.
