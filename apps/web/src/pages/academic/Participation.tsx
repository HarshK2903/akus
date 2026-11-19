import {
  useCommand,
  reasonFields,
  type ApplicationRecord,
} from "../../lib/academic";
import { Field, SelectField, SourceFields } from "../../components/SourceUi";
import { Badge } from "../../components/ui";
import { CommandError } from "../../components/PeopleUi";
import { instant } from "../../lib/people";

function proofFields(f: FormData) {
  const timestamp = String(f.get("enrolled_at") || "");
  return {
    ...reasonFields(f),
    document_digest: f.get("document_digest"),
    observed_at: new Date(String(f.get("observed_at"))).toISOString(),
    enrolled_at: timestamp ? new Date(timestamp).toISOString() : null,
    enrolled_on: f.get("enrolled_on") || null,
  };
}
function ProofFields({ label }: { label: string }) {
  return (
    <>
      <p>
        Enter exactly one enrollment value matching the official source
        precision. A date alone cannot prove ordering within that day. Times use
        your browser's local timezone.
      </p>
      <Field
        label={`${label} enrollment time (local time)`}
        name="enrolled_at"
        type="datetime-local"
        step="1"
      />
      <Field
        label={`${label} enrollment date (date-only source)`}
        name="enrolled_on"
        type="date"
      />
      <Field
        label="Archived official document SHA-256"
        name="document_digest"
        pattern="[a-f0-9]{64}"
        required
      />
      <Field
        label="Evidence observed at (local time)"
        name="observed_at"
        type="datetime-local"
        step="1"
        required
      />
      <SourceFields />
    </>
  );
}
export function Participation({
  app,
  canVerify,
}: {
  app: ApplicationRecord;
  canVerify: boolean;
}) {
  const claim = useCommand();
  const verify = useCommand();
  const request = useCommand();
  const decide = useCommand();
  const data = app.participation;
  if (!data) return null;
  const live = ["UNDER_REVIEW", "APPROVED"].includes(app.state);
  const latest = data.claims[0];
  return (
    <>
      <section className="panel prose section-gap">
        <h2>External enrollment evidence</h2>
        <p>
          Institutional submission:{" "}
          {app.submitted_at
            ? instant(app.submitted_at)
            : "Not submitted — a draft is not permission to enroll."}
        </p>
        <Badge tone={data.verified_submission_first ? "neutral" : "warning"}>
          {data.verified_submission_first
            ? "HoD verified submission first"
            : latest
              ? "Enrollment pathway requires review"
              : "No external enrollment evidence recorded"}
        </Badge>
        <p>
          These records identify material retained in an official archive.
          Binary upload and malware scanning are not available here. An
          assertion or reference alone is not verified participation.
        </p>
        {app.own &&
          ["DRAFT", "UNDER_REVIEW", "APPROVED"].includes(app.state) && (
            <details>
              <summary>Record or correct enrollment evidence</summary>
              <form
                className="source-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  claim.mutate({
                    path: `/applications/${app.id}/enrollment-claims`,
                    body: {
                      expected_version: data.claim_version,
                      ...proofFields(new FormData(e.currentTarget)),
                    },
                  });
                }}
              >
                <ProofFields label="Claimed" />
                <label className="checkbox-label">
                  <input type="checkbox" required /> I report the actual event
                  and source precision; AKUS submission must not be backdated.
                </label>
                <CommandError error={claim.error} />
                <button className="primary" disabled={claim.isPending}>
                  Record enrollment assertion
                </button>
                {claim.isSuccess && (
                  <p role="status">
                    Assertion recorded; independent verification remains
                    required.
                  </p>
                )}
              </form>
            </details>
          )}
        <ol className="source-history">
          {[...data.findings, ...data.claims].map((c) => (
            <li key={c.id}>
              <strong>
                {c.outcome
                  ? `${c.outcome} · ${c.chronology?.replaceAll("_", " ")}`
                  : `Unverified claim ${c.version}`}
              </strong>
              <p>
                {c.enrolled_at
                  ? instant(c.enrolled_at)
                  : `${c.enrolled_on} · date only`}
              </p>
              <p>{c.reason}</p>
              <p className="wrap-anywhere">
                {c.source_reference} · SHA-256 {c.document_digest}
              </p>
              <small>Recorded {instant(c.recorded_at)}</small>
            </li>
          ))}
        </ol>
      </section>
      {canVerify && live && latest && (
        <section className="panel prose section-gap">
          <h2>Authenticate enrollment chronology</h2>
          <p>
            Independently inspect official evidence for {app.applicant}, exact
            offering {app.provider_id}. This finding grants no certificate or
            compliance credit.
          </p>
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              verify.mutate({
                path: `/applications/${app.id}/verify-enrollment`,
                body: {
                  claim_id: latest.id,
                  expected_version: data.finding_version,
                  outcome: f.get("outcome"),
                  independently_authenticated: true,
                  ...proofFields(f),
                },
              });
            }}
          >
            <ProofFields label="Official" />
            <SelectField label="Enrollment verification finding" name="outcome">
              <option value="UNRESOLVED">Unresolved evidence</option>
              <option value="VERIFIED">Independently authenticated</option>
              <option value="REJECTED">Evidence rejected</option>
            </SelectField>
            <label className="checkbox-label">
              <input type="checkbox" required /> I independently checked the
              exact identity, offering, source and event precision.
            </label>
            <CommandError error={verify.error} />
            <button className="primary" disabled={verify.isPending}>
              Record enrollment finding
            </button>
            {verify.isSuccess && (
              <p role="status">
                Independent finding recorded with current office authority.
              </p>
            )}
          </form>
        </section>
      )}
      {app.own && live && latest && !data.pending_withdrawal && (
        <section className="panel prose section-gap">
          <h2>Request withdrawal after enrollment</h2>
          <p>
            Before commencement, current HoD can authorize release after
            verification. A request alone keeps the seat counted. After
            commencement voluntary withdrawal retains it.
          </p>
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              request.mutate({
                path: `/applications/${app.id}/withdrawal-requests`,
                body: {
                  expected_version: app.version,
                  voluntary_request: true,
                  ...reasonFields(new FormData(e.currentTarget)),
                },
              });
            }}
          >
            <SourceFields />
            <label className="checkbox-label">
              <input type="checkbox" required /> I voluntarily request HoD
              review of my withdrawal.
            </label>
            <CommandError error={request.error} />
            <button disabled={request.isPending}>
              Request HoD withdrawal decision
            </button>
          </form>
        </section>
      )}
      {data.pending_withdrawal && (
        <section className="panel prose section-gap">
          <h2>Pending HoD withdrawal request</h2>
          <p>{data.pending_withdrawal.reason}</p>
          <p>
            Source: {data.pending_withdrawal.source_reference}. Current
            allocation remains counted.
          </p>
          {canVerify && (
            <form
              className="source-form"
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                decide.mutate({
                  path: `/applications/${app.id}/withdrawal-decision`,
                  body: {
                    expected_version: app.version,
                    request_id: data.pending_withdrawal!.id,
                    decision: f.get("decision"),
                    independently_checked: true,
                    ...reasonFields(f),
                  },
                });
              }}
            >
              <SelectField label="Withdrawal request decision" name="decision">
                <option value="DENY">
                  Deny request; keep application and count
                </option>
                <option value="AUTHORIZE">
                  Authorize verified pre-start release
                </option>
              </SelectField>
              <SourceFields />
              <label className="checkbox-label">
                <input type="checkbox" required /> I independently checked the
                request, chronology and commencement evidence.
              </label>
              <CommandError error={decide.error} />
              <button disabled={decide.isPending}>
                Record withdrawal decision
              </button>
            </form>
          )}
        </section>
      )}
    </>
  );
}
