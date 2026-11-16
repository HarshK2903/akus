# Local demonstration

1. Open http://127.0.0.1:5173 and choose a clearly fictional demo identity. Google sign-in is disabled with an explanation.
2. Enter the workspace. Refresh reads actual API/database state; worker shows running only for a recent heartbeat. Academic years are LOCAL/DEMO rows, not published quotas.
3. Open Profile & access to inspect your current source authority, employment episodes, office history and access limits.
4. Open Policy guide. Search `quota` or `P-51`; confirmed and pending decisions remain distinct. Search survives reload.
5. On small screens use Open navigation; Escape closes the dialog and restores focus. Scroll the year table with keyboard focus.
6. Sign out to revoke the server session. A direct profile link then returns to sign-in.

Faculty and DRC use `/app/home`, HoD uses `/hod/home`, Principal `/principal/home`, Admin `/admin/home`. These are foundation views, not full role dashboards. HoD and Principal have no personal application workflow. The six login fixtures plus two history-only fixtures are not real staff. Reviews, quota edits, catalog, applications, certificate evidence, annual/Silver assessment, reports will arrive in later tested phases.

## Staff and office source workflow (Phase 2A)

1. Choose **Nila Shah · Admin**. Open **Staff directory → Add staff record**. Enter a new permanent staff key, display name, home department, employment start, classification, source reference and reason. Submit; the saved detail and immutable change event appear only after the server commits. This does not create a sign-in account.
2. On detail choose **Employment history** to inspect episodes; Tara Bose's fictional history shows two episodes sharing one identity. Editing past episodes and recording separation are not yet available.
3. Choose **Record appointment**. Select source-authorized office and scope, exact IST start/end (end exclusive), source and rationale. DRC must be faculty. An overlapping DRC/HoD appointment is rejected even across departments; input remains for correction. Existing academic cases are not altered.
4. In **Office appointments**, choose **View appointment**. Inspect original issued dates separately from current effective expiry. For a current appointment, enter the official end reason/source, confirm the checkbox and select **End appointment now**. The record remains; staff history shows the immutable end event. Do this only on a temporary demonstration appointment if preserving the six standard login examples.
5. Choose **Dev Mehta · Principal** to read the institution-wide staff/office registers with no source-write controls. Leela Iyer sees only CSE staff and scoped offices, Omar Das only ECE. Faculty/DRC see their own source histories. All API scopes are server-enforced.

The source actions above are functional LOCAL/DEMO workflows. All new source records are fictional in this environment. There is no institutional OIDC, staff import, teaching management, academic approval, quota or compliance integration yet. Role dashboards remain partial.
