import { useQuery } from "@tanstack/react-query";
import { Link, Navigate, useOutletContext, useParams } from "react-router-dom";
import { api, roleHome, type Identity } from "../lib/api";
import { accessKey } from "../lib/people";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
import type { Teaching } from "../lib/sources";

type DashboardData = {
  role: string;
  staff_in_scope: number;
  teaching_records: number;
  pending_accounts?: number;
  staged_imports?: number;
  own_review_route: string[];
  applicant_eligible: boolean;
  departments?: { id: string; name: string; teaching_records: number }[];
};
function Tile({ label, value }: { label: string; value: number }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>Recorded institutional sources</small>
    </div>
  );
}
function Journey({
  title,
  description,
  to,
  label,
}: {
  title: string;
  description: string;
  to: string;
  label: string;
}) {
  return (
    <section className="panel dashboard-journey">
      <h2>{title}</h2>
      <p>{description}</p>
      <Link className="button" to={to}>
        {label} →
      </Link>
    </section>
  );
}
function PersonalTeaching() {
  const actor = useOutletContext<Identity>();
  const records = useQuery({
    queryKey: ["teaching-preview", accessKey(actor)],
    queryFn: () =>
      api<{ items: Teaching[] }>(
        `/teaching?person_id=${actor.person_id}&limit=5`,
      ),
  });
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Your teaching record</h2>
        <Badge tone="warning">Acceptance pending</Badge>
      </div>
      {records.isPending ? (
        <Loading />
      ) : records.error ? (
        <ErrorState
          error={records.error}
          retry={() => void records.refetch()}
        />
      ) : records.data?.items.length ? (
        <ul className="record-cards">
          {records.data.items.map((t) => (
            <li key={t.id}>
              <Link to={`/people/teaching/${t.id}`}>{t.subject}</Link>
              <span>
                {t.term} · first recorded teaching {t.first_official_date}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="empty-state">
          No official teaching assignments have been recorded for you.
        </p>
      )}
      <p className="prose">
        IO-02 is awaiting an institutional decision. These records do not
        automatically certify Silver compliance.
      </p>
      <Link className="panel-link" to="/app/teaching">
        Open teaching allocations →
      </Link>
    </section>
  );
}
export function FacultyDashboard({ data }: { data: DashboardData }) {
  return (
    <>
      <PageHeader
        title="Faculty workspace"
        description="Your official teaching record, personal access and academic next steps."
        action={<Badge>Faculty</Badge>}
      />
      <div className="metric-grid">
        <Tile label="Teaching allocations" value={data.teaching_records} />
      </div>
      <div className="overview-grid">
        <PersonalTeaching />
        <Journey
          title="NPTEL participation"
          description="Ordinary faculty applications will pass through DRC review, then HoD. Admission requires approved topic mapping and published capacity."
          to="/app/applications"
          label="Application readiness"
        />
        <Journey
          title="Annual & subject Silver"
          description="Annual completion and subject-wise Silver are separate. Compliance assessment depends on verified examination evidence."
          to="/app/compliance"
          label="Compliance readiness"
        />
        <Journey
          title="Your institutional profile"
          description="Check your effective employment, department membership and access. Request a source correction through your institution’s Admin."
          to="/app/profile"
          label="View profile"
        />
      </div>
    </>
  );
}
export function DrcDashboard({ data }: { data: DashboardData }) {
  return (
    <>
      <PageHeader
        title="DRC Head workspace"
        description="Your faculty responsibilities and independent departmental review capacity."
        action={<Badge>Faculty + DRC Head</Badge>}
      />
      <div className="metric-grid">
        <Tile label="Your teaching allocations" value={data.teaching_records} />
      </div>
      <div className="overview-grid">
        <Journey
          title="Independent review queue"
          description="Review submitted ordinary faculty applications under your current office authority. You cannot review your own application."
          to="/drc/reviews"
          label="Open review queue"
        />
        <Journey
          title="Your own NPTEL application"
          description="Your application goes directly to HoD. DRC officeholding does not remove your faculty obligations."
          to="/app/applications"
          label="Direct-to-HoD route"
        />
        <PersonalTeaching />
        <Journey
          title="Your annual & Silver record"
          description="The same applicable faculty obligations apply. Teaching acceptance remains pending IO-02."
          to="/app/compliance"
          label="Compliance readiness"
        />
      </div>
    </>
  );
}
export function HodDashboard({ data }: { data: DashboardData }) {
  return (
    <>
      <PageHeader
        title="HoD department oversight"
        description="Effective departmental authority, source visibility and academic service readiness."
        action={<Badge>NPTEL-exempt office</Badge>}
      />
      <div className="metric-grid">
        <Tile
          label="Staff in your department scope"
          value={data.staff_in_scope}
        />
        <Tile
          label="Department teaching allocations"
          value={data.teaching_records}
        />
      </div>
      <div className="overview-grid">
        <Journey
          title="Department teaching"
          description="Review recorded subject allocations, terms, effective dates and source correction history."
          to="/hod/teaching"
          label="Open allocations"
        />
        <Journey
          title="Final academic reviews"
          description="Ordinary faculty routes finish with HoD; DRC Head applicants come directly to HoD. Current authority is checked on every decision."
          to="/hod/reviews"
          label="Open review queue"
        />
        <Journey
          title="Primary topic & annual quotas"
          description="A department, approved canonical primary topic and July–June year identify one shared quota pool. Publish capacity, inspect occupancy and reconcile transfers."
          to="/hod/quotas"
          label="Manage annual quotas"
        />
        <Journey
          title="People in your scope"
          description="Read current staff and effective office appointments for departments you hold authority over."
          to="/people/staff"
          label="Open staff directory"
        />
      </div>
    </>
  );
}
export function AdminDashboard({ data }: { data: DashboardData }) {
  return (
    <>
      <PageHeader
        title="Administration workspace"
        description="Maintain official source records and controlled institutional access."
        action={<Badge>Data stewardship</Badge>}
      />
      <div className="metric-grid">
        <Tile label="Staff records" value={data.staff_in_scope} />
        <Tile
          label="Imports awaiting completion"
          value={data.staged_imports ?? 0}
        />
        <Tile
          label="Pending account requests"
          value={data.pending_accounts ?? 0}
        />
      </div>
      <div className="overview-grid">
        <Journey
          title="Official roster & teaching imports"
          description="Upload CSV or XLSX, inspect every row and explicitly commit validated source facts."
          to="/admin/imports"
          label="Open imports"
        />
        <Journey
          title="Staff histories & corrections"
          description="Maintain employment episodes, department membership, institutional emails and source corrections without deleting history."
          to="/admin/staff"
          label="Manage staff"
        />
        <Journey
          title="Academic reference data"
          description="Maintain departments, canonical subjects, subject aliases and official July–June academic years."
          to="/admin/reference"
          label="Open reference setup"
        />
        <Journey
          title="Account-link review"
          description="Resolve verified Google identities against an approved roster. Admin access does not grant academic approval rights."
          to="/admin/accounts"
          label="Review accounts"
        />
      </div>
    </>
  );
}
export function PrincipalDashboard({ data }: { data: DashboardData }) {
  return (
    <>
      <PageHeader
        title="Principal institution overview"
        description="Institution-wide source visibility, with read-only oversight."
        action={<Badge>NPTEL-exempt · read only</Badge>}
      />
      <div className="metric-grid">
        <Tile label="Institutional staff records" value={data.staff_in_scope} />
        <Tile
          label="Recorded teaching allocations"
          value={data.teaching_records}
        />
      </div>
      <section className="panel">
        <div className="panel-header">
          <h2>Department source coverage</h2>
          <Badge>Source inventory</Badge>
        </div>
        <ul className="record-cards">
          {data.departments?.map((d) => (
            <li key={d.id}>
              <Link to={`/principal/teaching?department_id=${d.id}`}>
                {d.name}
              </Link>
              <span>{d.teaching_records} teaching records</span>
            </li>
          ))}
        </ul>
        <p className="prose">
          Counts describe recorded source data, not completion rates or verified
          NPTEL outcomes.
        </p>
      </section>
      <div className="overview-grid section-gap">
        <Journey
          title="Institutional people & offices"
          description="Inspect authorized staff histories and effective appointments across departments."
          to="/people/staff"
          label="Open directory"
        />
        <Journey
          title="Academic reporting readiness"
          description="Institutional compliance reporting requires verified evidence and the later compliance engine. No missing result is treated as failure."
          to="/principal/reports"
          label="Reporting service status"
        />
      </div>
    </>
  );
}
export function Dashboard() {
  const actor = useOutletContext<Identity>();
  const query = useQuery({
    queryKey: ["dashboard", accessKey(actor)],
    queryFn: () => api<DashboardData>("/dashboard"),
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorState error={query.error} retry={() => void query.refetch()} />
    );
  if (!query.data) return null;
  const data = query.data;
  return (
    <>
      {data.role === "ADMIN" ? (
        <AdminDashboard data={data} />
      ) : data.role === "PRINCIPAL" ? (
        <PrincipalDashboard data={data} />
      ) : data.role === "HOD" ? (
        <HodDashboard data={data} />
      ) : data.role === "DRC_HEAD" ? (
        <DrcDashboard data={data} />
      ) : data.role === "FACULTY" ? (
        <FacultyDashboard data={data} />
      ) : (
        <>
          <PageHeader
            title="Staff workspace"
            description="Your institutional source record."
          />
          <Link to="/app/profile">Open profile</Link>
        </>
      )}
      <Link className="panel-link" to="/app/system">
        System connections & academic calendar →
      </Link>
    </>
  );
}
export function RoleDashboard({ role }: { role?: string }) {
  const actor = useOutletContext<Identity>();
  if (role && role !== actor.role)
    return <Navigate to="/access-denied" replace />;
  return <Dashboard />;
}
export function AcademicIntegration({ area: given }: { area?: string }) {
  const actor = useOutletContext<Identity>();
  const { area: param } = useParams();
  const area = given ?? param ?? "applications";
  const query = useQuery({
    queryKey: ["integration", area, accessKey(actor)],
    queryFn: () =>
      api<{ area: string; phase: string; dependency: string }>(
        `/academic/integration/${area}`,
      ),
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorState error={query.error} retry={() => void query.refetch()} />
    );
  return (
    <>
      <PageHeader
        title={`${area[0].toUpperCase()}${area.slice(1)} service status`}
        description="Academic workflow readiness"
        action={<Badge tone="warning">Not yet implemented</Badge>}
      />
      <section className="panel prose">
        <h2>Required before this workflow can run</h2>
        <p>{query.data?.dependency}.</p>
        <p>
          Scheduled for phase {query.data?.phase}. No academic decision, seat
          reservation or compliance result has been created.
        </p>
        {area === "applications" && (
          <p>
            {actor.roles?.includes("DRC_HEAD")
              ? "Your own application will route directly to HoD."
              : "Your application will route through DRC Head and then HoD."}
          </p>
        )}
        <Link className="button" to={roleHome(actor.role)}>
          Return to your workspace
        </Link>
      </section>
    </>
  );
}
