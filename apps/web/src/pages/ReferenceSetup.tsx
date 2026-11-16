import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useOutletContext } from "react-router-dom";
import { api, type Identity } from "../lib/api";
import { accessKey, command } from "../lib/people";
import type { References } from "../lib/sources";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
import { CommandError, ScrollTable } from "../components/PeopleUi";
import { Field, SelectField, SourceFields } from "../components/SourceUi";
export function ReferenceSetup({
  initialKind = "subject",
}: {
  initialKind?: string;
}) {
  const actor = useOutletContext<Identity>();
  const cache = useQueryClient();
  const [kind, setKind] = useState(initialKind);
  const [editing, setEditing] = useState("");
  const [notice, setNotice] = useState("");
  const query = useQuery({
    queryKey: ["references", accessKey(actor)],
    queryFn: () => api<References>("/sources/reference"),
  });
  const write = useMutation({
    mutationFn: (form: FormData) => {
      const record = (
        kind === "alias"
          ? query.data?.aliases
          : kind === "department"
            ? query.data?.departments
            : query.data?.subjects
      )?.find((r) => r.id === editing);
      return command(
        "/admin/reference",
        {
          kind,
          ...(editing
            ? { id: editing, expected_version: record?.version }
            : {}),
          source_reference: form.get("source_reference"),
          reason: form.get("reason"),
          ...(kind === "year"
            ? { starts_on: form.get("starts_on") }
            : kind === "alias"
              ? { subject_id: form.get("subject_id"), name: form.get("name") }
              : { code: form.get("code"), name: form.get("name") }),
        },
        crypto.randomUUID(),
      );
    },
    onSuccess: () => {
      setNotice("Official reference saved with source history.");
      setEditing("");
      void cache.invalidateQueries();
    },
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorState error={query.error} retry={() => void query.refetch()} />
    );
  const data = query.data;
  if (!data) return null;
  const selected = (
    kind === "alias"
      ? data.aliases.map((a) => ({
          id: a.id,
          code: "",
          name: a.alias,
          version: a.version,
        }))
      : kind === "department"
        ? data.departments
        : data.subjects
  ).find((r) => r.id === editing);
  return (
    <>
      <PageHeader
        title="Academic reference data"
        description="Canonical departments and subjects, aliases, and officially configured July–June years."
        action={
          <Badge>
            {actor.can_manage_people ? "Source stewardship" : "Read only"}
          </Badge>
        }
      />
      {notice && (
        <p className="success-notice" role="status">
          {notice}
        </p>
      )}
      {actor.can_manage_people && (
        <section className="panel prose">
          <h2>
            {editing ? "Correct reference name" : "Record official reference"}
          </h2>
          <SelectField
            label="Reference type"
            value={kind}
            onChange={(e) => {
              setKind(e.target.value);
              setEditing("");
              setNotice("");
            }}
          >
            <option value="subject">Canonical subject</option>
            <option value="department">Department</option>
            <option value="alias">Subject alias</option>
            <option value="year">Academic year</option>
          </SelectField>
          <form
            className="source-form"
            key={`${kind}:${editing}`}
            onSubmit={(e) => {
              e.preventDefault();
              write.mutate(new FormData(e.currentTarget));
            }}
          >
            {kind === "year" ? (
              <>
                <Field
                  label="Official academic year starts on"
                  name="starts_on"
                  type="date"
                  required
                />
                <p>
                  Must be July 1. The year ends June 30. Creating a year does
                  not publish quotas or carry capacity forward.
                </p>
              </>
            ) : (
              <>
                {kind === "alias" ? (
                  <SelectField
                    label="Canonical subject"
                    name="subject_id"
                    defaultValue={
                      data.aliases.find((a) => a.id === editing)?.subject_id
                    }
                    required
                  >
                    <option value="">Select subject</option>
                    {data.subjects.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.code} · {s.name}
                      </option>
                    ))}
                  </SelectField>
                ) : (
                  <Field
                    label="Stable canonical code"
                    name="code"
                    required
                    pattern="[A-Z0-9][A-Z0-9_-]{1,29}"
                    defaultValue={selected?.code}
                    readOnly={!!editing}
                  />
                )}
                <Field
                  label={kind === "alias" ? "Alias name" : "Official name"}
                  name="name"
                  required
                  minLength={2}
                  maxLength={160}
                  defaultValue={selected?.name}
                />
              </>
            )}
            <SourceFields />
            <CommandError error={write.error} />
            <button className="primary" disabled={write.isPending}>
              Save official reference
            </button>
            {editing && (
              <button type="button" onClick={() => setEditing("")}>
                Cancel correction
              </button>
            )}
          </form>
        </section>
      )}
      {[
        { title: "Canonical subjects", rows: data.subjects, kind: "subject" },
        { title: "Departments", rows: data.departments, kind: "department" },
      ].map((group) => (
        <section className="panel section-gap" key={group.kind}>
          <div className="panel-header">
            <h2>{group.title}</h2>
          </div>
          <ScrollTable label={group.title}>
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Name</th>
                  <th>Version</th>
                  {actor.can_manage_people && <th>Source action</th>}
                </tr>
              </thead>
              <tbody>
                {group.rows.map((r) => (
                  <tr key={r.id}>
                    <td>{r.code}</td>
                    <td>{r.name}</td>
                    <td>{r.version}</td>
                    {actor.can_manage_people && (
                      <td>
                        <button
                          onClick={() => {
                            setKind(group.kind);
                            setEditing(r.id);
                            window.scrollTo({ top: 0, behavior: "smooth" });
                          }}
                        >
                          Correct {r.code}
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollTable>
          {!group.rows.length && (
            <p className="empty-state">No official records configured.</p>
          )}
        </section>
      ))}
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Official academic years</h2>
        </div>
        <ScrollTable label="Official academic years">
          <table>
            <thead>
              <tr>
                <th>Year</th>
                <th>Starts</th>
                <th>Ends</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {data.years.map((y) => (
                <tr key={y.id}>
                  <td>{y.label}</td>
                  <td>{y.starts_on}</td>
                  <td>{y.ends_on}</td>
                  <td>{y.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollTable>
      </section>
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Subject aliases</h2>
        </div>
        <ul className="record-cards">
          {data.aliases.map((a) => (
            <li key={a.id}>
              <strong>{a.alias}</strong>
              <span>
                {data.subjects.find((s) => s.id === a.subject_id)?.name} ·{" "}
                {a.source_reference}
              </span>
              {actor.can_manage_people && (
                <button
                  onClick={() => {
                    setKind("alias");
                    setEditing(a.id);
                    window.scrollTo({ top: 0, behavior: "smooth" });
                  }}
                >
                  Correct alias {a.alias}
                </button>
              )}
            </li>
          ))}
        </ul>
        {!data.aliases.length && (
          <p className="empty-state">
            No subject aliases recorded. Similar names are never automatically
            merged.
          </p>
        )}
      </section>
    </>
  );
}
