import { accessKey } from "../lib/people";
import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Link,
  Navigate,
  useNavigate,
  useOutletContext,
  useSearchParams,
} from "react-router-dom";
import { api } from "../lib/api";
import type { Identity } from "../lib/api";
import { command, officeLabel } from "../lib/people";
import type {
  AppointmentCreate,
  Department,
  StaffDetail,
  StaffPage,
} from "../lib/people";
import { ErrorState, Loading, PageHeader } from "../components/ui";
import { CommandError } from "../components/PeopleUi";
export function AppointmentNew() {
  const actor = useOutletContext<Identity>();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const cache = useQueryClient();
  const key = useRef(crypto.randomUUID());
  const [search, setSearch] = useState("");
  const [form, setForm] = useState({
    person_id: params.get("person") ?? "",
    office: "DRC_HEAD",
    department_id: "",
    valid_from: "",
    valid_until: "",
    source_reference: "",
    reason: "",
  });
  const departments = useQuery({
    queryKey: ["departments", accessKey(actor)],
    queryFn: () => api<Department[]>("/people/departments"),
    enabled: actor.can_manage_people,
  });
  const people = useQuery({
    queryKey: ["staff", search, 0, accessKey(actor)],
    queryFn: () =>
      api<StaffPage>(`/people/staff?q=${encodeURIComponent(search)}&limit=25`),
    enabled: actor.can_manage_people,
  });
  const selected = useQuery({
    queryKey: ["person", form.person_id, accessKey(actor)],
    queryFn: () => api<StaffDetail>(`/people/staff/${form.person_id}`),
    enabled: !!form.person_id && actor.can_manage_people,
  });
  const save = useMutation({
    mutationFn: () =>
      command(
        "/admin/appointments",
        {
          ...form,
          office: form.office as AppointmentCreate["office"],
          department_id:
            form.office === "PRINCIPAL" ? null : form.department_id,
          valid_from: new Date(form.valid_from + "+05:30").toISOString(),
          valid_until: form.valid_until
            ? new Date(form.valid_until + "+05:30").toISOString()
            : null,
        },
        key.current,
      ),
    onSuccess: async () => {
      await Promise.all([
        cache.invalidateQueries({ queryKey: ["appointments"] }),
        cache.invalidateQueries({ queryKey: ["person"] }),
        cache.invalidateQueries({ queryKey: ["staff"] }),
        cache.invalidateQueries({ queryKey: ["me"] }),
      ]);
      navigate(`/admin/staff/${form.person_id}`, {
        state: {
          notice:
            "Appointment recorded. Authority follows the effective interval.",
        },
      });
    },
  });
  function change(field: string, value: string) {
    setForm({ ...form, [field]: value });
    key.current = crypto.randomUUID();
    save.reset();
  }
  if (!actor.can_manage_people) return <Navigate to="/access-denied" replace />;
  return (
    <>
      <PageHeader
        title="Record office appointment"
        description="Use the formal source appointment. The server checks employment, scope and overlapping authority before committing."
      />
      <section className="panel form-panel">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
        >
          <fieldset disabled={save.isPending}>
            <legend>Appointee and authority</legend>
            <label htmlFor="person-search">Find staff by name or key</label>
            <input
              id="person-search"
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <label htmlFor="appointee">Staff member</label>
            {people.isPending ? (
              <Loading />
            ) : people.error ? (
              <ErrorState
                error={people.error}
                retry={() => void people.refetch()}
              />
            ) : (
              <select
                id="appointee"
                required
                value={form.person_id}
                onChange={(e) => change("person_id", e.target.value)}
              >
                <option value="">Select staff member</option>
                {selected.data &&
                  !people.data?.items.some((p) => p.id === form.person_id) && (
                    <option value={form.person_id}>
                      {selected.data.person.display_name}
                    </option>
                  )}
                {people.data?.items.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.display_name} · {p.staff_key}
                  </option>
                ))}
              </select>
            )}
            <small>
              Search returns the first 25 matches; refine the name or key if
              needed.
            </small>
            <div className="form-grid">
              <div>
                <label htmlFor="office">Office</label>
                <select
                  id="office"
                  value={form.office}
                  onChange={(e) => change("office", e.target.value)}
                >
                  {["DRC_HEAD", "HOD", "ACTING_HOD", "PRINCIPAL"].map((o) => (
                    <option key={o} value={o}>
                      {officeLabel(o)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="office-department">Scope</label>
                {form.office === "PRINCIPAL" ? (
                  <p>Institution-wide</p>
                ) : departments.error ? (
                  <ErrorState
                    error={departments.error}
                    retry={() => void departments.refetch()}
                  />
                ) : (
                  <select
                    id="office-department"
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
                <label htmlFor="valid-from">Effective from (IST)</label>
                <input
                  id="valid-from"
                  type="datetime-local"
                  step="1"
                  required
                  value={form.valid_from}
                  onChange={(e) => change("valid_from", e.target.value)}
                />
              </div>
              <div>
                <label htmlFor="valid-until">
                  Effective until (IST, exclusive)
                </label>
                <input
                  id="valid-until"
                  type="datetime-local"
                  step="1"
                  value={form.valid_until}
                  onChange={(e) => change("valid_until", e.target.value)}
                />
                <small>
                  Leave blank only for an open-ended source appointment.
                </small>
              </div>
            </div>
            <label htmlFor="appointment-source">
              Official source reference
            </label>
            <input
              id="appointment-source"
              required
              minLength={3}
              maxLength={300}
              value={form.source_reference}
              onChange={(e) => change("source_reference", e.target.value)}
            />
            <label htmlFor="appointment-reason">Appointment rationale</label>
            <textarea
              id="appointment-reason"
              required
              minLength={5}
              maxLength={1000}
              value={form.reason}
              onChange={(e) => change("reason", e.target.value)}
            />
            <div className="context-note">
              DRC Head and HoD/acting HoD may never overlap for the same person,
              including in different departments. Existing academic cases are
              not automatically waived, approved or withdrawn by an office
              change.
            </div>
            <CommandError error={save.error} />
            <div className="form-actions">
              <Link className="button" to="/admin/appointments">
                Cancel
              </Link>
              <button
                className="primary"
                disabled={save.isPending || !departments.data}
              >
                {save.isPending ? "Recording…" : "Record appointment"}
              </button>
            </div>
          </fieldset>
        </form>
      </section>
    </>
  );
}
