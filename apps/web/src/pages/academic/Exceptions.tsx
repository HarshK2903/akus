import { useQuery } from "@tanstack/react-query";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../../lib/api";
import { instant } from "../../lib/people";
import { reasonFields, useCommand } from "../../lib/academic";
import { Badge, Loading, PageHeader, ErrorState } from "../../components/ui";
import { CommandError, Pager } from "../../components/PeopleUi";
import { Field, SelectField, SourceFields } from "../../components/SourceUi";

type Kind = "integrity" | "separation";
type Row = {
  id: string;
  app_id: string;
  applicant: string;
  offering: string;
  reason: string;
  status: string;
  updated_at: string;
};
type Event = {
  id: string;
  action: string;
  recorded_at: string;
  actor: string | null;
  office: string | null;
  facts: Record<string, unknown>;
};
type Detail = Row & {
  state: string;
  other_open_reviews: string[];
  submitted_at: string;
  allocation: string;
  current_pool: string;
  original_pool: string;
  facts: Record<string, unknown>;
  events: Event[];
  can_decide: boolean;
  may_verify_absence: boolean;
  may_verify_certificate: boolean;
  designated_subject_id: string | null;
  subjects_at_separation: Record<string, unknown>[];
};
function timestamp(f: FormData, name: string) {
  const value = f.get(name);
  return value ? new Date(String(value)).toISOString() : null;
}
function Evidence() {
  return (
    <>
      <SourceFields />
      <Field
        label="Official document SHA-256"
        name="digest"
        required
        pattern="[a-f0-9]{64}"
      />
      <Field
        label="Source observed at (local time)"
        name="observed"
        type="datetime-local"
        required
        step="1"
      />
    </>
  );
}
function proof(f: FormData) {
  return {
    ...reasonFields(f),
    document_digest: f.get("digest"),
    observed_at: timestamp(f, "observed"),
  };
}
export function PermanentOrder({
  episodes,
}: {
  episodes: { id: string; ends_before?: unknown; starts_on?: unknown }[];
}) {
  const records = episodes.filter((e) => e.ends_before),
    cmd = useCommand();
  return (
    <section className="panel prose section-gap">
      <h2>Permanent departure order</h2>
      {!records.length ? (
        <p>
          Record the official employment end date before confirming a permanent
          departure.
        </p>
      ) : (
        <form
          className="source-form"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget),
              episode = records.find((r) => r.id === f.get("episode"));
            if (episode)
              cmd.mutate({
                path:
                  "/admin/employment-episodes/" +
                  episode.id +
                  "/permanent-separation",
                body: {
                  ...proof(f),
                  effective_on: episode.ends_before,
                  effective_at: timestamp(f, "effective"),
                  permanent_order_confirmed: true,
                },
              });
          }}
        >
          <SelectField name="episode" label="Officially ended episode" required>
            {records.map((r) => (
              <option key={r.id} value={r.id}>
                {String(r.starts_on)} to {String(r.ends_before)}
              </option>
            ))}
          </SelectField>
          <Field
            label="Effective time if stated in order (local time)"
            name="effective"
            type="datetime-local"
            step="1"
          />
          <Evidence />
          <label className="checkbox-label">
            <input type="checkbox" required />I checked the official permanent
            separation order for this episode.
          </label>
          <CommandError error={cmd.error} />
          <button className="primary" disabled={cmd.isPending}>
            Record permanent order
          </button>
          {cmd.isSuccess && (
            <p role="status">
              Permanent order recorded for reconciliation on its effective date.
            </p>
          )}
        </form>
      )}
    </section>
  );
}
const root = (k: Kind) =>
  "/hod/" + (k === "separation" ? "separation-cases" : "integrity");
export function ExceptionList({ kind }: { kind: Kind }) {
  const [params, set] = useSearchParams(),
    status = params.get("status") || "OPEN",
    offset = Number(params.get("offset")) || 0;
  const q = useQuery({
    queryKey: ["case-list", kind, status, offset],
    queryFn: () =>
      api<{ items: Row[]; total: number }>(
        `/${kind}-cases?status=${encodeURIComponent(status)}&offset=${offset}`,
      ),
  });
  return (
    <>
      <PageHeader
        title={
          kind === "separation"
            ? "Separation closure cases"
            : "Integrity reviews"
        }
        description={
          kind === "separation"
            ? "Review effective departure, enrollment and commencement for each counted seat."
            : "Review disputed chronology and corrected prior outcomes."
        }
      />
      <section className="panel prose">
        <SelectField
          label="Case status"
          value={status}
          onChange={(e) => set({ status: e.target.value })}
        >
          <option value="OPEN">Open</option>
          <option value="RESOLVED">Resolved</option>
          <option value="ALL">All cases</option>
        </SelectField>
        {q.isPending ? (
          <Loading />
        ) : q.error ? (
          <ErrorState error={q.error} retry={() => void q.refetch()} />
        ) : (
          <>
            <ul className="source-history">
              {q.data.items.map((c) => (
                <li key={c.id}>
                  <Link to={root(kind) + "/" + c.id + "?" + params.toString()}>
                    {c.applicant} · {c.offering}
                  </Link>
                  <p>
                    {c.reason.replaceAll("_", " ")} · {instant(c.updated_at)}
                  </p>
                </li>
              ))}
            </ul>
            {!q.data.total && <p>No cases match this status.</p>}
            <Pager
              total={q.data.total}
              offset={offset}
              limit={25}
              change={(next) => set({ status, offset: String(next) })}
            />
          </>
        )}
      </section>
    </>
  );
}
function Facts({ values }: { values: Record<string, unknown> }) {
  return (
    <dl>
      {Object.entries(values)
        .filter(([, v]) => v != null)
        .map(([key, v]) => (
          <div key={key}>
            <dt>{key.replaceAll("_", " ")}</dt>
            <dd className="wrap-anywhere">
              {typeof v === "object" ? JSON.stringify(v) : String(v)}
            </dd>
          </div>
        ))}
    </dl>
  );
}
export function ExceptionDetail({ kind }: { kind: Kind }) {
  const { caseId } = useParams(),
    [params] = useSearchParams(),
    cmd = useCommand();
  const q = useQuery({
    queryKey: ["case-detail", kind, caseId],
    queryFn: () => api<Detail>(`/${kind}-cases/${caseId}`),
  });
  if (q.isPending) return <Loading />;
  if (q.error)
    return <ErrorState error={q.error} retry={() => void q.refetch()} />;
  const c = q.data,
    is47 = c.reason === "Q47_CHRONOLOGY_REVIEW";
  return (
    <>
      <PageHeader
        title={
          kind === "integrity"
            ? "Integrity case dossier"
            : "Separation chronology"
        }
        description={c.applicant + " · " + c.offering}
      />
      <Link to={root(kind) + "?" + params.toString()}>Back to case list</Link>
      <section className="panel prose section-gap">
        <h2>Application and quota</h2>
        <Badge>{c.status}</Badge>
        <p>{c.reason.replaceAll("_", " ")}</p>
        <Facts
          values={{
            application_state: c.state,
            valid_submission: instant(c.submitted_at),
            allocation: c.allocation,
            current_pool: c.current_pool,
            original_pool: c.original_pool,
          }}
        />
        <Link to={"/app/applications/" + c.app_id}>Application history</Link>
      </section>
      <section className="panel prose section-gap">
        <h2>Case timeline</h2>
        {c.other_open_reviews.map((r) => (
          <p key={r}>Related open review · {r.replaceAll("_", " ")}</p>
        ))}
        {c.events.map((e) => (
          <details key={e.id}>
            <summary>
              {e.action.replaceAll("_", " ")} · {instant(e.recorded_at)}
            </summary>
            <Facts values={{ ...e.facts, actor: e.actor, office: e.office }} />
          </details>
        ))}
      </section>
      {c.subjects_at_separation.length > 0 && (
        <section className="panel prose section-gap">
          <h2>Subjects at separation</h2>
          {c.subjects_at_separation.map((v, i) => (
            <Facts key={i} values={v} />
          ))}
        </section>
      )}
      {kind === "separation" && c.state === "SEPARATED" && (
        <HistoricalReview record={c} />
      )}
      {c.may_verify_absence && (
        <form
          className="panel prose source-form section-gap"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            cmd.mutate({
              path: "/separation-cases/" + c.id + "/roster-finding",
              body: {
                ...proof(f),
                expected_event_id: c.events[0].id,
                absence_through: timestamp(f, "through"),
                checked_complete_person_offering_roster: true,
              },
            });
          }}
        >
          <h2>Authenticate non-enrollment</h2>
          <Field
            label="Official roster coverage through (local time)"
            type="datetime-local"
            step="1"
            required
            name="through"
          />
          <Evidence />
          <label>
            <input type="checkbox" required />I checked the complete official
            enrollment roster for this person and offering through the recorded
            instant.
          </label>
          <CommandError error={cmd.error} />
          <button disabled={cmd.isPending}>Verify roster and apply Q43</button>
        </form>
      )}
      {c.can_decide && (
        <form
          className="panel prose source-form section-gap"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            cmd.mutate({
              path: `/${kind}-cases/${c.id}/decision`,
              body: {
                ...proof(f),
                expected_event_id: c.events[0].id,
                finding: f.get("finding"),
                independently_checked: true,
                separation_at: timestamp(f, "separation"),
                commencement_at: timestamp(f, "commencement"),
                enrollment_at: timestamp(f, "enrollment"),
                enrollment_on: f.get("enrollment_day") || null,
              },
            });
          }}
        >
          <h2>Independent decision</h2>
          <SelectField
            label="Documented finding"
            name="finding"
            required
            defaultValue=""
          >
            <option value="">Select a finding</option>
            {(kind === "integrity"
              ? ["UPHOLD", "INVALIDATE"]
              : is47
                ? ["INDETERMINATE", "BEFORE_START", "AFTER_START"]
                : ["Q44"]
            ).map((x) => (
              <option key={x}>{x}</option>
            ))}
          </SelectField>
          {kind === "separation" && (
            <>
              {is47 && (
                <>
                  <Field
                    label="Verified commencement time (if known)"
                    type="datetime-local"
                    name="commencement"
                    step="1"
                  />
                  <Field
                    label="Verified separation time (if known)"
                    type="datetime-local"
                    name="separation"
                    step="1"
                  />
                </>
              )}
              <Field
                label="Enrollment date when the source gives only a date"
                type="date"
                name="enrollment_day"
              />
              <Field
                label="Verified enrollment time (if established)"
                type="datetime-local"
                name="enrollment"
                step="1"
              />
            </>
          )}
          <Evidence />
          <label className="checkbox-label">
            <input type="checkbox" required />I independently checked the source
            evidence and event order.
          </label>
          <CommandError error={cmd.error} />
          <button className="primary" disabled={cmd.isPending}>
            Record case decision
          </button>
        </form>
      )}
      {kind === "integrity" && !c.can_decide && c.status === "OPEN" && (
        <p className="panel prose">
          Recognition is suspended. Final disposition requires an independent
          reviewer with a formal appointment for this case.
        </p>
      )}
    </>
  );
}

function HistoricalReview({ record }: { record: Detail }) {
  const [params, set] = useSearchParams(),
    asOf = params.get("as_of") || "";
  const path = "/separation-cases/" + record.id + "/historical-review",
    cmd = useCommand();
  const q = useQuery({
    queryKey: ["historical-evidence", record.id, asOf],
    queryFn: () =>
      api<{
        as_of: string;
        snapshot_at: string | null;
        annual: Record<string, string>;
        subjects: Record<string, unknown>[];
        finding: Record<string, unknown> | null;
      }>(path + (asOf ? "?as_of=" + encodeURIComponent(asOf) : "")),
  });
  return (
    <section className="panel prose section-gap">
      <h2>Historical certificate assessment</h2>
      <form
        className="source-form"
        onSubmit={(e) => {
          e.preventDefault();
          const f = new FormData(e.currentTarget);
          const next = new URLSearchParams(params);
          const t = timestamp(f, "asof");
          if (t) next.set("as_of", t);
          else next.delete("as_of");
          set(next);
        }}
      >
        <Field
          label="Records known by (local time)"
          name="asof"
          type="datetime-local"
          step="1"
        />
        <button>View historical report</button>
      </form>
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorState error={q.error} retry={() => void q.refetch()} />
      ) : (
        <>
          <p>Evidence known by {instant(q.data.as_of)}</p>
          {q.data.finding ? (
            <Facts values={q.data.finding} />
          ) : (
            <p>
              No authenticated certificate for this application at this time.
            </p>
          )}
          {Object.keys(q.data.annual).length > 0 && (
            <>
              <h3>Historical annual completion</h3>
              <Facts values={q.data.annual} />
            </>
          )}
          {q.data.subjects.map((s) => (
            <Facts key={String(s.subject_id)} values={s} />
          ))}
        </>
      )}
      {record.may_verify_certificate &&
        record.designated_subject_id &&
        !asOf &&
        q.data?.finding?.eligibility === "ELIGIBLE" &&
        (!q.data.finding.subject_id ||
          (q.data.finding.subject_id === record.designated_subject_id &&
            q.data.finding.silver ===
              "OBLIGATION_ACCEPTANCE_POLICY_PENDING_IO02")) && (
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              cmd.mutate({
                path: path + "/subject",
                body: {
                  ...proof(f),
                  subject_id: record.designated_subject_id,
                  finding_id: q.data?.finding?.id,
                  relevance_basis: f.get("basis"),
                  checked_subject_relevance: true,
                },
              });
            }}
          >
            <h3>Assess subject relevance</h3>
            <p>Designated subject {record.designated_subject_id}</p>
            <Field
              label="Official subject relevance finding"
              name="basis"
              required
            />
            <Evidence />
            <label>
              <input type="checkbox" required />I verified the syllabus and
              assessment against this specific subject.
            </label>
            <CommandError error={cmd.error} />
            <button disabled={cmd.isPending}>Record subject finding</button>
          </form>
        )}
      {!record.may_verify_certificate && !q.data?.finding && (
        <p>
          Certificate authentication requires a documented designation for this
          case.
        </p>
      )}
      {record.may_verify_certificate &&
        !asOf &&
        q.isSuccess &&
        !q.data.finding && (
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              const subject = f.get("subject");
              cmd.mutate({
                path,
                body: {
                  ...proof(f),
                  certificate_key: f.get("certificate"),
                  actual_exam_on: f.get("exam"),
                  actual_exam_at: timestamp(f, "exam_time"),
                  issued_on: f.get("issued"),
                  score_percent: Number(f.get("score")),
                  subject_id: subject ? record.designated_subject_id : null,
                  relevance_basis: subject ? f.get("basis") : null,
                  checked_person_offering_certificate: true,
                  verified_exam_and_score_sharing: true,
                },
              });
            }}
          >
            <h3>Verify archived result</h3>
            <Field
              label="Official certificate identifier"
              required
              name="certificate"
            />
            <Field
              label="Actual examination date"
              required
              type="date"
              name="exam"
            />
            <Field
              label="Exact examination time if documented"
              type="datetime-local"
              step="0.001"
              name="exam_time"
            />
            <Field
              label="Certificate issue date"
              required
              type="date"
              name="issued"
            />
            <Field
              label="Verified percentage"
              type="number"
              min={0}
              max={100}
              step="any"
              required
              name="score"
            />
            {record.designated_subject_id && (
              <>
                <label>
                  <input type="checkbox" name="subject" /> Assess relevance to
                  designated subject {record.designated_subject_id}
                </label>
                <Field
                  label="Official subject relevance finding"
                  name="basis"
                />
              </>
            )}
            <Evidence />
            <label>
              <input type="checkbox" required />I verified the certificate,
              person, offering, examination and actual score sharing against the
              official sources.
            </label>
            <CommandError error={cmd.error} />
            <button className="primary" disabled={cmd.isPending}>
              Record historical finding
            </button>
          </form>
        )}
    </section>
  );
}

export function OfficeAlerts() {
  const [params, set] = useSearchParams(),
    all = params.get("scope") === "all",
    offset = Number(params.get("offset")) || 0;
  const q = useQuery({
    queryKey: ["office-alerts", all, offset],
    queryFn: () =>
      api<{
        total: number;
        today: string;
        items: {
          application_id: string;
          department: string;
          offering: string;
          office: string;
          reviewer: string | null;
          deadline_status: string;
          task: string;
          original_enrollment_cutoff: string | null;
          enrollment_cutoff: string | null;
          exam_registration_cutoff: string | null;
        }[];
      }>("/review-office-alerts?vacant_only=" + !all + "&offset=" + offset),
  });
  return (
    <>
      <PageHeader
        title="Review offices and deadlines"
        description="Pending applications follow the current appointment. Published dates remain visible during a vacancy."
      />
      <section className="panel prose">
        <SelectField
          label="Review office coverage"
          value={all ? "all" : "vacant"}
          onChange={(e) => set({ scope: e.target.value })}
        >
          <option value="vacant">Vacant offices</option>
          <option value="all">All pending reviews</option>
        </SelectField>
        {q.isPending ? (
          <Loading />
        ) : q.error ? (
          <ErrorState error={q.error} retry={() => void q.refetch()} />
        ) : (
          <>
            <p>As of {q.data.today}</p>
            {!q.data.total && <p>No matching reviews.</p>}
            {q.data.items.map((x) => (
              <article key={x.application_id}>
                <h2>{x.offering}</h2>
                <p>
                  {x.department} · {x.office.replaceAll("_", " ")} ·{" "}
                  {x.reviewer || "Vacant"}
                </p>
                <Facts
                  values={{
                    review_task: x.task,
                    deadline_status: x.deadline_status,
                    original_enrollment_cutoff: x.original_enrollment_cutoff,
                    current_enrollment_cutoff: x.enrollment_cutoff,
                    exam_registration_cutoff: x.exam_registration_cutoff,
                  }}
                />
              </article>
            ))}
            <Pager
              total={q.data.total}
              offset={offset}
              limit={25}
              change={(next) =>
                set({ scope: all ? "all" : "vacant", offset: String(next) })
              }
            />
          </>
        )}
      </section>
    </>
  );
}
