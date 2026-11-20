import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Link,
  useParams,
  useOutletContext,
  useSearchParams,
} from "react-router-dom";
import { api, type Identity } from "../../lib/api";
import { accessKey, instant } from "../../lib/people";
import { useCommand, reasonFields } from "../../lib/academic";
import { Field, SelectField, SourceFields } from "../../components/SourceUi";
import { Loading, PageHeader, ErrorState, Badge } from "../../components/ui";
import { CommandError, Pager } from "../../components/PeopleUi";

import { words } from "../../lib/compliance";
type Entry = {
  id: string;
  version: number;
  recorded_at: string;
  actor_id: string;
  kind: string;
  facts: Record<string, string | number | boolean | null>;
  document_id: string | null;
  document_state: string | null;
  can_download: boolean;
};
type Dossier = {
  archive: {
    recorded_at: string;
    facts: Record<string, string | number | boolean | null>;
  } | null;
  application_id: string;
  course: string;
  offering: string;
  version: number;
  status: string;
  can_register: boolean;
  can_verify: boolean;
  authority: string;
  events: Entry[];
  subjects: { id: string; name: string; can_verify: boolean }[];
};
type Library = {
  items: {
    id: string;
    course: string;
    person: string;
    status: string;
    state: string;
  }[];
  total: number;
};
export function CertificateLibrary() {
  const actor = useOutletContext<Identity>();
  const [params, set] = useSearchParams();
  const offset = Math.max(0, Number(params.get("offset")) || 0),
    search = params.get("search") || "",
    pending = params.get("pending") === "true";
  const query = useQuery({
    queryKey: ["certificates", accessKey(actor), params.toString()],
    queryFn: () =>
      api<Library>(
        `/certificates?${new URLSearchParams({ search, pending: String(pending), offset: String(offset) })}`,
      ),
  });
  function change(values: Record<string, string>) {
    set(
      new URLSearchParams({
        ...Object.fromEntries(params),
        offset: "0",
        ...values,
      }),
    );
  }
  return (
    <>
      <PageHeader
        title="Certificate library"
        description="Find an application to record an actual exam, submit certificate evidence or inspect its verification history."
      />
      <section className="panel source-form">
        <Field
          label="Search courses or staff"
          type="search"
          value={search}
          onChange={(e) => change({ search: e.target.value })}
        />
        <label>
          <input
            type="checkbox"
            checked={pending}
            onChange={(e) => change({ pending: String(e.target.checked) })}
          />{" "}
          Awaiting independent review
        </label>
      </section>
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <section className="panel section-gap">
          <h2>Application dossiers</h2>
          <ul className="record-cards">
            {query.data.items.map((i) => (
              <li key={i.id}>
                <Link to={"/app/certificates/" + i.id}>{i.course}</Link>
                <span>
                  {i.person} · {words(i.state)}
                </span>
                <Badge>{words(i.status)}</Badge>
              </li>
            ))}
          </ul>
          {!query.data.total && (
            <p>No submitted applications match these filters in your scope.</p>
          )}
          <Pager
            offset={offset}
            limit={20}
            total={query.data.total}
            change={(v) => change({ offset: String(v) })}
          />
        </section>
      )}
    </>
  );
}
function EvidenceForm({
  d,
  mode,
}: {
  d: Dossier;
  mode: "evidence" | "verify" | "disposition";
}) {
  const cmd = useCommand();
  const [problem, setProblem] = useState("");
  const [busy, setBusy] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [subject, setSubject] = useState("");
  const registering = mode === "evidence",
    deciding = mode === "disposition";
  return (
    <form
      className="panel source-form section-gap"
      onSubmit={async (e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        setProblem("");
        setBusy(true);
        try {
          let digest = String(f.get("digest") || "");
          let attachment;
          if (file) {
            if (file.size > 2097152 || file.type !== "application/pdf")
              throw new Error("Select a PDF of 2 MiB or less.");
            const bytes = new Uint8Array(await file.arrayBuffer());
            digest = Array.from(
              new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
              (b) => b.toString(16).padStart(2, "0"),
            ).join("");
            let raw = "";
            for (let i = 0; i < bytes.length; i += 8192)
              raw += String.fromCharCode(...bytes.subarray(i, i + 8192));
            attachment = {
              media_type: "application/pdf",
              base64_data: btoa(raw),
            };
          }
          const proof = {
            ...reasonFields(f),
            document_digest: digest,
            observed_at: new Date(String(f.get("observed"))).toISOString(),
            expected_version: d.version,
          };
          const exam = {
            actual_exam_on: f.get("exam"),
            issued_on: f.get("issued") || null,
            certificate_key: f.get("key") || null,
            score_percent: f.get("score") ? Number(f.get("score")) : null,
            sitting: f.get("sitting"),
            subject_id: subject || null,
          };
          const exact = f.get("exact");
          const body = deciding
            ? {
                ...proof,
                outcome: f.get("outcome"),
                independently_checked: f.has("checked"),
              }
            : registering
              ? { ...proof, ...exam, attachment }
              : {
                  ...proof,
                  ...exam,
                  credential_grade: f.get("grade") || null,
                  actual_exam_at: exact
                    ? new Date(String(exact)).toISOString()
                    : null,
                  checked_person_offering_certificate: f.has("checked"),
                  verified_exam_and_score_sharing: f.has("shared"),
                  relevance_basis: subject ? f.get("relevance") : null,
                };
          cmd.mutate({
            path: `/certificates/${d.application_id}/${mode}`,
            body,
          });
        } catch (err) {
          setProblem(
            err instanceof Error
              ? err.message
              : "Unable to read the evidence file.",
          );
        } finally {
          setBusy(false);
        }
      }}
    >
      <h2>
        {registering
          ? "Record exam or certificate evidence"
          : deciding
            ? "Reject evidence or revoke a credential"
            : "Verify official certificate"}
      </h2>
      {registering && (
        <>
          <p>
            Attach a private PDF or identify a document in the official archive.
            Your submission goes to independent review.
          </p>
          <Field
            label="Private PDF (optional, up to 2 MiB)"
            type="file"
            accept="application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </>
      )}
      {!file && (
        <Field
          label="Official document SHA-256"
          name="digest"
          required
          pattern="[0-9a-f]{64}"
        />
      )}
      {!deciding && (
        <>
          <Field
            label="Exam sitting or session"
            name="sitting"
            minLength={2}
            required
          />
          <Field
            label="Actual examination date"
            name="exam"
            type="date"
            required
          />
          <Field
            label="Issuer certificate identifier"
            name="key"
            minLength={3}
            required={!registering}
          />
          <Field
            label="Certificate issue date"
            name="issued"
            type="date"
            required={!registering}
          />
          <Field
            label="Score percentage"
            name="score"
            type="number"
            min={0}
            max={100}
            step="any"
            required={!registering}
          />
          <SelectField
            label="Related teaching subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
          >
            <option value="">No subject assessment</option>
            {d.subjects
              .filter((s) => registering || s.can_verify)
              .map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
          </SelectField>
        </>
      )}
      {!registering && !deciding && (
        <>
          <Field
            label="Exact local exam time, if sourced"
            type="datetime-local"
            step="1"
            name="exact"
          />
          <Field label="Issuer grade or classification" name="grade" />
          {subject && (
            <Field
              label="Documented academic relevance"
              name="relevance"
              minLength={5}
              required
            />
          )}
          <label>
            <input required type="checkbox" name="checked" /> I independently
            verified the named person, offering and certificate with the issuer.
          </label>
          <label>
            <input required type="checkbox" name="shared" /> I verified actual
            exam participation and score sharing.
          </label>
        </>
      )}
      {deciding && (
        <>
          <SelectField label="Finding" name="outcome">
            <option value="REJECTED">Reject pending evidence</option>
            <option value="REVOKED">Record official revocation</option>
          </SelectField>
          <label>
            <input required type="checkbox" name="checked" /> I independently
            checked the official source for this decision.
          </label>
        </>
      )}
      <Field
        label="Evidence observed at (local time)"
        name="observed"
        type="datetime-local"
        step="1"
        required
      />
      <SourceFields />
      {problem && <p role="alert">{problem}</p>}
      <CommandError error={cmd.error} />
      <button className="primary" disabled={busy || cmd.isPending}>
        {registering
          ? "Submit evidence for review"
          : deciding
            ? "Record disposition"
            : "Record independent verification"}
      </button>
      {cmd.isSuccess && <p role="status">Evidence history updated.</p>}
    </form>
  );
}
export function CertificateDetail() {
  const { aid } = useParams();
  const actor = useOutletContext<Identity>();
  const q = useQuery({
    queryKey: ["credential", aid, accessKey(actor)],
    queryFn: () => api<Dossier>("/certificates/" + aid),
  });
  if (q.isPending) return <Loading />;
  if (q.isError)
    return <ErrorState error={q.error} retry={() => void q.refetch()} />;
  const d = q.data;
  return (
    <>
      <PageHeader
        title={d.course}
        description={"Certificate dossier · " + d.offering}
        action={<Link to="/app/certificates">Certificate library</Link>}
      />
      <section className="panel">
        <h2>Verification history</h2>
        <Badge>{words(d.status)}</Badge>
        <p>
          {d.can_verify
            ? d.authority
            : "Final verification requires an independent, application-specific appointment."}
        </p>
        {d.archive && (
          <p>
            Archived verification · {String(d.archive.facts.certificate_key)} ·
            exam {String(d.archive.facts.actual_exam_on)} ·{" "}
            {instant(d.archive.recorded_at)}
          </p>
        )}
        {!d.events.length && !d.archive && (
          <p>No exam evidence has been submitted for this application.</p>
        )}
        <ol className="source-timeline">
          {d.events.map((r) => (
            <li key={r.id}>
              <strong>
                Revision {r.version} · {words(r.kind)}
              </strong>
              <time>{instant(r.recorded_at)}</time>
              <p>{r.facts.reason}</p>
              <dl className="revision-facts">
                {Object.entries(r.facts)
                  .filter(([, v]) => v !== null)
                  .map(([k, v]) => (
                    <div key={k}>
                      <dt>{words(k)}</dt>
                      <dd>{String(v)}</dd>
                    </div>
                  ))}
              </dl>
              {r.document_id && (
                <p>
                  Private PDF · {words(r.document_state || "quarantined")}{" "}
                  {r.can_download && (
                    <a
                      href={`/api/v1/certificates/${aid}/documents/${r.document_id}`}
                    >
                      Download PDF
                    </a>
                  )}
                </p>
              )}
            </li>
          ))}
        </ol>
      </section>
      {d.can_register && <EvidenceForm d={d} mode="evidence" />}
      {d.can_verify && (d.version > 0 || !!d.archive) && (
        <>
          <ExamFinding d={d} />
          <EvidenceForm d={d} mode="verify" />
          <EvidenceForm d={d} mode="disposition" />
        </>
      )}
    </>
  );
}

function ExamFinding({ d }: { d: Dossier }) {
  const cmd = useCommand();
  return (
    <form
      className="panel source-form section-gap"
      onSubmit={(e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        const t = f.get("exact");
        cmd.mutate({
          path: "/certificates/" + d.application_id + "/exam",
          body: {
            ...reasonFields(f),
            expected_version: d.version,
            document_digest: f.get("digest"),
            observed_at: new Date(String(f.get("observed"))).toISOString(),
            actual_exam_on: f.get("day"),
            actual_exam_at: t ? new Date(String(t)).toISOString() : null,
            sitting: f.get("sitting"),
            checked_person_offering_attendance: f.has("checked"),
          },
        });
      }}
    >
      <h2>Confirm attendance while results are pending</h2>
      <Field
        label="Attendance register SHA-256"
        name="digest"
        required
        pattern="[0-9a-f]{64}"
      />
      <Field
        label="Confirmed exam sitting"
        name="sitting"
        required
        minLength={2}
      />
      <Field label="Confirmed exam date" name="day" type="date" required />
      <Field
        label="Exact sitting time if documented"
        name="exact"
        type="datetime-local"
        step="1"
      />
      <Field
        label="Attendance source observed at"
        name="observed"
        type="datetime-local"
        step="1"
        required
      />
      <SourceFields />
      <label>
        <input type="checkbox" required name="checked" /> I independently
        authenticated attendance for this person and offering.
      </label>
      <CommandError error={cmd.error} />
      <button disabled={cmd.isPending}>Record verified attendance</button>
      {cmd.isSuccess && <p role="status">Attendance recorded.</p>}
    </form>
  );
}
