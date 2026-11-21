import { useQuery } from "@tanstack/react-query";
import { Link, useOutletContext } from "react-router-dom";
import {
  ArrowRight,
  CircleCheck,
  RefreshCw,
  Server,
  ShieldCheck,
} from "lucide-react";
import { api, roleLabels } from "../lib/api";
import type { Foundation, Identity, Year } from "../lib/api";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
export function Overview() {
  const person = useOutletContext<Identity>();
  const status = useQuery({
    queryKey: ["foundation"],
    queryFn: () => api<Foundation>("/foundation"),
    refetchInterval: 15000,
  });
  const years = useQuery({
    queryKey: ["years"],
    queryFn: () => api<Year[]>("/academic-years"),
  });
  return (
    <>
      <PageHeader
        title="System connections & academic calendar"
        description={`Welcome, ${person.name}. Current access · ${roleLabels[person.role]}.`}
        action={
          <button
            onClick={() => {
              void status.refetch();
              void years.refetch();
            }}
            disabled={status.isFetching}
          >
            <RefreshCw size={15} />
            Refresh status
          </button>
        }
      />
      <section className="intro-panel">
        <div>
          <h2>Employment and office authority</h2>
          <p>
            Your access is resolved from current employment and office records.
            Open your profile to inspect your current department and effective
            appointments.
          </p>
          <Link className="text-link" to="/app/profile">
            View your profile & access <ArrowRight size={15} />
          </Link>
        </div>
        <div className="intro-mark" aria-hidden="true">
          <ShieldCheck size={42} />
          <span>AKUS</span>
          <small>Clarity. Traceability. Trust.</small>
        </div>
      </section>
      {person.can_read_directory && (
        <section className="panel section-gap">
          <div className="panel-header">
            <h2>
              {person.can_manage_people
                ? "Institutional source management"
                : (person.roles ?? []).includes("PRINCIPAL")
                  ? "Institution-wide oversight"
                  : "Departmental oversight"}
            </h2>
            <Badge>
              {person.can_manage_people ? "Admin authority" : "Read-only"}
            </Badge>
          </div>
          <div className="prose">
            <p>
              {person.can_manage_people
                ? "Create permanent staff records, record formal office appointments, and end current authority with a reason and an immutable history."
                : "Read staff and appointment records within your current authorized scope. Source editing requires separate Admin authority."}
            </p>
            <div className="record-links">
              <Link
                to={person.can_manage_people ? "/admin/staff" : "/people/staff"}
              >
                Open staff directory →
              </Link>
              <Link
                to={
                  person.can_manage_people
                    ? "/admin/appointments"
                    : "/people/appointments"
                }
              >
                Open office register →
              </Link>
            </div>
          </div>
        </section>
      )}
      <div className="overview-grid">
        <section className="panel">
          <div className="panel-header">
            <h2>Environment status</h2>
            <Server size={17} />
          </div>
          {status.isPending ? (
            <Loading />
          ) : status.error ? (
            <ErrorState
              error={status.error}
              retry={() => void status.refetch()}
            />
          ) : (
            status.data && (
              <>
                <ul className="status-list">
                  <li>
                    <span>
                      <strong>Application API</strong>
                      <small>FastAPI · live response</small>
                    </span>
                    <Badge tone="success">Connected</Badge>
                  </li>
                  <li>
                    <span>
                      <strong>Authoritative database</strong>
                      <small>PostgreSQL · current query</small>
                    </span>
                    <Badge tone="success">Connected</Badge>
                  </li>
                  <li>
                    <span>
                      <strong>Background worker</strong>
                      <small>PostgreSQL work ledger</small>
                    </span>
                    <Badge
                      tone={
                        status.data.worker === "running" ? "success" : "warning"
                      }
                    >
                      {status.data.worker === "running"
                        ? "Running"
                        : "Not reporting"}
                    </Badge>
                  </li>
                  <li>
                    <span>
                      <strong>Institutional Google sign-in</strong>
                      <small>
                        {person.mode === "LOCAL_DEMO"
                          ? "Fictional demo sessions available"
                          : "Institutional identity with source authorization"}
                      </small>
                    </span>
                    <Badge>
                      {status.data.google === "configured"
                        ? "Configured"
                        : "Not configured"}
                    </Badge>
                  </li>
                  <li>
                    <span>
                      <strong>NPTEL participation verification</strong>
                      <small>
                        Public metadata is available; enrollment and
                        certificates remain unverified
                      </small>
                    </span>
                    <Badge>Not connected</Badge>
                  </li>
                </ul>
                <p className="panel-footnote">
                  Checked{" "}
                  {new Date(status.data.checked_at).toLocaleTimeString("en-IN")}{" "}
                  · Refreshes every 15 seconds
                </p>
              </>
            )
          )}
        </section>
        <section className="panel">
          <div className="panel-header">
            <h2>Your workspace</h2>
            <Badge>Demo identity</Badge>
          </div>
          <div className="workspace-details">
            <span className="eyebrow">CURRENT CONTEXT</span>
            <h3>{roleLabels[person.role]}</h3>
            <p>{person.department}</p>
            <div className="context-note">
              {["HOD", "PRINCIPAL"].includes(person.role)
                ? "HoD and Principal are NPTEL-exempt. Personal application and compulsory compliance flows are not available for these offices."
                : person.role === "DRC_HEAD"
                  ? "DRC Heads remain faculty applicants. Their own applications go directly to a distinct HoD, with no self-review."
                  : person.role === "ADMIN"
                    ? "Administration maintains institutional reference data. Admin status alone grants no academic approval or quota authority."
                    : "Faculty applications follow independent DRC review, then HoD final review."}
            </div>
            <Link className="text-link" to="/app/help">
              Read the policy guide <ArrowRight size={15} />
            </Link>
          </div>
        </section>
      </div>
      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>Academic reference years</h2>
            <p>
              Fictional fixtures read from PostgreSQL. A year record does not
              publish a quota.
            </p>
          </div>
          <Badge>
            {person.mode === "LOCAL_DEMO" ? "LOCAL / DEMO" : "Official source"}
          </Badge>
        </div>
        {years.isPending ? (
          <Loading />
        ) : years.error ? (
          <ErrorState error={years.error} retry={() => void years.refetch()} />
        ) : (
          <div
            className="table-wrap"
            role="region"
            aria-label="Academic reference years"
            tabIndex={0}
          >
            <table>
              <caption className="sr-only">
                Academic year reference fixtures
              </caption>
              <thead>
                <tr>
                  <th>Academic year</th>
                  <th>Starts</th>
                  <th>Ends</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {years.data?.map((y) => (
                  <tr key={y.id}>
                    <td>
                      <strong>{y.label}</strong>
                    </td>
                    <td>{y.starts_on}</td>
                    <td>{y.ends_on}</td>
                    <td>Local demo fixture</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!years.data?.length && (
              <p className="empty-state">No academic years configured.</p>
            )}
          </div>
        )}
      </section>
      <section className="delivery-section">
        <div>
          <div className="eyebrow">WORKSPACE CAPABILITIES</div>
          <h2>Available workflows</h2>
          <p>
            Your current institutional authority determines which records and
            decisions you can access.
          </p>
        </div>
        <ol className="phase-list">
          <li>
            <CircleCheck size={18} />
            <div>
              <strong>Application and quota records</strong>
              <span>
                Admission, review decisions and current allocation history
              </span>
            </div>
            <Badge>Available</Badge>
          </li>
          <li>
            <span className="phase-number">02</span>
            <div>
              <strong>People and authority</strong>
              <span>
                Official staff, employment, teaching and effective office
                records
              </span>
            </div>
            <Badge>Current sources</Badge>
          </li>
          <li>
            <span className="phase-number">03</span>
            <div>
              <strong>Course, topic & quota</strong>
              <span>
                Public provider observations, HoD mappings and published annual
                pools
              </span>
            </div>
            <Badge>Available</Badge>
          </li>
        </ol>
      </section>
    </>
  );
}
