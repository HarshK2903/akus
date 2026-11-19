import { useQuery } from "@tanstack/react-query";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { api } from "../../lib/api";
import { instant } from "../../lib/people";
import {
  useCommand,
  useContextData,
  reasonFields,
  type Offering,
} from "../../lib/academic";
import { PageHeader, Loading, ErrorState, Badge } from "../../components/ui";
import { Field, SelectField, SourceFields } from "../../components/SourceUi";
import { Pager, CommandError } from "../../components/PeopleUi";

const labels = {
  NO_VALID_CERT: "No valid certificate",
  VALID_CERT: "Valid certificate",
  UNRESOLVED: "Unresolved",
};
const eligibility = {
  OUTCOME_PENDING: "Awaiting conclusive verification",
  REPEAT_PROHIBITED: "Repeat prohibited",
  NO_CERT_VERIFIED: "No certificate verified",
};
type Evidence = {
  id: string;
  reason: string;
  version: number;
  actor_id: string;
  office_id?: string;
  outcome?: keyof typeof labels;
  asserted_outcome?: keyof typeof labels;
  concluded_on?: string;
  source_reference: string;
  document_digest: string;
  observed_at: string;
  recorded_at: string;
};
type Attempt = {
  id: string;
  offering_id: string;
  course: string;
  provider_id: string;
  applicant: string;
  own: boolean;
  can_decide: boolean;
  eligibility: keyof typeof eligibility;
  evidence_version: number;
  finding_version: number;
  evidence: Evidence[];
  findings: Evidence[];
};
function SourceProof() {
  return (
    <>
      <Field
        label="Archived document SHA-256"
        name="digest"
        pattern="[a-f0-9]{64}"
        required
      />
      <Field
        label="Evidence observed at (local time)"
        name="observed"
        type="datetime-local"
        step="1"
        required
      />
      <SourceFields />
    </>
  );
}
function proof(f: FormData) {
  return {
    ...reasonFields(f),
    document_digest: f.get("digest"),
    observed_at: new Date(String(f.get("observed"))).toISOString(),
  };
}
function OutcomeSelect({ label }: { label: string }) {
  return (
    <SelectField name="outcome" label={label} defaultValue="UNRESOLVED">
      {Object.entries(labels).map(([k, v]) => (
        <option key={k} value={k}>
          {v}
        </option>
      ))}
    </SelectField>
  );
}
function Report({ offering, version }: { offering: string; version: number }) {
  const navigate = useNavigate();
  const cmd = useCommand((id) => navigate("/app/previous-attempts/" + id));
  return (
    <form
      className="panel prose source-form section-gap"
      onSubmit={(e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        cmd.mutate({
          path: "/outcome-verifications",
          body: {
            ...proof(f),
            offering_id: offering,
            asserted_outcome: f.get("outcome"),
            expected_version: version,
          },
        });
      }}
    >
      <h2>
        {version ? "Add revised evidence" : "Request outcome verification"}
      </h2>
      <p>
        Identify the source in the official archive. Your department HoD reviews
        this evidence before a fresh application can be considered.
      </p>
      <OutcomeSelect label="Reported prior result" />
      <SourceProof />
      <CommandError error={cmd.error} />
      <button className="primary" disabled={cmd.isPending}>
        Send evidence for review
      </button>
      {cmd.isSuccess && (
        <p role="status">Evidence recorded for independent review.</p>
      )}
    </form>
  );
}
function Verification({ a }: { a: Attempt }) {
  const cmd = useCommand();
  return (
    <form
      className="panel prose source-form section-gap"
      onSubmit={(e) => {
        e.preventDefault();
        const f = new FormData(e.currentTarget);
        cmd.mutate({
          path: "/outcome-verifications/" + a.id + "/decision",
          body: {
            ...proof(f),
            expected_version: a.finding_version,
            evidence_id: a.evidence[0].id,
            outcome: f.get("outcome"),
            concluded_on: f.get("concluded") || null,
            conclusive_official_result: f.has("conclusive"),
            independently_authenticated_person_and_run: f.has("independent"),
          },
        });
      }}
    >
      <h2>Record independent finding</h2>
      <p>
        Verify the source for {a.applicant} and offering {a.provider_id}. Choose
        Unresolved if a screenshot or missing certificate leaves the result
        uncertain.
      </p>
      <OutcomeSelect label="HoD outcome finding" />
      <Field label="Official result date" type="date" name="concluded" />
      <SourceProof />
      <label className="checkbox-label">
        <input type="checkbox" name="independent" required />I independently
        checked the person and exact offering.
      </label>
      <label className="checkbox-label">
        <input type="checkbox" name="conclusive" />
        The official result conclusively establishes this outcome.
      </label>
      <CommandError error={cmd.error} />
      <button className="primary" disabled={cmd.isPending}>
        Record finding
      </button>
      {cmd.isSuccess && <p role="status">Finding recorded.</p>}
    </form>
  );
}
export function AttemptList({ inbox = false }: { inbox?: boolean }) {
  const [params, setParams] = useSearchParams();
  const offset = Number(params.get("offset")) || 0;
  const endpoint = inbox ? "/outcome-verifications" : "/previous-attempts";
  const root = inbox ? "/hod/outcome-verifications" : "/app/previous-attempts";
  const search = params.get("search") || "";
  const order = params.get("order") || "newest";
  const q = useQuery({
    queryKey: [endpoint, offset, search, order],
    queryFn: () =>
      api<{ items: Attempt[]; total: number }>(
        endpoint +
          "?" +
          new URLSearchParams({ offset: String(offset), search, order }),
      ),
  });

  if (q.error)
    return <ErrorState error={q.error} retry={() => void q.refetch()} />;
  return (
    <>
      <PageHeader
        title={inbox ? "Prior-result verification inbox" : "My prior attempts"}
        description={
          inbox
            ? "Review documentary outcomes for eligible department members."
            : "Repeat eligibility follows your permanent record across offerings of the same canonical course."
        }
      />
      {!inbox && (
        <p>
          <Link to="/app/catalog">Find a prior offering in the catalog</Link>
        </p>
      )}
      <section className="panel prose">
        <h2>{inbox ? "Verification cases" : "Attempt history"}</h2>
        <Field
          label="Search course, offering or applicant"
          value={search}
          onChange={(e) =>
            setParams({ search: e.target.value, order }, { replace: true })
          }
        />
        <SelectField
          label="Sort attempts"
          value={order}
          onChange={(e) => setParams({ search, order: e.target.value })}
        >
          <option value="newest">Newest first</option>
          <option value="oldest">Oldest first</option>
        </SelectField>
        {q.isPending && <Loading />}
        {q.data && !q.data.items.length && (
          <p>No prior attempts recorded here.</p>
        )}
        <ul className="source-history">
          {q.data?.items.map((a) => (
            <li key={a.id}>
              <Link
                to={
                  root +
                  "/" +
                  a.id +
                  (params.size ? "?" + params.toString() : "")
                }
              >
                {a.course} · {a.provider_id}
              </Link>
              <p>
                {a.applicant} · {eligibility[a.eligibility]}
              </p>
            </li>
          ))}
        </ul>
        <Pager
          offset={offset}
          limit={25}
          total={q.data?.total || 0}
          change={(next) => setParams({ search, order, offset: String(next) })}
        />
      </section>
    </>
  );
}
export function NewAttempt() {
  const { offeringId } = useParams();
  const context = useContextData();
  const q = useQuery({
    queryKey: ["attempt-offering", offeringId],
    queryFn: () => api<Offering>("/nptel/offerings/" + offeringId),
  });
  if (q.isPending || context.isPending) return <Loading />;
  if (q.error || context.error)
    return (
      <ErrorState
        error={q.error || context.error!}
        retry={() => {
          void q.refetch();
          void context.refetch();
        }}
      />
    );
  return (
    <>
      <PageHeader
        title="Report a prior attempt"
        description={q.data.provider_id}
      />
      <Link to="/app/previous-attempts">View prior attempts</Link>
      {context.data.can_apply && <Report offering={q.data.id} version={0} />}
    </>
  );
}
export function AttemptDetail({ inbox = false }: { inbox?: boolean }) {
  const { attemptId } = useParams();
  const [params] = useSearchParams();
  const context = useContextData();
  const q = useQuery({
    queryKey: ["attempt", attemptId],
    queryFn: () => api<Attempt>("/previous-attempts/" + attemptId),
  });
  if (q.isPending) return <Loading />;
  if (q.error)
    return <ErrorState error={q.error} retry={() => void q.refetch()} />;
  const a = q.data;
  return (
    <>
      <PageHeader
        title={a.course}
        description={a.applicant + " · " + a.provider_id}
      />
      <Link
        to={
          (inbox ? "/hod/outcome-verifications" : "/app/previous-attempts") +
          (params.size ? "?" + params.toString() : "")
        }
      >
        {inbox ? "Verification inbox" : "My prior attempts"}
      </Link>
      <section className="panel prose section-gap">
        <h2>Repeat eligibility</h2>
        <Badge>{eligibility[a.eligibility]}</Badge>
        <p>
          {a.eligibility === "REPEAT_PROHIBITED"
            ? "A verified valid certificate bars future attempts at this canonical course."
            : a.eligibility === "NO_CERT_VERIFIED"
              ? "A fresh application may be considered after all other admission checks."
              : "Drafts remain available. Submission requires a conclusive independent outcome."}{" "}
          Verification alone reserves no seat.
        </p>
        <Link to="/app/catalog">Browse offerings</Link>
      </section>
      {(
        [
          ["HoD findings", a.findings],
          ["Submitted evidence", a.evidence],
        ] as const
      ).map(([title, rows]) => (
        <section key={title} className="panel prose section-gap">
          <h2>{title}</h2>
          {!rows.length && <p>Awaiting independent review.</p>}
          <ol className="source-history">
            {rows.map((r) => (
              <li key={r.id}>
                <strong>
                  {labels[(r.outcome ?? r.asserted_outcome)!]} · revision{" "}
                  {r.version}
                </strong>
                <p>{r.reason}</p>
                <p>{r.source_reference}</p>
                <small className="wrap-anywhere">
                  SHA-256 {r.document_digest}
                </small>
                <p>
                  Observed {instant(r.observed_at)} · Recorded{" "}
                  {instant(r.recorded_at)}
                </p>
                {r.office_id && (
                  <p className="wrap-anywhere">
                    Reviewing appointment {r.office_id} · result date{" "}
                    {r.concluded_on || "unresolved"}
                  </p>
                )}
              </li>
            ))}
          </ol>
        </section>
      ))}
      {a.own && context.data?.can_apply && (
        <Report offering={a.offering_id} version={a.evidence_version} />
      )}
      {a.can_decide && <Verification a={a} />}
    </>
  );
}
