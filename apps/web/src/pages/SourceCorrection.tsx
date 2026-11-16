import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Link,
  useOutletContext,
  useLocation,
  useParams,
} from "react-router-dom";
import { api, type Identity } from "../lib/api";
import { accessKey, command } from "../lib/people";
import type { References, SourceRecord, StaffSources } from "../lib/sources";
import { ErrorState, Loading, PageHeader } from "../components/ui";
import { CommandError } from "../components/PeopleUi";
import {
  Field,
  NoAdmin,
  SelectField,
  SourceFields,
  SourceHistory,
} from "../components/SourceUi";
function localInstant(value: unknown) {
  return typeof value === "string"
    ? new Date(new Date(value).getTime() + 330 * 60_000)
        .toISOString()
        .slice(0, 19)
    : "";
}
function iso(value: FormDataEntryValue | null) {
  return value ? new Date(`${String(value)}+05:30`).toISOString() : null;
}
export function SourceCorrection() {
  const actor = useOutletContext<Identity>();
  const { staffId } = useParams();
  const cache = useQueryClient();
  const location = useLocation();
  const [kind, setKind] = useState(
    location.pathname.endsWith("/employment") ? "employment" : "person",
  );
  const [recordId, setRecordId] = useState("");
  const [office, setOffice] = useState("");
  const [notice, setNotice] = useState("");
  const query = useQuery({
    queryKey: ["staff-sources", staffId, accessKey(actor)],
    refetchOnWindowFocus: false,
    queryFn: () => api<StaffSources>(`/people/staff/${staffId}/sources`),
    enabled: actor.can_manage_people,
  });
  const refs = useQuery({
    queryKey: ["references", accessKey(actor)],
    queryFn: () => api<References>("/sources/reference"),
    enabled: actor.can_manage_people,
  });
  const choices: SourceRecord[] = !query.data
    ? []
    : kind === "person"
      ? [query.data.person]
      : kind === "employment"
        ? query.data.episodes
        : kind === "department"
          ? query.data.memberships
          : kind === "email"
            ? query.data.emails
            : query.data.offices.filter((o) => !o.superseded);
  const selected =
    kind === "person"
      ? query.data?.person
      : choices.find((r) => r.id === recordId);
  const mutation = useMutation({
    mutationFn: (form: FormData) => {
      const values: Record<string, unknown> =
        kind === "person"
          ? {
              display_name: form.get("display_name"),
              enabled: form.get("enabled") === "on",
            }
          : kind === "email"
            ? {
                email: form.get("email"),
                valid_from: iso(form.get("valid_from")),
                valid_until: iso(form.get("valid_until")),
              }
            : kind === "office"
              ? {
                  office: form.get("office"),
                  department_id:
                    form.get("office") === "PRINCIPAL"
                      ? null
                      : form.get("department_id"),
                  valid_from: iso(form.get("valid_from")),
                  valid_until: iso(form.get("valid_until")),
                }
              : {
                  starts_on: form.get("starts_on"),
                  ends_before: form.get("ends_before") || null,
                  ...(kind === "employment"
                    ? { is_faculty: form.get("is_faculty") === "on" }
                    : {
                        episode_id: form.get("episode_id"),
                        department_id: form.get("department_id"),
                      }),
                };
      return command(
        `/admin/staff/${staffId}/sources`,
        {
          kind,
          id: selected?.id ?? null,
          expected_version:
            kind === "office" ? selected?.version : selected?.source_version,
          values,
          source_reference: form.get("source_reference"),
          reason: form.get("reason"),
        },
        crypto.randomUUID(),
      );
    },
    onSuccess: () => {
      setNotice(
        "Source change recorded. Original facts remain in the revision history.",
      );
      void cache.invalidateQueries();
    },
  });
  if (!actor.can_manage_people) return <NoAdmin />;
  if (query.isPending || refs.isPending) return <Loading />;
  if (query.error || refs.error)
    return (
      <ErrorState
        error={(query.error ?? refs.error)!}
        retry={() => {
          void query.refetch();
          void refs.refetch();
        }}
      />
    );
  const data = query.data;
  if (!data) return null;
  const label = (r: SourceRecord) =>
    kind === "email"
      ? `${r.email} · ${r.valid_from}`
      : kind === "office"
        ? `${r.office} · ${r.valid_from}`
        : `${r.starts_on} → ${r.ends_before ?? "Open-ended"}`;
  const currentOffice = office || String(selected?.office ?? "DRC_HEAD");
  return (
    <>
      <PageHeader
        title="Staff source management"
        description={`${data.person.display_name} · Authorized corrections preserve source history.`}
      />
      <div className="record-links">
        <Link to={`/admin/staff/${staffId}`}>← Staff record</Link>
        <Link
          className="button"
          to={`/admin/appointments/new?person=${staffId}`}
        >
          Record appointment
        </Link>
      </div>
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Employment episode register</h2>
        </div>
        <div
          className="table-wrap"
          role="region"
          aria-label="Employment episode register"
          tabIndex={0}
        >
          <table>
            <thead>
              <tr>
                <th>Start</th>
                <th>End before</th>
                <th>Classification</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {data.episodes.map((e) => (
                <tr key={e.id}>
                  <td>{String(e.starts_on)}</td>
                  <td>{String(e.ends_before ?? "Open-ended")}</td>
                  <td>{e.is_faculty ? "Faculty" : "Non-faculty"}</td>
                  <td>{String(e.source_reference)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {notice && (
        <p role="status" className="success-notice">
          {notice}
        </p>
      )}
      <div className="overview-grid section-gap">
        <section className="panel prose">
          <h2>Record or correct official facts</h2>
          <SelectField
            label="Source record type"
            value={kind}
            onChange={(e) => {
              setKind(e.target.value);
              setRecordId("");
              setOffice("");
              setNotice("");
            }}
          >
            <option value="person">Staff identity / access status</option>
            <option value="employment">Employment episode</option>
            <option value="department">Home department membership</option>
            <option value="email">Institutional email</option>
            <option value="office">Replace mistaken office appointment</option>
          </SelectField>
          {kind !== "person" && (
            <SelectField
              label="Existing record"
              value={recordId}
              onChange={(e) => {
                setRecordId(e.target.value);
                setOffice("");
              }}
            >
              <option value="">
                {kind === "office"
                  ? "Select appointment to replace"
                  : "Add a new official record"}
              </option>
              {choices.map((r) => (
                <option key={r.id} value={r.id}>
                  {label(r)}
                </option>
              ))}
            </SelectField>
          )}
          <form
            className="source-form"
            key={`${kind}:${recordId}:${selected?.source_version ?? 0}`}
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate(new FormData(e.currentTarget));
            }}
          >
            {kind === "person" ? (
              <>
                <Field
                  label="Official display name"
                  name="display_name"
                  defaultValue={String(selected?.display_name ?? "")}
                  required
                  minLength={2}
                />
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="enabled"
                    defaultChecked={selected?.enabled === true}
                  />
                  Institutional account access enabled
                </label>
              </>
            ) : kind === "email" ? (
              <>
                <Field
                  label="Institutional email address"
                  name="email"
                  type="email"
                  required
                  defaultValue={String(selected?.email ?? "")}
                />
                <Field
                  label="Email valid from (IST)"
                  name="valid_from"
                  type="datetime-local"
                  step="1"
                  required
                  defaultValue={localInstant(selected?.valid_from)}
                />
                <Field
                  label="Email valid until (IST, exclusive)"
                  name="valid_until"
                  type="datetime-local"
                  step="1"
                  defaultValue={localInstant(selected?.valid_until)}
                />
              </>
            ) : kind === "office" ? (
              <>
                <SelectField
                  label="Correct office"
                  name="office"
                  value={currentOffice}
                  onChange={(e) => setOffice(e.target.value)}
                >
                  <option value="DRC_HEAD">DRC Head</option>
                  <option value="HOD">HoD</option>
                  <option value="ACTING_HOD">Acting HoD</option>
                  <option value="PRINCIPAL">Principal</option>
                </SelectField>
                {currentOffice !== "PRINCIPAL" && (
                  <SelectField
                    label="Office department"
                    name="department_id"
                    required
                    defaultValue={String(selected?.department_id ?? "")}
                  >
                    <option value="">Select department</option>
                    {refs.data?.departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </SelectField>
                )}
                <Field
                  label="Office effective from (IST)"
                  name="valid_from"
                  type="datetime-local"
                  step="1"
                  required
                  defaultValue={localInstant(selected?.valid_from)}
                />
                <Field
                  label="Office effective until (IST, exclusive)"
                  name="valid_until"
                  type="datetime-local"
                  step="1"
                  defaultValue={localInstant(selected?.valid_until)}
                />
              </>
            ) : (
              <>
                {kind === "department" && (
                  <>
                    <SelectField
                      label="Employment episode"
                      name="episode_id"
                      required
                      defaultValue={String(selected?.episode_id ?? "")}
                    >
                      <option value="">Select episode</option>
                      {data.episodes.map((e) => (
                        <option key={e.id} value={e.id}>
                          {String(e.starts_on)} →{" "}
                          {String(e.ends_before ?? "Open-ended")}
                        </option>
                      ))}
                    </SelectField>
                    <SelectField
                      label="Home department"
                      name="department_id"
                      required
                      defaultValue={String(selected?.department_id ?? "")}
                    >
                      <option value="">Select department</option>
                      {refs.data?.departments.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name}
                        </option>
                      ))}
                    </SelectField>
                  </>
                )}
                <Field
                  label="Effective start date"
                  name="starts_on"
                  type="date"
                  required
                  defaultValue={String(selected?.starts_on ?? "")}
                />
                <Field
                  label="Effective end before (exclusive)"
                  name="ends_before"
                  type="date"
                  defaultValue={String(selected?.ends_before ?? "")}
                />
                {kind === "employment" && (
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="is_faculty"
                      defaultChecked={selected?.is_faculty === true}
                    />
                    Official faculty employment classification
                  </label>
                )}
              </>
            )}
            <SourceFields />
            <CommandError error={mutation.error} />
            <button
              className="primary"
              disabled={mutation.isPending || (kind === "office" && !selected)}
            >
              Save source change
            </button>
          </form>
        </section>
        <section className="panel prose">
          <h2>Effective dates and source history</h2>
          <p>
            A correction changes the current source projection and retains the
            original facts. An office replacement must pass employment, scope
            and HoD/DRC exclusion checks in the same transaction.
          </p>
          <p>
            Before shortening an employment episode, correct dependent teaching,
            membership and office intervals. Genuine rehire is a new episode; a
            source typo is a correction to the existing episode.
          </p>
          <p>
            Institutional email changes do not move a Google subject link. A
            verified replacement account requires explicit reconciliation.
          </p>
          <p>
            Academic exemptions, retrospective credit and application closures
            remain separate policy-governed workflows. Admin source corrections
            grant none of those outcomes.
          </p>
          {data.identity_links.length > 0 && (
            <>
              <h3>Google link references</h3>
              <ul>
                {data.identity_links.map((l) => (
                  <li key={l.id}>
                    {l.linked_email} · {l.revoked_at ? "Revoked" : "Active"}
                    <small className="cell-meta">{l.id}</small>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      </div>
      <SourceHistory history={data.history} />
    </>
  );
}
