import { MovementTable } from "./Applications";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../lib/api";
import {
  useCommand,
  useContextData,
  useDepartment,
  reasonFields,
  type Mapping,
  type Pool,
  type Topic,
} from "../../lib/academic";
import { Badge, ErrorState, Loading, PageHeader } from "../../components/ui";
import { CommandError, ScrollTable } from "../../components/PeopleUi";
import { Field, SelectField, SourceFields } from "../../components/SourceUi";
import { AcademicLinks, DepartmentChoice, History, SourceLink } from "./Shared";
import { instant } from "../../lib/people";

type Proposal = {
  id: string;
  label: string;
  department_id: string;
  source_reference: string;
  reason: string;
  status: string;
  topic_id: string | null;
};
export function Topics() {
  const context = useContextData();
  const { topicId } = useParams();
  const [kind, setKind] = useState("topic");
  const query = useQuery({
    queryKey: ["nptel-topics"],
    queryFn: () => api<{ items: Topic[] }>("/nptel/topics"),
  });
  const proposals = useQuery({
    queryKey: ["topic-proposals"],
    queryFn: () => api<{ items: Proposal[] }>("/nptel/topic-proposals"),
  });
  const save = useCommand();
  const resolve = useCommand();
  if (query.isPending || context.isPending) return <Loading />;
  if (query.error || context.error)
    return (
      <ErrorState
        error={query.error || context.error || new Error("Source unavailable")}
        retry={() => void query.refetch()}
      />
    );
  if (!query.data || !context.data) return null;
  const selected = query.data.items.find((t) => t.id === topicId);
  return (
    <>
      <PageHeader
        title={selected ? selected.name : "Canonical charging topics"}
        description="Provider category aliases and canonical topics are source references. Department HoD mapping is a separate academic decision."
      />
      <AcademicLinks />
      <section className="panel">
        <ScrollTable label="Canonical topics">
          <table>
            <thead>
              <tr>
                <th>Canonical topic</th>
                <th>Provider aliases</th>
                <th>Version</th>
              </tr>
            </thead>
            <tbody>
              {query.data.items
                .filter((t) => !topicId || t.id === topicId)
                .map((t) => (
                  <tr key={t.id}>
                    <td>
                      <Link to={`/hod/topics/${t.id}`}>{t.name}</Link>
                      <p className="muted">{t.code}</p>
                    </td>
                    <td>
                      {t.aliases.map((a) => a.label).join(" · ") ||
                        "No aliases"}
                    </td>
                    <td>{t.version}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </ScrollTable>
        {!query.data.items.length && (
          <p className="empty-state">
            No canonical topics. Source administration can create a documented
            topic; applicants can propose one without reserving capacity.
          </p>
        )}
      </section>
      <section className="panel prose section-gap">
        <h2>
          {context.data.can_source
            ? "Maintain topic references"
            : "Propose a topic for source review"}
        </h2>
        {context.data.can_source && (
          <SelectField
            label="Reference action"
            value={kind}
            onChange={(e) => setKind(e.target.value)}
          >
            <option value="topic">Create canonical topic</option>
            <option value="alias">Record provider category alias</option>
          </SelectField>
        )}
        {(context.data.can_source ||
          context.data.can_apply ||
          context.data.hod_departments.length > 0) && (
          <form
            className="source-form"
            key={kind}
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              save.mutate({
                path: context.data!.can_source
                  ? kind === "topic"
                    ? "/admin/nptel/topics"
                    : "/admin/nptel/topic-aliases"
                  : "/nptel/topic-proposals",
                body: {
                  ...reasonFields(f),
                  ...(context.data!.can_source
                    ? kind === "topic"
                      ? { code: f.get("code"), name: f.get("name") }
                      : { topic_id: f.get("topic_id"), label: f.get("label") }
                    : { label: f.get("label") }),
                },
              });
            }}
          >
            {context.data.can_source && kind === "topic" ? (
              <>
                <Field
                  label="Stable topic code"
                  name="code"
                  required
                  pattern="[A-Z0-9][A-Z0-9_-]{1,39}"
                />
                <Field
                  label="Canonical topic name"
                  name="name"
                  required
                  minLength={2}
                />
              </>
            ) : (
              <>
                {context.data.can_source && (
                  <SelectField label="Canonical topic" name="topic_id" required>
                    <option value="">Select topic</option>
                    {query.data.items.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </SelectField>
                )}
                <Field
                  label="Provider category label"
                  name="label"
                  required
                  minLength={2}
                />
              </>
            )}
            <SourceFields />
            <CommandError error={save.error} />
            <button className="primary" disabled={save.isPending}>
              {context.data.can_source
                ? "Save topic reference"
                : "Submit topic proposal"}
            </button>
            {save.isSuccess && (
              <p role="status">
                Source request recorded. This does not approve a charging
                mapping or publish quota.
              </p>
            )}
          </form>
        )}
      </section>
      <section className="panel prose section-gap">
        <h2>Topic proposals</h2>
        {proposals.error ? (
          <ErrorState
            error={proposals.error}
            retry={() => void proposals.refetch()}
          />
        ) : !proposals.data?.items.length ? (
          <p>No proposals in your current scope.</p>
        ) : (
          proposals.data.items.map((p) => (
            <article className="section-gap" key={p.id}>
              <h3>{p.label}</h3>
              <Badge>{p.status}</Badge>
              <p>{p.reason}</p>
              <p className="muted">{p.source_reference}</p>
              {context.data!.can_source && !p.topic_id && (
                <form
                  className="source-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const f = new FormData(e.currentTarget);
                    resolve.mutate({
                      path: `/admin/nptel/topic-proposals/${p.id}/resolve`,
                      body: { topic_id: f.get("topic_id"), ...reasonFields(f) },
                    });
                  }}
                >
                  <SelectField
                    label={`Canonical reference for ${p.label}`}
                    name="topic_id"
                    required
                  >
                    <option value="">Choose documented reference</option>
                    {query.data!.items.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </SelectField>
                  <SourceFields />
                  <button disabled={resolve.isPending}>
                    Link proposal to canonical reference
                  </button>
                </form>
              )}
            </article>
          ))
        )}
        <CommandError error={resolve.error} />
      </section>
      {selected && <History events={selected.history} />}
    </>
  );
}

type MappingRow = {
  id: string;
  code: string;
  title: string;
  topic: string | null;
  mapping_version: number;
  status: string;
  pending_requests: number;
};
export function MappingList({ requests = false }: { requests?: boolean }) {
  const context = useContextData();
  const scope = useDepartment(context.data);
  const query = useQuery({
    queryKey: ["mappings", scope.department],
    queryFn: () =>
      api<{ items: MappingRow[] }>(
        `/departments/${scope.department}/topic-mappings`,
      ),
    enabled: !!scope.department,
  });
  if (context.isPending) return <Loading />;
  if (context.error)
    return (
      <ErrorState error={context.error} retry={() => void context.refetch()} />
    );
  if (!context.data) return null;
  const q = scope.params.get("q") || "";
  const items =
    query.data?.items.filter(
      (r) =>
        (!requests || r.pending_requests > 0) &&
        `${r.title} ${r.code}`.toLowerCase().includes(q.toLowerCase()),
    ) || [];
  return (
    <>
      <PageHeader
        title={
          requests
            ? "Primary-topic mapping requests"
            : "Department primary-topic mappings"
        }
        description="One current HoD-approved charging topic per canonical course, reused across its offerings."
      />
      <AcademicLinks />
      <div className="filter-bar">
        <DepartmentChoice
          context={context.data}
          value={scope.department}
          change={scope.choose}
        />
        <Field
          label="Search mapping courses"
          value={q}
          onChange={(e) =>
            scope.setParams({ department: scope.department, q: e.target.value })
          }
        />
      </div>
      <p>
        <Link
          to={`${requests ? "/hod/topic-mappings" : "/hod/topic-mappings/requests"}?department=${scope.department}`}
        >
          {requests ? "All mappings" : "Open mapping request inbox"} →
        </Link>
      </p>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <section className="panel">
          <ScrollTable label="Department course mappings">
            <table>
              <thead>
                <tr>
                  <th>Canonical course</th>
                  <th>Approved charging topic</th>
                  <th>Status</th>
                  <th>Revision</th>
                </tr>
              </thead>
              <tbody>
                {items.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <Link
                        to={`/hod/topic-mappings/${r.id}?department=${scope.department}`}
                      >
                        {r.title}
                      </Link>
                      <p className="muted">{r.code}</p>
                    </td>
                    <td>{r.topic || "No approved topic"}</td>
                    <td>
                      <Badge
                        tone={r.status === "APPROVED" ? "neutral" : "warning"}
                      >
                        {r.status.replaceAll("_", " ")}
                      </Badge>
                    </td>
                    <td>{r.mapping_version}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollTable>
          {!items.length && (
            <p className="empty-state">
              No matching mapping records. A faculty mapping request never
              creates a submitted application or a seat.
            </p>
          )}
        </section>
      )}
    </>
  );
}

export function MappingDetail({ editing = false }: { editing?: boolean }) {
  const { courseId } = useParams();
  const context = useContextData();
  const scope = useDepartment(context.data);
  const navigate = useNavigate();
  const [selectedSnapshot, setSelectedSnapshot] = useState("");
  const query = useQuery({
    queryKey: ["mapping", scope.department, courseId],
    queryFn: () =>
      api<Mapping>(
        `/departments/${scope.department}/topic-mappings/${courseId}`,
      ),
    enabled: !!scope.department,
  });
  const save = useCommand(() =>
    navigate(`/hod/topic-mappings/${courseId}?department=${scope.department}`),
  );
  if (query.isPending || context.isPending) return <Loading />;
  if (query.error || context.error)
    return (
      <ErrorState
        error={query.error || context.error || new Error("Mapping unavailable")}
        retry={() => void query.refetch()}
      />
    );
  if (!query.data || !context.data) return null;
  const m = query.data;
  const canWrite = context.data.hod_departments.includes(scope.department);
  const chosen =
    m.candidates.find((c) => c.snapshot_id === selectedSnapshot) ||
    m.candidates[0];
  return (
    <>
      <PageHeader
        title={editing ? "Approve or revise primary topic" : m.course.title}
        description={`Department course mapping · revision ${m.version}`}
        action={
          !editing &&
          canWrite && (
            <Link
              className="button primary"
              to={`/hod/topic-mappings/${courseId}/edit?department=${scope.department}`}
            >
              Approve or revise mapping
            </Link>
          )
        }
      />
      <Link to={`/hod/topic-mappings?department=${scope.department}`}>
        ← Department mappings
      </Link>
      <DepartmentChoice
        context={context.data}
        value={scope.department}
        change={scope.choose}
      />
      <div className="overview-grid section-gap">
        <section className="panel prose">
          <h2>Current charging decision</h2>
          <p>{m.revisions[0]?.topic || "No approved mapping"}</p>
          <p>{m.course.description}</p>
          <Link to={`/app/catalog/${courseId}?department=${scope.department}`}>
            Inspect exact offerings and provider metadata →
          </Link>
        </section>
        <section className="panel prose">
          <h2>Existing reservation impact</h2>
          <Badge tone="warning">Policy pending · P-NEW-11</Badge>
          <p>
            A new decision applies to subsequent admissions. Existing
            reservations must not silently move across topics; their eventual
            treatment requires institutional policy.
          </p>
        </section>
      </div>
      {editing && (
        <section className="panel prose section-gap">
          <h2>Academic mapping decision</h2>
          {!canWrite ? (
            <p role="alert">
              Only the current HoD or acting HoD for this department may decide.
              Principal oversight and Admin source access do not grant this
              authority.
            </p>
          ) : !chosen ? (
            <p>
              Accept an official offering source first. No categories may be
              invented.
            </p>
          ) : (
            <form
              className="source-form"
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                save.mutate({
                  path: `/departments/${scope.department}/topic-mappings/${courseId}`,
                  body: {
                    topic_id: f.get("topic_id"),
                    snapshot_id: chosen.snapshot_id,
                    expected_version: m.version,
                    ...reasonFields(f),
                  },
                });
              }}
            >
              <SelectField
                label="Decision source offering"
                value={chosen.snapshot_id}
                onChange={(e) => setSelectedSnapshot(e.target.value)}
              >
                {m.candidates.map((c) => (
                  <option key={c.snapshot_id} value={c.snapshot_id}>
                    {c.provider_id} · {instant(c.observed_at)}
                  </option>
                ))}
              </SelectField>
              <p>
                All observed provider categories:{" "}
                {chosen.categories.join(" · ")}
              </p>
              <SourceLink url={chosen.source_url} />
              <SelectField
                key={chosen.snapshot_id}
                label="One primary charging topic"
                name="topic_id"
                required
              >
                <option value="">Select an academically justified topic</option>
                {context.data.topics
                  .filter((t) => chosen.topic_ids.includes(t.id))
                  .map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
              </SelectField>
              {!chosen.topic_ids.length && (
                <p role="alert">
                  No canonical topic matches the observed categories. Request
                  source alias review; do not select an unrelated topic.
                </p>
              )}
              <SourceFields />
              <p>
                Effective at the actual decision time. Prior revisions and
                original submitted snapshots remain immutable.
              </p>
              <label className="checkbox-label">
                <input type="checkbox" required /> I confirm this topic on
                academic grounds and understand the existing-seat policy is
                pending.
              </label>
              <CommandError error={save.error} />
              <button
                className="primary"
                disabled={save.isPending || !chosen.topic_ids.length}
              >
                Confirm primary topic
              </button>
            </form>
          )}
        </section>
      )}
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Effective mapping revisions</h2>
        </div>
        <ScrollTable label="Primary-topic revision history">
          <table>
            <thead>
              <tr>
                <th>Revision</th>
                <th>Topic</th>
                <th>Effective interval</th>
                <th>Rationale and source</th>
              </tr>
            </thead>
            <tbody>
              {m.revisions.map((r) => (
                <tr key={r.id}>
                  <td>{r.version}</td>
                  <td>{r.topic}</td>
                  <td>
                    {instant(r.valid_from)} →{" "}
                    {r.valid_until ? instant(r.valid_until) : "Current"}
                  </td>
                  <td>
                    {r.reason}
                    <p className="muted">{r.source_reference}</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollTable>
        {!m.revisions.length && (
          <p className="empty-state">No approved decision.</p>
        )}
      </section>
      <History events={m.history} />
    </>
  );
}

export function QuotaList() {
  const context = useContextData();
  const scope = useDepartment(context.data);
  const year = scope.params.get("year") || "";
  const query = useQuery({
    queryKey: ["quotas", scope.department, year],
    queryFn: () =>
      api<{ items: Pool[] }>(
        `/departments/${scope.department}/quotas${year ? `?academic_year_id=${year}` : ""}`,
      ),
    enabled: !!scope.department,
  });
  if (context.isPending) return <Loading />;
  if (context.error)
    return (
      <ErrorState error={context.error} retry={() => void context.refetch()} />
    );
  if (!context.data) return null;
  return (
    <>
      <PageHeader
        title="Annual shared topic quotas"
        description="Each department, canonical topic and July–June year has its own published cap. Courses share this capacity."
        action={
          context.data.hod_departments.includes(scope.department) && (
            <Link
              className="button primary"
              to={`/hod/quotas/new?department=${scope.department}`}
            >
              Configure annual quota
            </Link>
          )
        }
      />
      <AcademicLinks />
      <div className="filter-bar">
        <DepartmentChoice
          context={context.data}
          value={scope.department}
          change={scope.choose}
        />
        <SelectField
          label="Academic year filter"
          value={year}
          onChange={(e) =>
            scope.setParams({
              department: scope.department,
              ...(e.target.value ? { year: e.target.value } : {}),
            })
          }
        >
          <option value="">All configured years</option>
          {context.data.years.map((y) => (
            <option key={y.id} value={y.id}>
              {y.label}
            </option>
          ))}
        </SelectField>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <section className="panel">
          <ScrollTable label="Annual shared topic quota pools">
            <table>
              <thead>
                <tr>
                  <th>Canonical topic / year</th>
                  <th>Publication</th>
                  <th>Maximum</th>
                  <th>Counted</th>
                  <th>Available internally</th>
                </tr>
              </thead>
              <tbody>
                {query.data?.items.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <Link to={`/hod/quotas/${p.id}`}>
                        {p.topic} · {p.academic_year}
                      </Link>
                    </td>
                    <td>
                      <Badge
                        tone={p.status === "DRAFT" ? "warning" : "neutral"}
                      >
                        {p.status}
                      </Badge>
                    </td>
                    <td>{p.maximum}</td>
                    <td>{p.occupied}</td>
                    <td>{p.available ?? "Unpublished"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollTable>
          {!query.data?.items.length && (
            <p className="empty-state">
              No quota pool configured for this scope. There is no default
              capacity and no annual rollover publication.
            </p>
          )}
        </section>
      )}
      <p className="muted">
        An internal vacancy does not establish external NPTEL enrollment
        availability.
      </p>
    </>
  );
}

export function QuotaDetail({
  editing = false,
  ledger = false,
  creating = false,
}: {
  editing?: boolean;
  ledger?: boolean;
  creating?: boolean;
}) {
  const { poolId } = useParams();
  const context = useContextData();
  const scope = useDepartment(context.data);
  const navigate = useNavigate();
  const query = useQuery({
    queryKey: ["quota", poolId, scope.params.get("as_of")],
    queryFn: () =>
      api<Pool>(
        `/quotas/${poolId}?` +
          new URLSearchParams(
            scope.params.get("as_of")
              ? { as_of: scope.params.get("as_of")! }
              : {},
          ),
      ),
    enabled: !!poolId,
  });
  const save = useCommand((id) => navigate(`/hod/quotas/${id}`));
  if (context.isPending || (!creating && query.isPending)) return <Loading />;
  if (context.error || (!creating && query.error))
    return (
      <ErrorState
        error={context.error || query.error || new Error("Quota unavailable")}
        retry={() => void query.refetch()}
      />
    );
  if (!context.data || (!creating && !query.data)) return null;
  const p = query.data;
  const department = p?.department_id || scope.department;
  const canWrite = context.data.hod_departments.includes(department);
  return (
    <>
      <PageHeader
        title={
          creating
            ? "Configure annual topic quota"
            : editing
              ? "Publish or revise annual quota"
              : ledger
                ? "Quota allocation ledger"
                : `${p?.topic} · ${p?.academic_year}`
        }
        description="Current department HoD authority, exact annual pool, explicit capacity and immutable decision history."
        action={
          !editing &&
          !creating &&
          canWrite && (
            <Link className="button primary" to={`/hod/quotas/${poolId}/edit`}>
              Publish or revise quota
            </Link>
          )
        }
      />
      <Link to={`/hod/quotas?department=${department}`}>
        ← Annual quota pools
      </Link>
      {p && (
        <section className="panel prose section-gap">
          <h2>
            {p.status} · {p.occupied} counted / {p.maximum} maximum
          </h2>
          <p>
            Available internally: {p.available ?? "Not published"}. Revision{" "}
            {p.version}. Counted occupancy includes held, confirmed and retained
            seats across every course charged to this pool.
          </p>
          <Link to={`/hod/quotas/${p.id}/ledger`}>
            Open immutable allocation ledger →
          </Link>
        </section>
      )}
      {(creating || editing) && (
        <section className="panel prose section-gap">
          <h2>Quota decision</h2>
          {!canWrite ? (
            <p role="alert">
              Current HoD authority for this department is required.
            </p>
          ) : (
            <form
              className="source-form"
              key={p?.version || "new"}
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                save.mutate({
                  path: `/departments/${department}/quotas`,
                  body: {
                    topic_id: p?.topic_id || f.get("topic_id"),
                    academic_year_id:
                      p?.academic_year_id || f.get("academic_year_id"),
                    maximum: Number(f.get("maximum")),
                    publish: f.get("publish") === "on",
                    expected_version: p?.version || 0,
                    ...reasonFields(f),
                  },
                });
              }}
            >
              {creating && (
                <>
                  <SelectField
                    label="Canonical charging topic"
                    name="topic_id"
                    required
                  >
                    <option value="">Select topic</option>
                    {context.data.topics.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </SelectField>
                  <SelectField
                    label="Quota academic year"
                    name="academic_year_id"
                    required
                  >
                    <option value="">Select July–June year</option>
                    {context.data.years.map((y) => (
                      <option key={y.id} value={y.id}>
                        {y.label}
                      </option>
                    ))}
                  </SelectField>
                </>
              )}
              <Field
                label="Maximum shared seats"
                name="maximum"
                type="number"
                min={p?.occupied || 0}
                max={2147483647}
                step="1"
                required
                defaultValue={p?.maximum}
              />
              <p>
                New maximum must remain at least {p?.occupied || 0} counted
                seats. The server checks again under a transaction lock.
              </p>
              <label className="checkbox-label">
                <input
                  name="publish"
                  type="checkbox"
                  defaultChecked={p?.status === "PUBLISHED"}
                />{" "}
                Publish this annual cap now
              </label>
              <SourceFields />
              <CommandError error={save.error} />
              <button className="primary" disabled={save.isPending}>
                Save quota decision
              </button>
            </form>
          )}
        </section>
      )}
      {!creating && !editing && (
        <section className="panel prose section-gap">
          <h2>
            {ledger ? "Allocation movement history" : "Counted allocations"}
          </h2>
          <p>
            {p?.occupied
              ? `${p.occupied} counted allocations.`
              : "No seats have been reserved in this pool."}
          </p>
          <p className="muted">
            Only successful valid submission can create a held seat. Creating or
            publishing this pool never reserves capacity.
          </p>
        </section>
      )}
      {p && (
        <section className="panel section-gap">
          <div className="panel-header">
            <h2>Count and ledger reconciliation</h2>
          </div>
          <p className="prose">
            Stored: {p.reconciliation?.stored_count} · Counted allocations:{" "}
            {p.reconciliation?.counted_allocations} · Ledger balance:{" "}
            {p.reconciliation?.ledger_balance}.{" "}
            {p.reconciliation?.as_of
              ? "Stored and allocation counts are current."
              : p.reconciliation?.matches_current
                ? "Counts reconcile."
                : "Review required."}
          </p>
          <ScrollTable label="Pool allocations">
            <table>
              <thead>
                <tr>
                  <th>Application</th>
                  <th>Workflow</th>
                  <th>Allocation</th>
                </tr>
              </thead>
              <tbody>
                {p.allocations?.map((a) => (
                  <tr key={a.application_id}>
                    <td>
                      <Link to={`/app/applications/${a.application_id}`}>
                        {a.applicant}
                      </Link>
                    </td>
                    <td>{a.state}</td>
                    <td>{a.allocation_state}</td>
                  </tr>
                ))}
                {!p.allocations?.length && (
                  <tr>
                    <td colSpan={3}>
                      No allocation records in your current scope.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </ScrollTable>
          {ledger && (
            <form
              className="source-form"
              onSubmit={(e) => {
                e.preventDefault();
                const value = new FormData(e.currentTarget).get("cutoff");
                scope.setParams((prev) => {
                  const next = new URLSearchParams(prev);
                  if (value)
                    next.set("as_of", new Date(String(value)).toISOString());
                  else next.delete("as_of");
                  return next;
                });
              }}
            >
              <label>
                Movements recorded through (local time)
                <input type="datetime-local" name="cutoff" />
              </label>
              <button>Filter movements</button>
            </form>
          )}
          {p.reconciliation?.as_of && (
            <p>
              Ledger balance at {instant(p.reconciliation.as_of)} ·{" "}
              {p.reconciliation.ledger_balance}
            </p>
          )}
          <MovementTable items={p.ledger || []} />
          <p className="prose muted">
            {p.visibility === "OWN_ALLOCATIONS_ONLY"
              ? "Only your allocation records are shown; totals cover the pool."
              : "Department records visible under your current authority."}{" "}
            Latest 200 records.
          </p>
        </section>
      )}
      <History events={p?.history} />
    </>
  );
}
