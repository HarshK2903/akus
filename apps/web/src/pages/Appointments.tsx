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
import { instant, officeLabel } from "../lib/people";
import type { AppointmentPage } from "../lib/people";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
import { Pager, ScrollTable } from "../components/PeopleUi";
export function Appointments() {
  const actor = useOutletContext<Identity>();
  const [params, setParams] = useSearchParams();
  const offset = Math.max(0, Number(params.get("offset")) || 0);
  const query = useQuery({
    queryKey: ["appointments", offset, accessKey(actor)],
    queryFn: () =>
      api<AppointmentPage>(`/people/appointments?offset=${offset}&limit=25`),
    enabled: actor.can_read_directory,
  });
  if (!actor.can_read_directory)
    return <Navigate to="/access-denied" replace />;
  return (
    <>
      <PageHeader
        title="Office appointments"
        description="Effective-dated authority, with permanent issued facts and recorded changes. DRC and HoD must remain distinct people."
        action={
          actor.can_manage_people ? (
            <Link className="button primary" to="/admin/appointments/new">
              Record appointment
            </Link>
          ) : (
            <Badge>Read-only oversight</Badge>
          )
        }
      />
      <section className="panel">
        <div className="panel-header">
          <h2>Appointment register</h2>
          <span className="small">All times IST · end is exclusive</span>
        </div>
        {query.isPending ? (
          <Loading />
        ) : query.error ? (
          <ErrorState error={query.error} retry={() => void query.refetch()} />
        ) : (
          query.data && (
            <>
              <ScrollTable label="Office appointment register">
                <table>
                  <thead>
                    <tr>
                      <th>Person / office</th>
                      <th>Scope</th>
                      <th>Validity</th>
                      <th>Source / reason</th>
                      <th>State</th>
                      {actor.can_manage_people && <th>Action</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {query.data.items.map((a) => (
                      <tr key={a.id}>
                        <td>
                          <Link
                            to={`${actor.can_manage_people ? "/admin/appointments" : "/people/appointments"}/${a.id}`}
                          >
                            {a.person_name}
                          </Link>
                          <small className="cell-meta">
                            {officeLabel(a.office)}
                          </small>
                        </td>
                        <td>{a.department ?? "Institution-wide"}</td>
                        <td>
                          {instant(a.valid_from)}
                          <small className="cell-meta">
                            Until {instant(a.valid_until)}
                          </small>
                        </td>
                        <td className="wrap-cell">
                          {a.source_reference}
                          <small className="cell-meta">{a.reason}</small>
                        </td>
                        <td>
                          <Badge
                            tone={
                              a.status === "CURRENT" ? "success" : "neutral"
                            }
                          >
                            {a.status.toLowerCase()}
                          </Badge>
                        </td>
                        {actor.can_manage_people && (
                          <td>
                            <Link
                              className="button"
                              to={`/admin/appointments/${a.id}`}
                            >
                              View appointment
                            </Link>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollTable>
              {!query.data.items.length && (
                <p className="empty-state">
                  No appointments in your authorized scope.
                </p>
              )}
              <Pager
                total={query.data.total}
                offset={offset}
                limit={25}
                change={(n) => setParams({ offset: String(n) })}
              />
            </>
          )
        )}
      </section>
    </>
  );
}
