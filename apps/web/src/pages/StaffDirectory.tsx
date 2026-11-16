import { accessKey } from "../lib/people";
import { useQuery } from "@tanstack/react-query";
import {
  Link,
  Navigate,
  useOutletContext,
  useSearchParams,
} from "react-router-dom";
import { api } from "../lib/api";
import type { Identity } from "../lib/api";
import type { StaffPage } from "../lib/people";
import { officeLabel } from "../lib/people";
import { PageHeader, Badge, ErrorState, Loading } from "../components/ui";
import { Pager, ScrollTable } from "../components/PeopleUi";
export function StaffDirectory() {
  const actor = useOutletContext<Identity>();
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const rawOffset = Number(params.get("offset"));
  const offset = Number.isFinite(rawOffset) && rawOffset >= 0 ? rawOffset : 0;
  const query = useQuery({
    queryKey: ["staff", q, offset, accessKey(actor)],
    queryFn: () =>
      api<StaffPage>(
        `/people/staff?q=${encodeURIComponent(q)}&offset=${offset}&limit=25`,
      ),
    enabled: actor.can_read_directory,
  });
  if (!actor.can_read_directory)
    return <Navigate to="/access-denied" replace />;
  const base = actor.can_manage_people ? "/admin/staff" : "/people/staff";
  return (
    <>
      <PageHeader
        title="Staff directory"
        description={
          actor.can_manage_people
            ? `Permanent identities and effective employment records.${actor.mode === "LOCAL_DEMO" ? " All records in this environment are LOCAL / DEMO." : " Official institutional sources."}`
            : (actor.roles ?? []).includes("PRINCIPAL")
              ? "Institution-wide oversight. Source records are read-only."
              : "Current departmental scope, resolved from your effective office appointment."
        }
        action={
          actor.can_manage_people ? (
            <Link className="button primary" to="/admin/staff/new">
              Add staff record
            </Link>
          ) : (
            <Badge>Read-only</Badge>
          )
        }
      />
      <section className="panel">
        <div className="directory-toolbar">
          <label htmlFor="staff-search">
            Search name or permanent staff key
          </label>
          <input
            id="staff-search"
            type="search"
            value={q}
            onChange={(e) =>
              setParams(e.target.value ? { q: e.target.value } : {}, {
                replace: true,
              })
            }
            placeholder="Search staff…"
          />
        </div>
        {query.isPending ? (
          <Loading />
        ) : query.error ? (
          <ErrorState error={query.error} retry={() => void query.refetch()} />
        ) : (
          query.data && (
            <>
              <ScrollTable label="Staff records">
                <table>
                  <thead>
                    <tr>
                      <th>Staff member</th>
                      <th>Department</th>
                      <th>Employment</th>
                      <th>Current offices</th>
                    </tr>
                  </thead>
                  <tbody>
                    {query.data.items.map((p) => (
                      <tr key={p.id}>
                        <td>
                          <Link to={`${base}/${p.id}`}>{p.display_name}</Link>
                          <small className="cell-meta">{p.staff_key}</small>
                        </td>
                        <td>{p.department ?? "No current assignment"}</td>
                        <td>
                          <Badge
                            tone={
                              p.employment_status === "ACTIVE"
                                ? "success"
                                : "neutral"
                            }
                          >
                            {p.employment_status === "ACTIVE"
                              ? "Active"
                              : "Inactive"}
                          </Badge>
                        </td>
                        <td>
                          {p.offices.map(officeLabel).join(", ") ||
                            "No current office"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollTable>
              {!query.data.items.length && (
                <p className="empty-state">
                  No staff records match this search.
                </p>
              )}
              <Pager
                total={query.data.total}
                offset={offset}
                limit={25}
                change={(value) => setParams({ q, offset: String(value) })}
              />
            </>
          )
        )}
      </section>
      <p className="panel-footnote">
        Creating a staff record does not provision Google sign-in or grant an
        academic office.
      </p>
    </>
  );
}
