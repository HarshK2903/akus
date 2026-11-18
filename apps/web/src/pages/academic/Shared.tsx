import { Link } from "react-router-dom";
import type { Context, Event, Metadata } from "../../lib/academic";
import { instant } from "../../lib/people";
import { SelectField } from "../../components/SourceUi";
import { Badge } from "../../components/ui";

export function DepartmentChoice({
  context,
  value,
  change,
}: {
  context: Context;
  value: string;
  change: (value: string) => void;
}) {
  return (
    <SelectField
      label="Department scope"
      value={value}
      onChange={(e) => change(e.target.value)}
    >
      {context.departments.map((d) => (
        <option key={d.id} value={d.id}>
          {d.name}
        </option>
      ))}
    </SelectField>
  );
}
export function SourceLink({ url }: { url?: string | null }) {
  if (!url) return <span>Source not available</span>;
  return url?.startsWith("https://onlinecourses.nptel.ac.in/") ? (
    <a href={url} target="_blank" rel="noreferrer">
      Official provider source ↗
    </a>
  ) : (
    <span>LOCAL / DEMO source · no live provider verification</span>
  );
}
export function Dates({ metadata }: { metadata: Metadata }) {
  return (
    <>
      <div className="category-tags">
        {metadata.categories.map((c) => (
          <Badge key={c}>{c}</Badge>
        ))}
      </div>
      <dl className="detail-grid">
        {[
          [
            "Duration",
            metadata.duration_weeks
              ? `${metadata.duration_weeks} weeks`
              : "Unknown",
          ],
          ["Course starts", metadata.starts_on],
          ["Course ends", metadata.ends_on],
          ["Enrollment closes", metadata.enrollment_ends_on],
          ["Exam registration closes", metadata.exam_registration_ends_on],
          ["Published scheduled exam", metadata.scheduled_exam_on],
        ].map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value || "Not supplied"}</dd>
          </div>
        ))}
      </dl>
      <p className="muted">
        Dates are in IST. A published exam is tentative; it proves neither
        attendance nor a certificate.
      </p>
    </>
  );
}
export function History({ events = [] }: { events?: Event[] }) {
  return (
    <section className="panel section-gap">
      <div className="panel-header">
        <h2>Decision and source history</h2>
        <Badge>Immutable events</Badge>
      </div>
      {!events.length ? (
        <p className="empty-state">No recorded decisions yet.</p>
      ) : (
        <ol className="source-history">
          {events.map((e) => (
            <li key={e.id}>
              <strong>{e.kind.replaceAll("_", " ")}</strong>
              <p className="muted">{instant(e.recorded_at)}</p>
              <details>
                <summary>View recorded facts</summary>
                <dl>
                  {Object.entries(e.data).map(([k, v]) => (
                    <div key={k}>
                      <dt>{k.replaceAll("_", " ")}</dt>
                      <dd className="wrap-anywhere">
                        {typeof v === "object"
                          ? JSON.stringify(v)
                          : String(v ?? "None")}
                      </dd>
                    </div>
                  ))}
                </dl>
              </details>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
export function AcademicLinks() {
  return (
    <p className="academic-links">
      <Link to="/app/catalog">Course catalog</Link>
      <Link to="/hod/topics">Canonical topics</Link>
      <Link to="/hod/topic-mappings">Department mappings</Link>
      <Link to="/hod/quotas">Annual topic quotas</Link>
    </p>
  );
}
