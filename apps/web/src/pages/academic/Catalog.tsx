import { useQuery } from "@tanstack/react-query";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { api } from "../../lib/api";
import {
  useCommand,
  useContextData,
  useDepartment,
  reasonFields,
  type Course,
  type Offering,
} from "../../lib/academic";
import { Badge, ErrorState, Loading, PageHeader } from "../../components/ui";
import { CommandError, Pager, ScrollTable } from "../../components/PeopleUi";
import { Field, SelectField, SourceFields } from "../../components/SourceUi";
import {
  AcademicLinks,
  Dates,
  DepartmentChoice,
  History,
  SourceLink,
} from "./Shared";
import { instant } from "../../lib/people";

export function Catalog() {
  const [params, setParams] = useSearchParams();
  const context = useContextData();
  const offset = Math.max(0, Number(params.get("offset")) || 0);
  const q = params.get("q") || "";
  const query = useQuery({
    queryKey: ["catalog", params.toString()],
    queryFn: () =>
      api<{ items: Course[]; total: number }>(
        `/nptel/courses?q=${encodeURIComponent(q)}&category=${encodeURIComponent(params.get("category") || "")}&offset=${offset}`,
      ),
  });
  return (
    <>
      <PageHeader
        title="NPTEL course catalog"
        description="Canonical courses and their exact offerings, with visible provider provenance."
        action={
          context.data?.can_source && (
            <Link className="button primary" to="/admin/catalog/new">
              Record canonical course
            </Link>
          )
        }
      />
      <AcademicLinks />
      <div className="filter-bar">
        <Field
          label="Search courses"
          value={q}
          onChange={(e) => setParams({ q: e.target.value })}
        />
        <Field
          label="Exact provider category"
          value={params.get("category") || ""}
          onChange={(e) => setParams({ q, category: e.target.value })}
        />
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <section className="panel">
          <ScrollTable label="NPTEL course catalog">
            <table>
              <thead>
                <tr>
                  <th>Canonical course</th>
                  <th>Exact offerings</th>
                  <th>Provider categories</th>
                  <th>Source status</th>
                </tr>
              </thead>
              <tbody>
                {query.data?.items.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <Link to={`/app/catalog/${c.id}`}>{c.title}</Link>
                      <p className="muted">{c.code}</p>
                    </td>
                    <td>{c.offerings.length} runs</td>
                    <td>
                      {[
                        ...new Set(
                          c.offerings.flatMap(
                            (o) => o.metadata?.categories || [],
                          ),
                        ),
                      ].join(" · ") || "No source yet"}
                    </td>
                    <td>
                      {c.offerings.some(
                        (o) => o.fresh && o.source_status === "CURRENT",
                      ) ? (
                        <Badge>Current observation</Badge>
                      ) : (
                        <Badge tone="warning">Source review needed</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollTable>
          {!query.data?.items.length && (
            <p className="empty-state">
              No matching canonical courses. An authorized source steward can
              record a course and fetch its exact provider offering.
            </p>
          )}
          <Pager
            limit={25}
            offset={offset}
            total={query.data?.total || 0}
            change={(next) => setParams({ q, offset: String(next) })}
          />
        </section>
      )}
    </>
  );
}

export function ProviderSources({ versions = false }: { versions?: boolean }) {
  const context = useContextData();
  const [params, setParams] = useSearchParams();
  const q = params.get("q") || "";
  const offset = Math.max(0, Number(params.get("offset")) || 0);
  const navigate = useNavigate();
  const query = useQuery({
    queryKey: ["provider-sources", q, offset],
    queryFn: () =>
      api<{ items: Course[]; total: number }>(
        `/nptel/courses?q=${encodeURIComponent(q)}&offset=${offset}`,
      ),
    enabled: !!context.data?.can_source,
  });
  const fetch = useCommand((id) => navigate(`/app/offerings/${id}`));
  if (context.isPending) return <Loading />;
  if (context.error)
    return (
      <ErrorState error={context.error} retry={() => void context.refetch()} />
    );
  if (!context.data?.can_source)
    return (
      <section className="panel prose">
        <h1>Source administration unavailable</h1>
        <p>A current Admin grant is required to maintain provider sources.</p>
        <Link to="/app/catalog">Open course catalog</Link>
      </section>
    );
  return (
    <>
      <PageHeader
        title={
          versions
            ? "Provider metadata versions"
            : "NPTEL provider synchronization"
        }
        description="Public academic metadata only. Manual fetches preserve observations; accepting a source never proves personal enrollment or a certificate."
      />
      <p className="academic-links">
        <Link to="/admin/nptel-sync">Fetch official source</Link>
        <Link to="/admin/nptel-offerings">Metadata versions</Link>
        <Link to="/admin/catalog/new">Record canonical course</Link>
      </p>
      <Field
        label="Search source courses"
        value={q}
        onChange={(e) => setParams({ q: e.target.value })}
      />
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          {!versions && (
            <section className="panel prose section-gap">
              <h2>Fetch or retry an exact offering</h2>
              <p>
                Use the canonical course and provider ID together. A failed
                fetch is recorded with its reason; retry here after checking the
                provider. Inspect the resulting source before acceptance.
              </p>
              <form
                className="source-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  const f = new FormData(e.currentTarget);
                  fetch.mutate({
                    path: "/admin/nptel/provider-fetches",
                    body: {
                      course_id: f.get("course_id"),
                      provider_id: f.get("provider_id"),
                      ...reasonFields(f),
                    },
                  });
                }}
              >
                <SelectField
                  label="Canonical source course"
                  name="course_id"
                  required
                >
                  <option value="">
                    Select a course from these search results
                  </option>
                  {query.data?.items.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.title} · {c.code}
                    </option>
                  ))}
                </SelectField>
                <Field
                  label="Exact provider offering ID"
                  name="provider_id"
                  placeholder="noc26_cs98"
                  pattern="noc[0-9]{2}_[a-z0-9]{2,30}"
                  required
                />
                <SourceFields />
                <label className="checkbox-label">
                  <input type="checkbox" required /> I checked the canonical
                  course and exact offering identity.
                </label>
                <CommandError error={fetch.error} />
                <button className="primary" disabled={fetch.isPending}>
                  {fetch.isPending
                    ? "Fetching official source…"
                    : "Fetch provider metadata"}
                </button>
              </form>
            </section>
          )}
          <section className="panel section-gap">
            <h2>Source records</h2>
            <ScrollTable label="Provider source records">
              <table>
                <thead>
                  <tr>
                    <th>Canonical course / offering</th>
                    <th>Scheduled exam and categories</th>
                    <th>Accepted observation</th>
                    <th>Source status</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data?.items.flatMap((c) =>
                    c.offerings.length
                      ? c.offerings.map((o) => (
                          <tr key={o.id}>
                            <td>
                              <Link to={`/app/offerings/${o.id}`}>
                                {o.provider_id}
                              </Link>
                              <p>
                                <Link to={`/app/catalog/${c.id}`}>
                                  {c.title}
                                </Link>
                              </p>
                            </td>
                            <td>
                              {o.metadata?.scheduled_exam_on || "Not accepted"}
                              <p>
                                {o.metadata?.categories.join(" · ") ||
                                  "No accepted categories"}
                              </p>
                            </td>
                            <td>
                              {o.observed_at
                                ? instant(o.observed_at)
                                : "No accepted observation"}
                              <p>
                                {o.trust || "Unverified"} ·{" "}
                                {o.fresh ? "Fresh" : "Stale or absent"}
                              </p>
                            </td>
                            <td>
                              <Badge
                                tone={
                                  o.source_status === "CURRENT" && o.fresh
                                    ? "neutral"
                                    : "warning"
                                }
                              >
                                {o.source_status.replaceAll("_", " ")}
                              </Badge>
                            </td>
                          </tr>
                        ))
                      : [
                          <tr key={c.id}>
                            <td>
                              <Link to={`/app/catalog/${c.id}`}>{c.title}</Link>
                            </td>
                            <td colSpan={3}>
                              No provider observation. Fetch its exact offering
                              after confirming the identity.
                            </td>
                          </tr>,
                        ],
                  )}
                </tbody>
              </table>
            </ScrollTable>
            {!query.data?.items.length && (
              <p className="empty-state">
                No matching courses. Record a canonical course before fetching
                an offering.
              </p>
            )}
            <Pager
              total={query.data?.total || 0}
              offset={offset}
              limit={25}
              change={(next) => setParams({ q, offset: String(next) })}
            />
          </section>
        </>
      )}
    </>
  );
}

export function CourseForm() {
  const context = useContextData();
  const navigate = useNavigate();
  const save = useCommand((id) => navigate(`/app/catalog/${id}`));
  if (context.isPending) return <Loading />;
  if (!context.data?.can_source)
    return (
      <ErrorState
        error={new Error("Current Admin source authority is required.")}
        retry={() => void context.refetch()}
      />
    );
  return (
    <>
      <PageHeader
        title="Record canonical course"
        description="Use an approved stable course identity. Similar titles never establish equivalence."
      />
      <Link to="/app/catalog">← Course catalog</Link>
      <section className="panel prose section-gap">
        <form
          className="source-form"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            save.mutate({
              path: "/admin/nptel/courses",
              body: {
                code: f.get("code"),
                title: f.get("title"),
                description: f.get("description"),
                ...reasonFields(f),
              },
            });
          }}
        >
          <Field label="Stable canonical course code" name="code" required />
          <Field label="Course title" name="title" required minLength={3} />
          <Field label="Plain-text course description" name="description" />
          <SourceFields />
          <CommandError error={save.error} />
          <button className="primary" disabled={save.isPending}>
            Save canonical course
          </button>
        </form>
      </section>
    </>
  );
}

export function CourseDetail() {
  const { courseId } = useParams();
  const context = useContextData();
  const scope = useDepartment(context.data);
  const navigate = useNavigate();
  const query = useQuery({
    queryKey: ["course", courseId, scope.department],
    queryFn: () =>
      api<Course>(
        `/nptel/courses/${courseId}?department_id=${scope.department}`,
      ),
    enabled: !!scope.department,
  });
  const fetch = useCommand((id) => navigate(`/app/offerings/${id}`));
  if (query.isPending || context.isPending) return <Loading />;
  if (query.error || context.error)
    return (
      <ErrorState
        error={query.error || context.error || new Error("Source unavailable")}
        retry={() => void query.refetch()}
      />
    );
  if (!query.data || !context.data) return null;
  const c = query.data;
  return (
    <>
      <PageHeader
        title={c.title}
        description={`Canonical identity ${c.code} · ${c.id}`}
      />
      <Link to="/app/catalog">← Course catalog</Link>
      <DepartmentChoice
        context={context.data}
        value={scope.department}
        change={scope.choose}
      />
      <section className="panel prose section-gap">
        <h2>Course identity</h2>
        <p>{c.description || "No description recorded."}</p>
        <p className="muted">Source: {c.source_reference}</p>
        <Link to={`/hod/topic-mappings/${c.id}?department=${scope.department}`}>
          Department primary-topic decision →
        </Link>
      </section>
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Exact offerings</h2>
        </div>
        <ScrollTable label="Exact course offerings">
          <table>
            <thead>
              <tr>
                <th>Provider run</th>
                <th>Duration</th>
                <th>Scheduled exam</th>
                <th>Charging topic</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {c.offerings.map((o) => (
                <tr key={o.id}>
                  <td>
                    <Link
                      to={`/app/offerings/${o.id}?department=${scope.department}`}
                    >
                      {o.provider_id}
                    </Link>
                  </td>
                  <td>{o.metadata?.duration_weeks ?? "Unknown"} weeks</td>
                  <td>
                    {o.metadata?.scheduled_exam_on || "Unknown"}
                    <p className="muted">
                      {o.expected_exam_year || "Year not configured"}
                    </p>
                  </td>
                  <td>{o.topic || "HoD mapping required"}</td>
                  <td>
                    {o.trust || "Not checked"} ·{" "}
                    {o.fresh ? "Current" : "Stale or absent"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollTable>
        {!c.offerings.length && (
          <p className="empty-state">
            No offering recorded. Course browsing reserves no capacity.
          </p>
        )}
      </section>
      {context.data.can_source && (
        <section className="panel prose section-gap">
          <h2>Fetch official NPTEL offering</h2>
          <p>
            This fetch reads public metadata only. Review its dates and
            canonical association before accepting the observation.
          </p>
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              fetch.mutate({
                path: "/admin/nptel/provider-fetches",
                body: {
                  course_id: c.id,
                  provider_id: f.get("provider_id"),
                  ...reasonFields(f),
                },
              });
            }}
          >
            <Field
              label="Exact provider offering ID"
              name="provider_id"
              placeholder="noc26_cs98"
              required
              pattern="noc[0-9]{2}_[a-z0-9]{2,30}"
            />
            <SourceFields />
            <CommandError error={fetch.error} />
            <button className="primary" disabled={fetch.isPending}>
              {fetch.isPending
                ? "Fetching official source…"
                : "Fetch provider metadata"}
            </button>
          </form>
        </section>
      )}
      <History events={c.history} />
    </>
  );
}

export function OfferingDetail() {
  const { offeringId } = useParams();
  const context = useContextData();
  const scope = useDepartment(context.data);
  const query = useQuery({
    queryKey: ["offering", offeringId, scope.department],
    queryFn: () =>
      api<Offering>(
        `/nptel/offerings/${offeringId}?department_id=${scope.department}`,
      ),
    enabled: !!scope.department,
  });
  const accept = useCommand();
  const intake = useCommand();
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
  return (
    <>
      <PageHeader
        title={o.metadata?.title || o.course?.title || o.provider_id}
        description={`Exact offering ${o.provider_id}`}
        action={
          <Badge
            tone={
              o.fresh && o.source_status === "CURRENT" ? "neutral" : "warning"
            }
          >
            {o.trust || o.source_status}
          </Badge>
        }
      />
      <Link to={`/app/catalog/${o.course_id}`}>
        ← Canonical course and runs
      </Link>
      <DepartmentChoice
        context={context.data}
        value={scope.department}
        change={scope.choose}
      />
      <div className="overview-grid section-gap">
        <section className="panel prose">
          <h2>Provider dates and categories</h2>
          {o.metadata ? (
            <Dates metadata={o.metadata} />
          ) : (
            <p>No accepted provider observation. Submission remains blocked.</p>
          )}
          <SourceLink url={o.source_url} />
          <p className="muted">
            Observed {o.observed_at ? instant(o.observed_at) : "not yet"} ·{" "}
            {o.source_status}
          </p>
        </section>
        <section className="panel prose">
          <h2>Department charging decision</h2>
          <dl>
            <dt>HoD-approved primary topic</dt>
            <dd>{o.topic || "Awaiting HoD mapping"}</dd>
            <dt>Scheduled-exam quota year</dt>
            <dd>{o.expected_exam_year || "Unknown / unconfigured"}</dd>
            <dt>Published shared capacity</dt>
            <dd>
              {o.quota
                ? `${o.quota.occupied} counted / ${o.quota.maximum} · ${o.quota.status}`
                : "No pool published"}
            </dd>
          </dl>
          {o.quota && (
            <Link to={`/hod/quotas/${o.quota.id}`}>View annual pool →</Link>
          )}
          <ul>
            {o.blockers.map((b) => (
              <li key={b}>{b.replaceAll("_", " ").toLowerCase()}</li>
            ))}
          </ul>
          <p>
            Categories are source evidence. Applicants cannot choose a different
            topic to obtain a seat.
          </p>
          {context.data.can_apply && (
            <>
              <Link
                className="button"
                to={`/app/applications/new/eligibility?offering=${o.id}`}
              >
                Application admission
              </Link>
              {!o.topic && o.snapshot_id && (
                <button
                  onClick={() =>
                    intake.mutate({
                      path: "/nptel/mapping-requests",
                      body: {
                        offering_id: o.id,
                        source_reference: o.source_url || "LOCAL_DEMO",
                        reason:
                          "Applicant requests an evidence-based department HoD mapping",
                      },
                    })
                  }
                  disabled={intake.isPending}
                >
                  Request HoD topic mapping
                </button>
              )}
              <CommandError error={intake.error} />
              {intake.isSuccess && (
                <p role="status">Mapping request recorded. No seat reserved.</p>
              )}
            </>
          )}
        </section>
      </div>
      {!!o.fetches?.length && (
        <section className="panel prose section-gap">
          <h2>Provider checks</h2>
          {o.fetches.map((f, i) => (
            <p key={i}>
              {instant(f.observed_at)} · {f.status}
              {f.error ? ` · ${f.error.replaceAll("_", " ")}` : ""}
            </p>
          ))}
        </section>
      )}
      {context.data.can_source && !!o.observations?.length && (
        <section className="panel prose section-gap">
          <h2>Review source observation</h2>
          <p>
            Confirm the exact offering belongs to this canonical course and that
            the observed official source is applicable. Acceptance records
            metadata; it does not verify personal participation.
          </p>
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              accept.mutate({
                path: `/admin/nptel/offerings/${o.id}/accept`,
                body: {
                  snapshot_id: f.get("snapshot_id"),
                  expected_version: o.version,
                  ...reasonFields(f),
                },
              });
            }}
          >
            <SelectField
              label="Observed source version"
              name="snapshot_id"
              required
            >
              {o.observations.map((s) => (
                <option key={s.id} value={s.id}>
                  {instant(s.observed_at)} · scheduled exam{" "}
                  {s.metadata.scheduled_exam_on || "unknown"} · {s.trust}
                </option>
              ))}
            </SelectField>
            {o.observations.map((s) => (
              <details key={s.id}>
                <summary>
                  {s.id === o.snapshot_id
                    ? "Current accepted observation"
                    : "Inspect observation"}{" "}
                  · {s.metadata.scheduled_exam_on || "unknown exam"}
                </summary>
                <Dates metadata={s.metadata} />
                <SourceLink url={s.source_url} />
                <p className="wrap-anywhere muted">Digest {s.digest}</p>
              </details>
            ))}
            <SourceFields />
            <label className="checkbox-label">
              <input type="checkbox" required /> I checked the exact course
              identity and official source applicability.
            </label>
            <CommandError error={accept.error} />
            <button className="primary" disabled={accept.isPending}>
              Accept source observation
            </button>
            {accept.isSuccess && (
              <p role="status">
                Source observation accepted and history recorded.
              </p>
            )}
          </form>
        </section>
      )}
      <History events={o.history} />
    </>
  );
}
