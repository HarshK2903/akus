import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Link,
  useNavigate,
  useOutletContext,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { api, type Identity } from "../lib/api";
import { accessKey, command, type StaffPage } from "../lib/people";
import type { References, StaffSources, Teaching } from "../lib/sources";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
import { CommandError, Pager, ScrollTable } from "../components/PeopleUi";
import {
  Field,
  NoAdmin,
  SelectField,
  SourceFields,
  SourceHistory,
} from "../components/SourceUi";
export function TeachingList() {
  const actor = useOutletContext<Identity>();
  const [params, setParams] = useSearchParams();
  const refs = useQuery({
    queryKey: ["references", accessKey(actor)],
    queryFn: () => api<References>("/sources/reference"),
  });
  const query = useQuery({
    queryKey: ["teaching", params.toString(), accessKey(actor)],
    queryFn: () =>
      api<{ items: Teaching[]; total: number; offset: number; limit: number }>(
        `/teaching?${params}`,
      ),
  });
  function filter(name: string, value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    next.delete("offset");
    setParams(next);
  }
  return (
    <>
      <PageHeader
        title="Teaching allocations"
        description="Official episode-scoped teaching facts. Corrections retain the original source history."
        action={
          actor.can_manage_people ? (
            <Link className="button primary" to="/admin/teaching/new">
              Record allocation
            </Link>
          ) : (
            <Badge>Read only</Badge>
          )
        }
      />
      <div className="policy-notice">
        <strong>POLICY_PENDING · IO-02</strong>
        <p>
          Whether imported teaching requires separate HoD confirmation is
          unratified. First teaching dates and provisional anniversaries are
          shown as source facts; no Silver credit or violation is asserted.
        </p>
      </div>
      <form className="filter-grid" onSubmit={(e) => e.preventDefault()}>
        <Field
          label="Faculty name filter"
          type="search"
          value={params.get("q") ?? ""}
          onChange={(e) => filter("q", e.target.value)}
        />
        <Field
          label="Exact academic term filter"
          value={params.get("term") ?? ""}
          onChange={(e) => filter("term", e.target.value)}
        />
        <SelectField
          label="Department filter"
          value={params.get("department_id") ?? ""}
          onChange={(e) => filter("department_id", e.target.value)}
        >
          <option value="">All permitted departments</option>
          {refs.data?.departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </SelectField>
        <SelectField
          label="Academic year filter"
          value={params.get("academic_year_id") ?? ""}
          onChange={(e) => filter("academic_year_id", e.target.value)}
        >
          <option value="">All years</option>
          {refs.data?.years.map((y) => (
            <option key={y.id} value={y.id}>
              {y.label}
            </option>
          ))}
        </SelectField>
        <SelectField
          label="Subject filter"
          value={params.get("subject_id") ?? ""}
          onChange={(e) => filter("subject_id", e.target.value)}
        >
          <option value="">All subjects</option>
          {refs.data?.subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </SelectField>
      </form>
      <section className="panel">
        {query.isPending ? (
          <Loading />
        ) : query.error ? (
          <ErrorState error={query.error} retry={() => void query.refetch()} />
        ) : (
          <>
            <ScrollTable label="Teaching allocations">
              <table>
                <thead>
                  <tr>
                    <th>Subject / staff</th>
                    <th>Department / term</th>
                    <th>Effective dates</th>
                    <th>First teaching in episode</th>
                    <th>Source state</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data?.items.map((t) => (
                    <tr key={t.id}>
                      <td>
                        <Link to={`/people/teaching/${t.id}`}>{t.subject}</Link>
                        <small className="cell-meta">{t.staff_name}</small>
                      </td>
                      <td>
                        {t.department}
                        <small className="cell-meta">
                          {t.academic_year} · {t.term}
                        </small>
                      </td>
                      <td>
                        {t.starts_on} → {t.ends_before}
                        <small className="cell-meta">End exclusive</small>
                      </td>
                      <td>{t.first_official_date ?? "No active source"}</td>
                      <td>
                        <Badge tone="warning">
                          {t.voided ? "Voided source" : "Acceptance pending"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </ScrollTable>
            {!query.data?.items.length && (
              <p className="empty-state">
                No official teaching records match these filters.
              </p>
            )}
            <Pager
              total={query.data?.total ?? 0}
              offset={query.data?.offset ?? 0}
              limit={25}
              change={(n) => {
                const next = new URLSearchParams(params);
                next.set("offset", String(n));
                setParams(next);
              }}
            />
          </>
        )}
      </section>
    </>
  );
}
export function TeachingDetail() {
  const actor = useOutletContext<Identity>();
  const { teachingId } = useParams();
  const query = useQuery({
    queryKey: ["teaching-record", teachingId, accessKey(actor)],
    queryFn: () => api<Teaching>(`/teaching/${teachingId}`),
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorState error={query.error} retry={() => void query.refetch()} />
    );
  const t = query.data;
  if (!t) return null;
  return (
    <>
      <PageHeader
        title={t.subject}
        description={`${t.staff_name} · ${t.external_key}`}
        action={
          actor.can_manage_people ? (
            <Link className="button" to={`/admin/teaching/${t.id}/correct`}>
              Correct source record
            </Link>
          ) : (
            <Badge>Read only</Badge>
          )
        }
      />
      <Link to="/people/teaching">← Teaching allocations</Link>
      <div className="overview-grid section-gap">
        <section className="panel prose">
          <h2>Official teaching record</h2>
          <dl className="profile-fields">
            <dt>Department</dt>
            <dd>{t.department}</dd>
            <dt>Term / academic year</dt>
            <dd>
              {t.term} · {t.academic_year}
            </dd>
            <dt>Effective interval</dt>
            <dd>
              {t.starts_on} → {t.ends_before} (exclusive)
            </dd>
            <dt>Source reference</dt>
            <dd>{t.source_reference}</dd>
            <dt>Source version</dt>
            <dd>{t.version}</dd>
            <dt>Record state</dt>
            <dd>{t.voided ? "Voided by source correction" : "Recorded"}</dd>
          </dl>
        </section>
        <section className="panel prose">
          <h2>Subject Silver source timeline</h2>
          <dl className="profile-fields">
            <dt>First official teaching in this episode</dt>
            <dd>{t.first_official_date ?? "No non-voided assignment"}</dd>
            <dt>Provisional two-year anniversary</dt>
            <dd>
              {t.provisional_deadline ??
                "Policy decision required / unavailable"}
            </dd>
            <dt>Acceptance</dt>
            <dd>POLICY_PENDING · IO-02</dd>
            <dt>Assessment</dt>
            <dd>
              {t.compliance === "NOT_ASSESSED"
                ? "Not assessed"
                : t.compliance.replaceAll("_", " ")}
            </dd>
            {t.status_at_separation && (
              <>
                <dt>Frozen at permanent separation</dt>
                <dd>{t.status_at_separation.replaceAll("_", " ")}</dd>
              </>
            )}
          </dl>
          <p>
            Repeated teaching within one employment episode preserves the
            earliest official date. A genuine rehire uses a new episode. Upload
            date never starts this clock.
          </p>
          {t.deadline_policy.includes("P-54") && (
            <p>February 29 anniversary handling is POLICY_PENDING · P-54.</p>
          )}
          {t.episode_closed && (
            <p>
              This employment episode is closed. No active monitoring or
              post-separation completion is inferred.
            </p>
          )}
        </section>
      </div>
      <SourceHistory history={t.history ?? []} />
    </>
  );
}
export function TeachingForm() {
  const actor = useOutletContext<Identity>();
  const { teachingId } = useParams();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const [search, setSearch] = useState("");
  const [personId, setPersonId] = useState("");
  const refs = useQuery({
    queryKey: ["references", accessKey(actor)],
    queryFn: () => api<References>("/sources/reference"),
    enabled: actor.can_manage_people,
  });
  const original = useQuery({
    queryKey: ["teaching-record", teachingId, accessKey(actor)],
    queryFn: () => api<Teaching>(`/teaching/${teachingId}`),
    enabled: !!teachingId && actor.can_manage_people,
  });
  const staff = useQuery({
    queryKey: ["staff-choice", search, accessKey(actor)],
    queryFn: () =>
      api<StaffPage>(`/people/staff?q=${encodeURIComponent(search)}&limit=25`),
    enabled: actor.can_manage_people && !teachingId,
  });
  const selectedPerson = original.data?.person_id ?? personId;
  const sources = useQuery({
    queryKey: ["staff-sources", selectedPerson, accessKey(actor)],
    queryFn: () => api<StaffSources>(`/people/staff/${selectedPerson}/sources`),
    enabled: !!selectedPerson && actor.can_manage_people,
  });
  const mutation = useMutation({
    mutationFn: (form: FormData) =>
      command(
        `/admin/teaching${teachingId ? `/${teachingId}` : ""}`,
        {
          external_key: form.get("external_key"),
          episode_id: form.get("episode_id"),
          subject_id: form.get("subject_id"),
          department_id: form.get("department_id"),
          academic_year_id: form.get("academic_year_id"),
          term: form.get("term"),
          starts_on: form.get("starts_on"),
          ends_before: form.get("ends_before"),
          source_reference: form.get("source_reference"),
          reason: form.get("reason"),
          voided: form.get("voided") === "on",
          expected_version: original.data?.version ?? null,
        },
        crypto.randomUUID(),
      ),
    onSuccess: (r) => {
      void cache.invalidateQueries();
      navigate(`/people/teaching/${r.id}`);
    },
  });
  if (!actor.can_manage_people) return <NoAdmin />;
  if (refs.isPending || (teachingId && original.isPending)) return <Loading />;
  if (refs.error || original.error)
    return (
      <ErrorState
        error={(refs.error ?? original.error)!}
        retry={() => {
          void refs.refetch();
          void original.refetch();
        }}
      />
    );
  if (selectedPerson && sources.isPending) return <Loading />;
  if (sources.error)
    return (
      <ErrorState error={sources.error} retry={() => void sources.refetch()} />
    );
  const t = original.data;
  return (
    <>
      <PageHeader
        title={
          teachingId ? "Correct teaching source" : "Record teaching allocation"
        }
        description="Record official facts with effective dates. This does not grant academic approval or compliance credit."
      />
      <section className="panel prose">
        {!teachingId && (
          <div className="filter-grid">
            <Field
              label="Find staff by name or key"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <SelectField
              label="Staff member"
              value={personId}
              onChange={(e) => setPersonId(e.target.value)}
            >
              <option value="">Select staff</option>
              {staff.data?.items.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.display_name} · {p.staff_key}
                </option>
              ))}
            </SelectField>
          </div>
        )}
        <form
          className="source-form"
          key={`${teachingId ?? selectedPerson}:${sources.data ? "ready" : "waiting"}`}
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate(new FormData(e.currentTarget));
          }}
        >
          <Field
            label="Official allocation key"
            name="external_key"
            required
            defaultValue={t?.external_key}
            readOnly={!!teachingId}
          />
          <SelectField
            label="Employment episode"
            name="episode_id"
            required
            defaultValue={t?.episode_id}
          >
            <option value="">Select faculty episode</option>
            {sources.data?.episodes
              .filter((e) => e.is_faculty === true)
              .map((e) => (
                <option
                  key={e.id}
                  value={e.id}
                  disabled={!!t && t.episode_id !== e.id}
                >
                  {String(e.starts_on)} →{" "}
                  {String(e.ends_before ?? "Open-ended")}
                </option>
              ))}
          </SelectField>
          <SelectField
            label="Canonical subject"
            name="subject_id"
            required
            defaultValue={t?.subject_id}
          >
            <option value="">Select subject</option>
            {refs.data?.subjects.map((s) => (
              <option key={s.id} value={s.id}>
                {s.code} · {s.name}
              </option>
            ))}
          </SelectField>
          <SelectField
            label="Teaching department"
            name="department_id"
            required
            defaultValue={t?.department_id}
          >
            <option value="">Select department</option>
            {refs.data?.departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </SelectField>
          <SelectField
            label="Official academic year"
            name="academic_year_id"
            required
            defaultValue={t?.academic_year_id}
          >
            <option value="">Select year</option>
            {refs.data?.years.map((y) => (
              <option key={y.id} value={y.id}>
                {y.label}
              </option>
            ))}
          </SelectField>
          <Field
            label="Academic term"
            name="term"
            required
            minLength={2}
            maxLength={60}
            defaultValue={t?.term}
          />
          <Field
            label="Teaching starts on"
            name="starts_on"
            type="date"
            required
            defaultValue={t?.starts_on}
          />
          <Field
            label="Teaching ends before (exclusive)"
            name="ends_before"
            type="date"
            required
            defaultValue={t?.ends_before}
          />
          {t && (
            <label className="checkbox-label">
              <input type="checkbox" name="voided" defaultChecked={t.voided} />
              Void a mistaken source record; preserve the evidence and
              correction history.
            </label>
          )}
          <SourceFields />
          <CommandError error={mutation.error} />
          <button
            className="primary"
            disabled={mutation.isPending || !sources.data}
          >
            Save teaching source
          </button>
        </form>
      </section>
    </>
  );
}
