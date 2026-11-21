import { StaffSources } from "../components/StaffSources";
import { accessKey } from "../lib/people";
import { useQuery } from "@tanstack/react-query";
import {
  Link,
  useLocation,
  useOutletContext,
  useParams,
} from "react-router-dom";
import { api } from "../lib/api";
import type { Identity } from "../lib/api";
import type { StaffDetail } from "../lib/people";
import { instant, officeLabel } from "../lib/people";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
import { ScrollTable } from "../components/PeopleUi";
export function StaffRecord({ own = false }: { own?: boolean }) {
  const actor = useOutletContext<Identity>();
  const { staffId } = useParams();
  const location = useLocation();
  const personId = own ? actor.person_id : staffId;
  const query = useQuery({
    queryKey: ["person", personId, accessKey(actor)],
    queryFn: () =>
      api<StaffDetail>(own ? "/me/authority" : `/people/staff/${personId}`),
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorState error={query.error} retry={() => void query.refetch()} />
    );
  if (!query.data) return null;
  const data = query.data;
  const isEmployment = location.pathname.endsWith("/employment");
  return (
    <>
      <PageHeader
        title={own ? "Profile & access" : data.person.display_name}
        description={
          own
            ? "Current authority is resolved from employment and effective office records on every API request."
            : `${data.person.staff_key} · Permanent person identity`
        }
        action={
          !own && actor.can_manage_people ? (
            <Link
              className="button"
              to={`/admin/appointments/new?person=${data.person.id}`}
            >
              Record appointment
            </Link>
          ) : (
            <Badge>Source records</Badge>
          )
        }
      />
      {location.state?.notice && (
        <p className="success-notice" role="status">
          {String(location.state.notice)}
        </p>
      )}
      {!own && (
        <div className="record-links">
          <Link to={actor.can_manage_people ? "/admin/staff" : "/people/staff"}>
            ← Staff directory
          </Link>
          {actor.can_manage_people && (
            <Link to={`/admin/staff/${data.person.id}/sources`}>
              Manage source records
            </Link>
          )}
          {actor.can_manage_people && (
            <Link
              to={`/admin/staff/${data.person.id}${isEmployment ? "" : "/employment"}`}
            >
              {isEmployment ? "Identity overview" : "Employment history"}
            </Link>
          )}
        </div>
      )}
      <div className="overview-grid">
        <section className="panel">
          <div className="panel-header">
            <h2>Institutional record</h2>
            <Badge
              tone={
                data.person.employment_status === "ACTIVE"
                  ? "success"
                  : "neutral"
              }
            >
              {data.person.employment_status === "ACTIVE"
                ? "Active employment"
                : "Inactive employment"}
            </Badge>
          </div>
          <dl className="profile-fields">
            <dt>Display name</dt>
            <dd>{data.person.display_name}</dd>
            <dt>Permanent staff key</dt>
            <dd>{data.person.staff_key}</dd>
            <dt>Current home department</dt>
            <dd>{data.person.department ?? "No current assignment"}</dd>
            <dt>Source reference</dt>
            <dd>{data.source_reference}</dd>
            <dt>Recorded at</dt>
            <dd>{instant(data.recorded_at)}</dd>
          </dl>
        </section>
        <section className="panel">
          <div className="panel-header">
            <h2>{own ? "Your effective access" : "Source stewardship"}</h2>
          </div>
          <div className="prose">
            {own ? (
              <>
                <p>
                  Current roles:{" "}
                  <strong>{(actor.roles ?? []).join(", ") || "Staff"}</strong>
                </p>
                <p>
                  {actor.can_manage_people
                    ? "You may maintain staff and office source records. Admin access alone grants no academic approval rights."
                    : (actor.roles ?? []).includes("PRINCIPAL")
                      ? "Institution-wide read-only oversight. Principal status does not grant source editing or academic decisions."
                      : (actor.roles ?? []).includes("HOD")
                        ? "You may read current departmental staff and offices. HoD is NPTEL-exempt."
                        : (actor.roles ?? []).includes("DRC_HEAD")
                          ? "Faculty eligibility remains. Your own applications will route directly to HoD; no self-review is permitted."
                          : actor.applicant_eligible
                            ? "You can apply for an NPTEL offering. Your application goes to the department DRC Head and then to the HoD."
                            : "Your current employment does not grant faculty applicant eligibility or an academic office."}
                </p>
                <p>
                  {actor.mode === "LOCAL_DEMO"
                    ? "This session uses a fictional LOCAL / DEMO identity."
                    : "This session uses a verified Google identity and current institutional source authority."}
                </p>
              </>
            ) : (
              <>
                <p>
                  Employment, department and office records have separate
                  effective dates. Issued appointment facts and audit events are
                  preserved.
                </p>
                <p>
                  Source corrections retain the earlier facts. A documented
                  permanent departure opens the applicable separation workflow.
                </p>
              </>
            )}
          </div>
        </section>
      </div>
      <section className="panel">
        <div className="panel-header">
          <h2>Employment episodes</h2>
          <span className="small">Dates only · end date is exclusive</span>
        </div>
        <ScrollTable label="Employment history">
          <table>
            <thead>
              <tr>
                <th>Start date</th>
                <th>End before</th>
                <th>Classification</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {data.episodes.map((e) => (
                <tr key={e.id}>
                  <td>{e.starts_on}</td>
                  <td>{e.ends_before ?? "Open-ended"}</td>
                  <td>{e.is_faculty ? "Faculty" : "Non-faculty"}</td>
                  <td>{e.source_reference}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollTable>
      </section>
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Office history</h2>
          <span className="small">Exact instants displayed in IST</span>
        </div>
        {data.appointments.length ? (
          <ScrollTable label="Office history">
            <table>
              <thead>
                <tr>
                  <th>Office / scope</th>
                  <th>Effective from</th>
                  <th>Effective until (exclusive)</th>
                  <th>State</th>
                </tr>
              </thead>
              <tbody>
                {data.appointments.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <Link
                        to={`${actor.can_manage_people ? "/admin" : "/people"}/appointments/${a.id}`}
                      >
                        {officeLabel(a.office)}
                      </Link>
                      <small className="cell-meta">
                        {a.department ?? "Institution-wide"}
                      </small>
                    </td>
                    <td>{instant(a.valid_from)}</td>
                    <td>{instant(a.valid_until)}</td>
                    <td>
                      <Badge>{a.status.toLowerCase()}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </ScrollTable>
        ) : (
          <p className="empty-state">No office appointments recorded.</p>
        )}
      </section>
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Recorded changes</h2>
          <span className="small">Latest 100 immutable events</span>
        </div>
        {data.events.length ? (
          <ol className="source-timeline">
            {data.events.map((e) => (
              <li key={e.id}>
                <strong>{e.action.replaceAll("_", " ")}</strong>
                <time>{instant(e.recorded_at)}</time>
                <p>{e.details.reason}</p>
                {e.details.ended_at && (
                  <small>Authority ended: {instant(e.details.ended_at)}</small>
                )}
              </li>
            ))}
          </ol>
        ) : (
          <p className="empty-state">
            No interactive changes recorded for this source fixture.
          </p>
        )}
      </section>
      <StaffSources personId={data.person.id} actor={actor} />
    </>
  );
}
