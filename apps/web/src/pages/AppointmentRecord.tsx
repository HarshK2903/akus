import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useOutletContext, useParams } from "react-router-dom";
import { api, type Identity } from "../lib/api";
import {
  accessKey,
  command,
  instant,
  officeLabel,
  type Appointment,
} from "../lib/people";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
import { CommandError } from "../components/PeopleUi";
export function AppointmentRecord() {
  const actor = useOutletContext<Identity>();
  const { appointmentId } = useParams();
  const cache = useQueryClient();
  const key = useRef(crypto.randomUUID());
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const query = useQuery({
    queryKey: ["appointment", appointmentId, accessKey(actor)],
    queryFn: () => api<Appointment>(`/people/appointments/${appointmentId}`),
  });
  const end = useMutation({
    mutationFn: () =>
      command(
        `/admin/appointments/${appointmentId}/end`,
        { expected_version: query.data!.version, reason },
        key.current,
      ),
    onSuccess: async () => {
      await Promise.all(
        ["appointment", "appointments", "person", "staff", "me"].map((name) =>
          cache.invalidateQueries({ queryKey: [name] }),
        ),
      );
    },
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorState error={query.error} retry={() => void query.refetch()} />
    );
  if (!query.data) return null;
  const a = query.data;
  return (
    <>
      <PageHeader
        title="Office appointment record"
        description={`${a.person_name} · ${officeLabel(a.office)}`}
        action={
          <Badge tone={a.status === "CURRENT" ? "success" : "neutral"}>
            {a.status.toLowerCase()}
          </Badge>
        }
      />
      <div className="record-links">
        <Link
          to={
            actor.can_manage_people
              ? "/admin/appointments"
              : actor.can_read_directory
                ? "/people/appointments"
                : "/app/profile"
          }
        >
          ←{" "}
          {actor.can_read_directory
            ? "Office appointments"
            : "Profile & access"}
        </Link>
      </div>
      {end.isSuccess && (
        <p role="status" className="success-notice">
          Appointment ended. The issued record and change history are preserved.
        </p>
      )}
      <section className="panel form-panel">
        <h2>Issued appointment</h2>
        <dl className="profile-fields">
          <dt>Person</dt>
          <dd>{a.person_name}</dd>
          <dt>Office / scope</dt>
          <dd>
            {officeLabel(a.office)} · {a.department ?? "Institution-wide"}
          </dd>
          <dt>Effective from</dt>
          <dd>{instant(a.valid_from)}</dd>
          <dt>Originally issued until</dt>
          <dd>{instant(a.original_until)}</dd>
          <dt>Current effective until (exclusive)</dt>
          <dd>{instant(a.valid_until)}</dd>
          <dt>Official source</dt>
          <dd>{a.source_reference}</dd>
          <dt>Original rationale</dt>
          <dd>{a.reason}</dd>
          <dt>Recorded at / version</dt>
          <dd>
            {instant(a.recorded_at)} · {a.version}
          </dd>
        </dl>
      </section>
      {actor.can_manage_people && a.status === "CURRENT" && (
        <section className="panel form-panel section-gap">
          <h2>End current authority</h2>
          <p className="section-gap">
            This ends the appointment at the server decision time. It preserves
            prior authority and decisions. Employment and academic cases are
            unaffected by this source action.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              end.mutate();
            }}
          >
            <label htmlFor="end-reason">Reason and source reference</label>
            <textarea
              id="end-reason"
              required
              minLength={5}
              maxLength={1000}
              value={reason}
              disabled={end.isPending}
              onChange={(e) => {
                setReason(e.target.value);
                key.current = crypto.randomUUID();
                end.reset();
              }}
            />
            <label className="checkbox-label">
              <input
                type="checkbox"
                required
                checked={confirmed}
                disabled={end.isPending}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              I confirm this source appointment must end now.
            </label>
            <CommandError error={end.error} />
            <div className="form-actions">
              <button
                className="primary"
                disabled={end.isPending || !confirmed}
              >
                {end.isPending ? "Ending…" : "End appointment now"}
              </button>
            </div>
          </form>
        </section>
      )}
    </>
  );
}
