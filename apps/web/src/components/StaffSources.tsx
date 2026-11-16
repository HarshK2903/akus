import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api, type Identity } from "../lib/api";
import { accessKey, instant } from "../lib/people";
import type { References, StaffSources as Sources } from "../lib/sources";
import { ErrorState, Loading } from "./ui";
import { ScrollTable } from "./PeopleUi";
export function StaffSources({
  personId,
  actor,
}: {
  personId: string;
  actor: Identity;
}) {
  const data = useQuery({
    queryKey: ["staff-sources", personId, accessKey(actor)],
    queryFn: () => api<Sources>(`/people/staff/${personId}/sources`),
  });
  const refs = useQuery({
    queryKey: ["references", accessKey(actor)],
    queryFn: () => api<References>("/sources/reference"),
  });
  if (data.isPending) return <Loading />;
  if (data.error)
    return <ErrorState error={data.error} retry={() => void data.refetch()} />;
  return (
    <section className="panel section-gap">
      <div className="panel-header">
        <h2>Department & email source history</h2>
        <Link to={`/people/teaching?person_id=${personId}`}>
          View teaching allocations →
        </Link>
      </div>
      <ScrollTable label="Department membership history">
        <table>
          <thead>
            <tr>
              <th>Department</th>
              <th>Effective from</th>
              <th>End before</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {data.data?.memberships.map((m) => (
              <tr key={m.id}>
                <td>
                  {refs.data?.departments.find((d) => d.id === m.department_id)
                    ?.name ?? String(m.department_id)}
                </td>
                <td>{String(m.starts_on)}</td>
                <td>{String(m.ends_before ?? "Open-ended")}</td>
                <td>{String(m.source_reference)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </ScrollTable>
      <div className="prose">
        <h3>Institutional email records</h3>
        {data.data?.emails.length ? (
          <ul>
            {data.data.emails.map((e) => (
              <li key={e.id}>
                {String(e.email)} · {instant(String(e.valid_from))} →{" "}
                {instant(e.valid_until ? String(e.valid_until) : null)}
                <small className="cell-meta">
                  {String(e.source_reference)}
                </small>
              </li>
            ))}
          </ul>
        ) : (
          <p>No official institutional email source recorded.</p>
        )}
        <p>
          Source errors require an authorized Admin correction. Email changes
          never transfer a Google subject to another person.
        </p>
      </div>
    </section>
  );
}
