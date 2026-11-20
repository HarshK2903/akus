import { Participation } from "./Participation";
import { useQuery } from "@tanstack/react-query";
import {
  Link,
  useNavigate,
  useOutletContext,
  useParams,
  useLocation,
  useSearchParams,
} from "react-router-dom";
import { type Identity } from "../../lib/api";
import { api } from "../../lib/api";
import {
  useCommand,
  useContextData,
  reasonFields,
  type ApplicationRecord,
  type Offering,
  type Movement,
} from "../../lib/academic";
import { instant } from "../../lib/people";
import { Badge, ErrorState, Loading, PageHeader } from "../../components/ui";
import { CommandError, Pager, ScrollTable } from "../../components/PeopleUi";
import { Field, SelectField, SourceFields } from "../../components/SourceUi";
import { Dates, History, SourceLink } from "./Shared";

export function Applications({
  review = false,
  reconciliation = false,
}: {
  review?: boolean;
  reconciliation?: boolean;
}) {
  const actor = useOutletContext<Identity>();
  const [params, setParams] = useSearchParams();
  const offset = Number(params.get("offset") || 0);
  const query = useQuery({
    queryKey: ["applications", review, reconciliation, offset],
    queryFn: () =>
      api<{ items: ApplicationRecord[]; total: number }>(
        `/applications?review=${review}&reconciliation=${reconciliation}&offset=${offset}`,
      ),
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorState error={query.error} retry={() => void query.refetch()} />
    );
  return (
    <>
      <PageHeader
        title={
          reconciliation
            ? "Quota transfer reconciliation"
            : review
              ? "Application review queue"
              : "NPTEL applications"
        }
        description={
          reconciliation
            ? "Counted source seats remain occupied until a lawful capacity-checked transfer succeeds. No guaranteed transfer priority."
            : review
              ? "Current office authority is checked again at each decision. Applicants cannot review their own applications."
              : "Drafts reserve no capacity. Successful submission holds exactly one seat in the approved annual topic pool."
        }
      />
      {actor.roles?.includes("DRC_HEAD") && (
        <p className="prose">
          Your own application will route directly to HoD.
        </p>
      )}
      <p className="academic-links">
        <Link to="/app/catalog">Discover courses</Link>
        <Link to="/app/applications">Applications</Link>
        <Link to="/hod/quota-transfers">Transfer and policy cases</Link>
      </p>
      <section className="panel">
        <ScrollTable label="Application records">
          <table>
            <thead>
              <tr>
                <th>Course and applicant</th>
                <th>Application / review</th>
                <th>Current charged pool</th>
                <th>Reconciliation</th>
              </tr>
            </thead>
            <tbody>
              {query.data.items.map((a) => (
                <tr key={a.id}>
                  <td>
                    <Link to={`/app/applications/${a.id}`}>{a.course}</Link>
                    <p>{a.applicant}</p>
                    {a.enrollment_deadline_passed && (
                      <Badge tone="warning">Enrollment cutoff passed</Badge>
                    )}
                    <small>{a.provider_id}</small>
                  </td>
                  <td>
                    <Badge>{a.state}</Badge>
                    <p>
                      {a.next_office?.replaceAll("_", " ") ||
                        "No pending review"}
                    </p>
                  </td>
                  <td>
                    {a.allocation ? (
                      <>
                        <Link to={`/hod/quotas/${a.allocation.pool.id}`}>
                          {a.allocation.pool.topic} ·{" "}
                          {a.allocation.pool.academic_year}
                        </Link>
                        <p>{a.allocation.state}</p>
                      </>
                    ) : (
                      "No seat reserved"
                    )}
                  </td>
                  <td>
                    {a.cases
                      .filter((c) => c.status === "OPEN")
                      .map((c) => (
                        <p key={c.id}>
                          {actor.roles?.some((r) =>
                            ["HOD", "PRINCIPAL"].includes(r),
                          ) ? (
                            <Link to={`/hod/quota-transfers/${c.id}`}>
                              {c.reason.replaceAll("_", " ")}
                            </Link>
                          ) : (
                            c.reason.replaceAll("_", " ")
                          )}
                        </p>
                      ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollTable>
        {!query.data.items.length && (
          <p className="empty-state">
            No matching applications in your current scope.
          </p>
        )}
      </section>
      <Pager
        total={query.data.total}
        offset={offset}
        limit={25}
        change={(n) => setParams({ offset: String(n) })}
      />
    </>
  );
}

function DraftNavigation({
  offering,
  draft,
}: {
  offering: string;
  draft?: string;
}) {
  const query = draft ? `draft=${draft}` : `offering=${offering}`;
  return (
    <nav className="academic-links" aria-label="Application steps">
      <Link to={`/app/applications/new/offering?${query}`}>1. Offering</Link>
      <Link to={`/app/applications/new/eligibility?${query}`}>
        2. Eligibility
      </Link>
      {draft && (
        <>
          <Link to={`/app/applications/new/evidence?${query}`}>
            3. Evidence
          </Link>
          <Link to={`/app/applications/new/review?${query}`}>
            4. Review and submit
          </Link>
        </>
      )}
    </nav>
  );
}

export function ApplicationDraft() {
  const [params] = useSearchParams();
  const draftId = params.get("draft");
  const step = useLocation().pathname.split("/").pop();
  const draftQuery = useQuery({
    queryKey: ["application-draft", draftId],
    queryFn: () => api<ApplicationRecord>(`/applications/${draftId}`),
    enabled: !!draftId,
  });
  const offeringId = draftQuery.data?.offering_id || params.get("offering");
  const navigate = useNavigate();
  const context = useContextData();
  const query = useQuery({
    queryKey: ["offering", offeringId],
    queryFn: () => api<Offering>(`/nptel/offerings/${offeringId}`),
    enabled: !!offeringId,
  });
  const save = useCommand((id) =>
    navigate(`/app/applications/new/evidence?draft=${id}`),
  );
  if (context.data && !context.data.can_apply)
    return (
      <>
        <PageHeader
          title="Applicant access unavailable"
          description="Only currently eligible Faculty and DRC Heads may originate applications."
        />
        <p role="alert">
          HoD and Principal offices are NPTEL-exempt. Oversight does not grant
          applicant authority.
        </p>
      </>
    );
  if (draftId && draftQuery.isPending) return <Loading />;
  if (draftQuery.error)
    return (
      <ErrorState
        error={draftQuery.error}
        retry={() => void draftQuery.refetch()}
      />
    );
  if (
    draftQuery.data &&
    (!draftQuery.data.own || draftQuery.data.state !== "DRAFT")
  )
    return (
      <>
        <PageHeader
          title="Draft editing unavailable"
          description="Submitted facts remain immutable."
        />
        <Link to={`/app/applications/${draftId}`}>View application</Link>
      </>
    );
  if (!offeringId)
    return (
      <>
        <PageHeader
          title="Choose an exact offering"
          description="Start from the catalog so the course and official run are identified correctly."
        />
        <Link to="/app/catalog">Open course catalog →</Link>
      </>
    );
  if (query.isPending || context.isPending) return <Loading />;
  if (query.error || context.error)
    return (
      <ErrorState
        error={query.error || context.error || new Error("Source unavailable")}
        retry={() => void query.refetch()}
      />
    );
  if (!query.data || !context.data) return null;
  const o = query.data;
  const saved = draftQuery.data;
  const navigation = (
    <DraftNavigation offering={o.id} draft={draftId || undefined} />
  );
  if (step === "review" && draftId)
    return (
      <>
        {navigation}
        <ApplicationDetail draftId={draftId} />
      </>
    );
  if (step === "evidence" && saved)
    return (
      <>
        <PageHeader
          title="Application evidence and chronology"
          description="Preserve official source references and distinguish assertions from independent findings."
        />
        {navigation}
        <section className="panel prose">
          <h2>Before valid submission</h2>
          <p>
            No external enrollment is expected before submission. Record any
            contrary evidence truthfully; it will block retrospective
            submission. Prior-result checks are separate from this offering's
            enrollment.
          </p>
          <p>
            Binary document upload is not available in this phase. Official
            archive references, checksums and observation times remain
            auditable.
          </p>
          <Link
            className="button primary"
            to={`/app/applications/new/review?draft=${saved.id}`}
          >
            Continue to review
          </Link>
        </section>
        <Participation app={saved} canVerify={false} />
      </>
    );
  if (step === "offering")
    return (
      <>
        <PageHeader
          title="Selected exact offering"
          description="The provider run and canonical course are distinct identities. Drafts reserve no capacity."
        />
        {navigation}
        <section className="panel prose">
          <h2>{o.metadata?.title || o.provider_id}</h2>
          {o.metadata && <Dates metadata={o.metadata} />}
          <Link to="/app/catalog">
            Choose a different offering as a new draft
          </Link>
          <p>
            <Link
              className="button primary"
              to={`/app/applications/new/eligibility?${draftId ? `draft=${draftId}` : `offering=${o.id}`}`}
            >
              Continue to eligibility
            </Link>
          </p>
        </section>
      </>
    );
  return (
    <>
      <PageHeader
        title="New application · eligibility declarations"
        description="Save a draft first, then inspect the submission snapshot. Unresolved evidence never creates a seat."
      />
      {navigation}
      <Link to={`/app/offerings/${o.id}`}>← Exact offering</Link>
      <section className="panel prose section-gap">
        <h2>{o.metadata?.title || o.provider_id}</h2>
        <SourceLink url={o.source_url} />
        {o.metadata && <Dates metadata={o.metadata} />}
      </section>
      {!context.data.can_apply ? (
        <p role="alert">
          Only currently eligible Faculty and DRC Heads can apply.
        </p>
      ) : (
        <section className="panel prose section-gap">
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              save.mutate({
                path: "/applications",
                body: {
                  offering_id: o.id,
                  ...(saved
                    ? { id: saved.id, expected_version: saved.version }
                    : {}),
                  declarations: {
                    academic_relevance: f.get("academic_relevance"),
                    score_sharing_yes: f.has("sharing"),
                    not_yet_enrolled: f.has("not_enrolled"),
                    prior_attempt: f.get("prior"),
                    emerging_technology_exception: f.has("exception"),
                    acknowledgement: f.has("acknowledge"),
                  },
                },
              });
            }}
          >
            <h2>Truthful declarations</h2>
            <label className="source-field">
              Academic relevance to your teaching or discipline
              <textarea
                name="academic_relevance"
                required
                maxLength={4000}
                defaultValue={saved?.declarations.academic_relevance || ""}
              />
            </label>
            <p>
              These are your declarations, not verified provider evidence. NPTEL
              enrollment must occur after valid AKUS submission. Unknown prior
              outcomes require HoD verification in the evidence workflow.
            </p>
            <label className="checkbox-label">
              <input
                name="sharing"
                type="checkbox"
                defaultChecked={saved?.declarations.score_sharing_yes}
              />{" "}
              I will select Yes for NPTEL score sharing.
            </label>
            <label className="checkbox-label">
              <input
                name="not_enrolled"
                type="checkbox"
                defaultChecked={saved?.declarations.not_yet_enrolled}
              />{" "}
              I have not already enrolled externally in this offering.
            </label>
            <SelectField
              label="Previous attempts at this canonical course"
              name="prior"
              defaultValue={
                saved?.declarations.prior_attempt || "OUTCOME_UNVERIFIED"
              }
            >
              <option value="OUTCOME_UNVERIFIED">
                Earlier result unknown / verification required
              </option>
              <option value="NONE_DECLARED">
                No previous attempt or certificate to declare
              </option>
              <option value="VALID_CERTIFICATE">
                I already hold a valid certificate
              </option>
            </SelectField>
            <label className="checkbox-label">
              <input
                name="exception"
                type="checkbox"
                defaultChecked={
                  saved?.declarations.emerging_technology_exception
                }
              />{" "}
              This application requires an emerging technology exception.
            </label>
            <label className="checkbox-label">
              <input
                name="acknowledge"
                type="checkbox"
                defaultChecked={saved?.declarations.acknowledgement}
              />{" "}
              I confirm these declarations and understand that evidence
              discrepancies require review.
            </label>
            <CommandError error={save.error} />
            <button className="primary" disabled={save.isPending}>
              Save draft for review
            </button>
          </form>
        </section>
      )}
    </>
  );
}

export function MovementTable({ items }: { items: Movement[] }) {
  return (
    <ScrollTable label="Immutable quota movements">
      <table>
        <thead>
          <tr>
            <th>Recorded</th>
            <th>Movement</th>
            <th>Pool / change</th>
            <th>Transaction</th>
          </tr>
        </thead>
        <tbody>
          {items.map((m) => (
            <tr key={m.id}>
              <td>{instant(m.recorded_at)}</td>
              <td>{m.kind}</td>
              <td>
                <Link to={`/hod/quotas/${m.pool_id}`}>
                  {m.pool_id.slice(0, 8)}
                </Link>{" "}
                · {m.delta > 0 ? "+" : ""}
                {m.delta}
              </td>
              <td className="wrap-anywhere">{m.movement_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {!items.length && <p className="empty-state">No allocation movements.</p>}
    </ScrollTable>
  );
}

export function ApplicationDetail({
  caseView = false,
  draftId,
}: {
  caseView?: boolean;
  draftId?: string;
}) {
  const { appId: routeAppId, caseId } = useParams();
  const appId = draftId || routeAppId;
  const navigate = useNavigate();
  const context = useContextData();
  const query = useQuery({
    queryKey: ["application", appId, caseId],
    queryFn: () =>
      api<ApplicationRecord>(
        caseView ? `/quota-transfer-cases/${caseId}` : `/applications/${appId}`,
      ),
  });
  const submit = useCommand((id) => navigate(`/app/applications/${id}`));
  const action = useCommand();
  const mapping = useCommand();
  const reportSchedule = useCommand();
  const verifySchedule = useCommand();
  if (query.isPending || context.isPending) return <Loading />;
  if (query.error || context.error)
    return (
      <ErrorState
        error={
          query.error || context.error || new Error("Application unavailable")
        }
        retry={() => void query.refetch()}
      />
    );
  if (!query.data || !context.data) return null;
  const a = query.data;
  const o = a.offering;
  return (
    <>
      <PageHeader
        title={caseView ? "Quota transfer case" : a.course}
        description={`${a.course} · ${a.applicant} · ${a.provider_id} · version ${a.version}`}
      />
      <p className="academic-links">
        {caseView && <Link to="/hod/quota-transfers">← Transfer cases</Link>}
        <Link to="/app/applications">← Applications</Link>
        <Link to={`/app/applications/${a.id}/quota`}>Quota history</Link>
        <Link to={`/app/applications/${a.id}/history`}>Audit timeline</Link>
      </p>
      <div className="overview-grid">
        <section className="panel prose">
          <h2>Application status</h2>
          <p>{a.declarations?.academic_relevance}</p>
          <Badge>{a.state}</Badge>
          <p>
            {a.next_office
              ? `Next review: ${a.next_office.replaceAll("_", " ")}`
              : "No pending review"}
          </p>
          <p>
            Submitted:{" "}
            {a.submitted_at ? instant(a.submitted_at) : "Not submitted"}
          </p>
          {!a.source_eligible &&
            ["UNDER_REVIEW", "APPROVED"].includes(a.state) && (
              <p role="alert">
                Applicant source records changed. Academic consequences require
                controlled review; counted capacity remains protected.
              </p>
            )}
          <p>
            {a.actual_exam && a.actual_exam !== "NOT_VERIFIED" ? (
              <>
                Verified actual examination · <strong>{a.actual_exam}</strong>
              </>
            ) : (
              <>
                Actual examination and certificate:{" "}
                <strong>not verified</strong>.
              </>
            )}{" "}
            {a.annual_compliance && a.annual_compliance !== "NOT_ASSESSED"
              ? "Annual recognition · " +
                a.annual_compliance.replaceAll("_", " ")
              : "Annual compliance is not assessed from a scheduled exam date."}
          </p>
        </section>
        <section className="panel prose">
          <h2>Annual quota facts</h2>
          <dl className="detail-grid">
            <div>
              <dt>Original submission year</dt>
              <dd>{a.submission?.facts.academic_year || "No submission"}</dd>
            </div>
            <div>
              <dt>Currently charged year</dt>
              <dd>
                {a.allocation?.pool.academic_year || "No counted allocation"}
              </dd>
            </div>
            <div>
              <dt>Latest official scheduled exam year</dt>
              <dd>{o?.expected_exam_year || "Not configured"}</dd>
            </div>
            <div>
              <dt>Allocation status</dt>
              <dd>{a.allocation?.state || "NONE"}</dd>
            </div>
          </dl>
          {a.allocation && (
            <>
              <p>
                {a.allocation.pool.topic} · {a.allocation.pool.occupied} /{" "}
                {a.allocation.pool.maximum} counted
              </p>
              <Link to={`/hod/quotas/${a.allocation.pool.id}`}>
                Inspect current pool →
              </Link>
            </>
          )}
        </section>
      </div>
      {a.cases
        .filter((c) => (caseView ? c.id === caseId : c.status === "OPEN"))
        .map((c) => (
          <section className="panel prose section-gap" key={c.id}>
            <h2>{c.kind.replaceAll("_", " ")}</h2>
            <p>
              {c.status} · Updated {instant(c.updated_at)}
            </p>
            <Badge tone="warning">{c.reason.replaceAll("_", " ")}</Badge>
            <p>
              {c.status === "OPEN"
                ? "The existing counted seat remains in its current pool. No target-year seat or policy exception has been granted."
                : "This case is resolved. The current allocation and immutable movement history below show the recorded outcome."}
            </p>
            {c.status === "OPEN" && c.kind === "QUOTA_TRANSFER" && (
              <p>
                <Link
                  to={
                    c.context.target_pool_id
                      ? `/hod/quotas/${String(c.context.target_pool_id)}`
                      : "/hod/quotas/new"
                  }
                >
                  Inspect or configure target annual quota →
                </Link>
              </p>
            )}
            <dl>
              {Object.entries(c.context).map(([k, v]) => (
                <div key={k}>
                  <dt>{k.replaceAll("_", " ")}</dt>
                  <dd className="wrap-anywhere">
                    {String(v ?? "Not configured")}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      {a.state === "DRAFT" && a.own && (
        <section className="panel prose section-gap">
          <h2>Review and submit</h2>
          <p>
            Submission validates current eligibility, source freshness, the
            effective mapping and published capacity in one transaction. It
            records your current declarations permanently.
          </p>
          <dl>
            {Object.entries(a.declarations).map(([k, v]) => (
              <div key={k}>
                <dt>{k.replaceAll("_", " ")}</dt>
                <dd>{String(v)}</dd>
              </div>
            ))}
          </dl>
          <Link to={`/app/applications/new/eligibility?draft=${a.id}`}>
            Edit this saved draft
          </Link>
          {o?.blockers.map((b) => (
            <p key={b} role="status">
              {b.replaceAll("_", " ")}
            </p>
          ))}
          {o && !o.mapping_revision_id && (
            <>
              <button
                onClick={() =>
                  mapping.mutate({
                    path: "/nptel/mapping-requests",
                    body: {
                      offering_id: o.id,
                      source_reference: `Application draft ${a.id}`,
                      reason:
                        "Request academic primary topic mapping for this draft",
                    },
                  })
                }
                disabled={mapping.isPending}
              >
                Request HoD mapping
              </button>
              <CommandError error={mapping.error} />
              {mapping.isSuccess && (
                <p role="status">Mapping request recorded. No seat reserved.</p>
              )}
            </>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit.mutate({
                path: `/applications/${a.id}/submit`,
                body: {
                  expected_version: a.version,
                  snapshot_id: o?.snapshot_id,
                  mapping_revision_id: o?.mapping_revision_id,
                },
              });
            }}
          >
            <label className="checkbox-label">
              <input type="checkbox" required /> I confirm these source facts
              and declarations for submission.
            </label>
            <CommandError error={submit.error} />
            <button
              className="primary section-gap"
              disabled={submit.isPending || !o?.snapshot_id}
            >
              Submit application and reserve one seat
            </button>
          </form>
        </section>
      )}
      {a.enrollment_deadline_passed && (
        <p className="panel prose">
          Enrollment cutoff passed. The seat stays held. Final approval requires
          a verified enrollment or a current official extension.
        </p>
      )}
      {a.can_review && (
        <section className="panel prose section-gap">
          <h2>Current office decision</h2>
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              action.mutate({
                path: `/applications/${a.id}/review`,
                body: {
                  expected_version: a.version,
                  decision: f.get("decision"),
                  ...(f.get("decision") === "APPROVE" && f.has("extension")
                    ? {
                        enrollment_extension: {
                          valid_through: f.get("valid_through"),
                          document_digest: f.get("extension_digest"),
                          observed_at: f.get("extension_observed")
                            ? new Date(
                                String(f.get("extension_observed")),
                              ).toISOString()
                            : null,
                          independently_checked: true,
                        },
                      }
                    : {}),
                  ...reasonFields(f),
                },
              });
            }}
          >
            <SelectField label="Decision" name="decision">
              <option value="APPROVE">
                Approve at my current review stage
              </option>
              <option value="REJECT">
                Reject and release the current seat
              </option>
            </SelectField>
            {a.enrollment_deadline_passed &&
              a.next_office === "HOD" &&
              !a.participation?.verified_submission_first && (
                <fieldset>
                  <legend>Official enrollment extension</legend>
                  <label className="checkbox-label">
                    <input type="checkbox" name="extension" />I verified a
                    current official extension for this person and offering.
                  </label>
                  <Field
                    name="valid_through"
                    label="Extension valid through"
                    type="date"
                  />
                  <Field
                    name="extension_observed"
                    label="Extension evidence observed at (local time)"
                    type="datetime-local"
                    step="1"
                  />
                  <Field
                    name="extension_digest"
                    label="Extension document SHA-256"
                    pattern="[a-f0-9]{64}"
                  />
                </fieldset>
              )}
            <SourceFields />
            <label className="checkbox-label">
              <input type="checkbox" required /> I confirm this decision and its
              recorded rationale.
            </label>
            <CommandError error={action.error} />
            <button className="primary" disabled={action.isPending}>
              Record review decision
            </button>
          </form>
        </section>
      )}
      {a.own && ["UNDER_REVIEW", "APPROVED"].includes(a.state) && (
        <section className="panel prose section-gap">
          <h2>Voluntary withdrawal</h2>
          <p>
            Before commencement and enrollment, a valid withdrawal releases the
            current pool. After commencement the seat remains counted. Earlier
            external enrollment requires verified HoD review; this form cannot
            grant that exception.
          </p>
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              action.mutate({
                path: `/applications/${a.id}/withdraw`,
                body: {
                  expected_version: a.version,
                  not_enrolled_declaration: f.has("not_enrolled"),
                  ...reasonFields(f),
                },
              });
            }}
          >
            <label className="checkbox-label">
              <input type="checkbox" name="not_enrolled" /> I have not enrolled
              externally in this offering.
            </label>
            <SourceFields />
            <label className="checkbox-label">
              <input type="checkbox" required /> I confirm this withdrawal
              request.
            </label>
            <CommandError error={action.error} />
            <button disabled={action.isPending}>Withdraw application</button>
          </form>
        </section>
      )}
      {context.data.hod_departments.includes(a.department_id) &&
        a.cases.some((c) => c.status === "OPEN") && (
          <section className="panel prose section-gap">
            <h2>Reassess verified schedule</h2>
            <p>
              Rechecks the latest accepted schedule and target capacity without
              overriding policy or releasing the source seat on failure.
            </p>
            <form
              className="source-form"
              onSubmit={(e) => {
                e.preventDefault();
                action.mutate({
                  path: `/applications/${a.id}/reconcile`,
                  body: reasonFields(new FormData(e.currentTarget)),
                });
              }}
            >
              <SourceFields />
              <CommandError error={action.error} />
              <button className="primary" disabled={action.isPending}>
                Recheck transfer
              </button>
            </form>
          </section>
        )}
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Quota movement ledger</h2>
        </div>
        <MovementTable items={a.ledger} />
      </section>
      <section className="panel prose section-gap">
        <h2>Original submitted snapshot</h2>
        {a.submission ? (
          <>
            <p>
              Immutable source: {a.submission.facts.trust}. Route:{" "}
              {a.submission.facts.route.join(" → ")}
            </p>
            <Dates metadata={a.submission.facts.metadata} />
          </>
        ) : (
          <p>No immutable submission exists for this draft.</p>
        )}
      </section>
      {a.own && ["UNDER_REVIEW", "APPROVED"].includes(a.state) && (
        <section className="panel prose section-gap">
          <h2>Report a person-specific scheduled exam date</h2>
          <p>
            A hall-ticket assertion is not verified evidence. Your current
            department HoD must authenticate the official document for your
            exact identity and offering. This creates a review case and
            preserves your currently counted seat.
          </p>
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              reportSchedule.mutate({
                path: `/applications/${a.id}/schedule-claims`,
                body: {
                  scheduled_exam_on: f.get("scheduled_exam_on"),
                  source_reference: f.get("hall_reference"),
                  reason: f.get("hall_reason"),
                },
              });
            }}
          >
            <Field
              label="Claimed person-specific exam date"
              name="scheduled_exam_on"
              type="date"
              required
            />
            <Field
              label="Hall-ticket source identifier"
              name="hall_reference"
              required
              minLength={3}
            />
            <Field
              label="Reason for person-specific schedule review"
              name="hall_reason"
              required
              minLength={5}
            />
            <CommandError error={reportSchedule.error} />
            <button disabled={reportSchedule.isPending}>
              Record unverified schedule claim
            </button>
            {reportSchedule.isSuccess && (
              <p role="status">
                Recorded as unverified. No quota transfer or exam participation
                has been verified.
              </p>
            )}
          </form>
        </section>
      )}
      {a.personal_schedule && (
        <section className="panel prose section-gap">
          <h2>Verified person-specific scheduled exam</h2>
          <p>
            {a.personal_schedule.scheduled_exam_on} · revision{" "}
            {a.personal_schedule.version} · verified{" "}
            {instant(a.personal_schedule.verified_at)}
          </p>
          <p>{a.personal_schedule.source_reference}</p>
          <p className="muted wrap-anywhere">
            Document SHA-256: {a.personal_schedule.document_digest}
          </p>
          <p>
            This HoD-authenticated scheduled date applies only to this applicant
            and offering. It does not verify exam attendance or a certificate.
          </p>
        </section>
      )}
      {context.data.hod_departments.includes(a.department_id) &&
        !a.own &&
        ["UNDER_REVIEW", "APPROVED"].includes(a.state) && (
          <section className="panel prose section-gap">
            <h2>Authenticate personal hall-ticket schedule</h2>
            <p>
              Independently check the official document against {a.applicant}{" "}
              and exact offering {a.provider_id}. Record its archived source
              reference and SHA-256 digest. A confirmed date triggers
              capacity-checked reconciliation only for this application.
            </p>
            <form
              className="source-form"
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                verifySchedule.mutate({
                  path: `/applications/${a.id}/verify-schedule`,
                  body: {
                    expected_version: a.personal_schedule?.version || 0,
                    scheduled_exam_on: f.get("verified_date"),
                    source_reference: f.get("verified_reference"),
                    document_digest: f.get("digest"),
                    observed_at: new Date(
                      String(f.get("observed_at")),
                    ).toISOString(),
                    reason: f.get("verification_reason"),
                    authenticated_official_person_and_offering: true,
                  },
                });
              }}
            >
              <Field
                type="date"
                label="Authenticated personal exam date"
                name="verified_date"
                required
              />
              <Field
                label="Official archived hall-ticket reference"
                name="verified_reference"
                required
                minLength={3}
              />
              <Field
                label="Official document SHA-256 digest"
                name="digest"
                pattern="[a-f0-9]{64}"
                required
              />
              <Field
                type="datetime-local"
                label="When you observed the official evidence (local time)"
                name="observed_at"
                required
              />
              <Field
                label="Hall-ticket verification rationale"
                name="verification_reason"
                required
                minLength={5}
              />
              <label className="checkbox-label">
                <input type="checkbox" required /> I authenticated the official
                document, exact applicant, offering and scheduled date
                independently.
              </label>
              <CommandError error={verifySchedule.error} />
              <button className="primary" disabled={verifySchedule.isPending}>
                Confirm personal schedule
              </button>
              {verifySchedule.isSuccess && (
                <p role="status">
                  Manual HoD verification recorded. Inspect the current
                  allocation and any remaining transfer case.
                </p>
              )}
            </form>
          </section>
        )}
      {a.own && a.state === "DRAFT" && (
        <p>
          <Link to={`/app/applications/new/eligibility?draft=${a.id}`}>
            Edit and resume saved draft
          </Link>
        </p>
      )}
      {a.own && ["REJECTED", "WITHDRAWN"].includes(a.state) && (
        <section className="panel prose section-gap">
          <h2>New independent application</h2>
          <p>
            The closed record will remain unchanged. A fresh application must
            pass current enrollment, commencement, quota and canonical-course
            checks.
          </p>
          <Link
            to={`/app/applications/new/eligibility?offering=${a.offering_id}`}
          >
            Start a new application for this offering
          </Link>
        </section>
      )}
      {a.state !== "DRAFT" && (
        <p>
          <Link to={"/app/certificates/" + a.id}>
            Exam and certificate dossier
          </Link>
        </p>
      )}
      <Participation
        app={a}
        canVerify={
          !a.own && context.data.hod_departments.includes(a.department_id)
        }
      />
      {!!a.draft_revisions?.length && (
        <section className="panel prose section-gap">
          <h2>Saved draft history</h2>
          {a.draft_revisions.map((r) => (
            <details key={r.version}>
              <summary>
                Revision {r.version} · {instant(r.recorded_at)}
              </summary>
              <p>
                {String(
                  r.declarations.academic_relevance ||
                    "Academic relevance not recorded",
                )}
              </p>
            </details>
          ))}
        </section>
      )}
      <History events={a.history} />
      <section className="panel prose section-gap">
        <h2>In-app notifications</h2>
        {a.notifications.length ? (
          a.notifications.map((n, i) => (
            <p key={i}>
              {n.kind.replaceAll("_", " ")} · {instant(n.created_at)}
            </p>
          ))
        ) : (
          <p>No notification events.</p>
        )}
        <p className="muted">
          Durable in-app events; email delivery is not configured.
        </p>
      </section>
    </>
  );
}
