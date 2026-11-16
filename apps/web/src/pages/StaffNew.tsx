import { accessKey } from "../lib/people";
import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Link,
  Navigate,
  useNavigate,
  useOutletContext,
} from "react-router-dom";
import { api } from "../lib/api";
import type { Identity } from "../lib/api";
import { command } from "../lib/people";
import type { Department, StaffCreate } from "../lib/people";
import { PageHeader, ErrorState, Loading } from "../components/ui";
import { CommandError } from "../components/PeopleUi";
export function StaffNew() {
  const actor = useOutletContext<Identity>();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const key = useRef(crypto.randomUUID());
  const [form, setForm] = useState({
    staff_key: "",
    display_name: "",
    department_id: "",
    starts_on: "",
    is_faculty: true,
    source_reference: "",
    reason: "",
  });
  const departments = useQuery({
    queryKey: ["departments", accessKey(actor)],
    queryFn: () => api<Department[]>("/people/departments"),
    enabled: actor.can_manage_people,
  });
  const save = useMutation({
    mutationFn: () => command("/admin/staff", form as StaffCreate, key.current),
    onSuccess: async (result) => {
      await cache.invalidateQueries({ queryKey: ["staff"] });
      navigate(`/admin/staff/${result.id}`, {
        state: {
          notice:
            "Staff record created. Initial employment and department assignment saved.",
        },
      });
    },
  });
  function change(field: string, value: string | boolean) {
    setForm({ ...form, [field]: value });
    key.current = crypto.randomUUID();
    save.reset();
  }
  if (!actor.can_manage_people) return <Navigate to="/access-denied" replace />;
  return (
    <>
      <PageHeader
        title="Add staff record"
        description="Record an authoritative permanent identity and its initial employment. No sign-in account or office is created."
      />
      <section className="panel form-panel">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
        >
          <fieldset disabled={save.isPending}>
            <legend>Identity and employment</legend>
            <div className="form-grid">
              <div>
                <label htmlFor="staff-key">Permanent staff key</label>
                <input
                  id="staff-key"
                  required
                  pattern="[A-Z0-9][A-Z0-9_-]{1,39}"
                  maxLength={40}
                  value={form.staff_key}
                  onChange={(e) =>
                    change("staff_key", e.target.value.toUpperCase())
                  }
                />
                <small>
                  Stable institutional key; do not reuse for another person.
                </small>
              </div>
              <div>
                <label htmlFor="display-name">Display name</label>
                <input
                  id="display-name"
                  required
                  minLength={2}
                  maxLength={120}
                  value={form.display_name}
                  onChange={(e) => change("display_name", e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="department">Home department</label>
                {departments.isPending ? (
                  <Loading />
                ) : departments.error ? (
                  <ErrorState
                    error={departments.error}
                    retry={() => void departments.refetch()}
                  />
                ) : (
                  <select
                    id="department"
                    required
                    value={form.department_id}
                    onChange={(e) => change("department_id", e.target.value)}
                  >
                    <option value="">Select department</option>
                    {departments.data?.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              <div>
                <label htmlFor="employment-start">Employment starts on</label>
                <input
                  id="employment-start"
                  type="date"
                  required
                  value={form.starts_on}
                  onChange={(e) => change("starts_on", e.target.value)}
                />
              </div>
            </div>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={form.is_faculty}
                onChange={(e) => change("is_faculty", e.target.checked)}
              />
              Faculty employment classification
            </label>
            <label htmlFor="staff-source">Official source reference</label>
            <input
              id="staff-source"
              required
              minLength={3}
              maxLength={300}
              placeholder="Record or circular reference; do not enter credentials"
              value={form.source_reference}
              onChange={(e) => change("source_reference", e.target.value)}
            />
            <label htmlFor="staff-reason">
              Reason for creating this record
            </label>
            <textarea
              id="staff-reason"
              required
              minLength={5}
              maxLength={1000}
              value={form.reason}
              onChange={(e) => change("reason", e.target.value)}
            />
            <div className="context-note">
              This creates an open-ended initial employment episode. Separation,
              rehire and historical corrections need their own audited
              workflows; they cannot be inferred from this form.
            </div>
            <CommandError error={save.error} />
            <div className="form-actions">
              <Link className="button" to="/admin/staff">
                Cancel
              </Link>
              <button
                className="primary"
                disabled={save.isPending || !departments.data?.length}
              >
                {save.isPending ? "Saving…" : "Create staff record"}
              </button>
            </div>
          </fieldset>
        </form>
      </section>
    </>
  );
}
