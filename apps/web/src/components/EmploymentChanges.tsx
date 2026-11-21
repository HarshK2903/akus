import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type Identity } from "../lib/api";
import { accessKey, command, instant } from "../lib/people";
import type { Reference, StaffSources } from "../lib/sources";
import { CommandError, Pager } from "./PeopleUi";
import { Field, SelectField } from "./SourceUi";
import { ErrorState, Loading } from "./ui";

type Impact = {
  recorded_at: string;
  order: {
    effective_on: string;
    effective_at: string | null;
    recorded_at: string;
    source_reference: string;
  } | null;
  total: number;
  applications: {
    id: string;
    state: string;
    pool_id: string | null;
    allocation: string | null;
    open_reviews: string[];
  }[];
  subjects: {
    subject: string;
    first_assignment: string;
    deadline: string | null;
  }[];
  offices: { office: string; valid_from: string; valid_until: string | null }[];
};

export function EmploymentChanges({
  sources,
  departments,
  actor,
}: {
  sources: StaffSources;
  departments: Reference[];
  actor: Identity;
}) {
  const last = sources.episodes.at(-1);
  const [preview, setPreview] = useState<{
    episode: string;
    day: string;
    offset: number;
  } | null>(null);
  const [receipt, setReceipt] = useState("");
  const cache = useQueryClient();
  const impact = useQuery({
    queryKey: ["employment-impact", accessKey(actor), preview],
    enabled: !!preview,
    queryFn: () =>
      api<Impact>(
        `/admin/employment-episodes/${preview!.episode}/impact?effective_on=${preview!.day}&offset=${preview!.offset}`,
      ),
  });
  const hire = useMutation({
    mutationFn: (f: FormData) =>
      command(
        `/admin/staff/${sources.person.id}/rehire`,
        {
          previous_episode_id: last?.id,
          expected_version: last?.source_version,
          starts_on: f.get("start"),
          department_id: f.get("department"),
          is_faculty: f.get("classification") === "faculty",
          source_reference: f.get("source"),
          reason: f.get("reason"),
        },
        crypto.randomUUID(),
      ),
    onSuccess: (r) => {
      setReceipt(r.id);
      void cache.invalidateQueries();
    },
  });
  return (
    <>
      <section className="panel section-gap">
        <h2>Employment impact preview</h2>
        <form
          className="source-form"
          onSubmit={(e) => {
            e.preventDefault();
            const f = new FormData(e.currentTarget);
            setPreview({
              episode: String(f.get("episode")),
              day: String(f.get("day")),
              offset: 0,
            });
          }}
        >
          <SelectField
            name="episode"
            label="Episode to preview"
            defaultValue={last?.id}
            required
          >
            {sources.episodes.map((ep) => (
              <option key={ep.id} value={ep.id}>
                {String(ep.starts_on)} to {String(ep.ends_before ?? "present")}
              </option>
            ))}
          </SelectField>
          <Field
            type="date"
            name="day"
            label="Proposed effective end date"
            required
          />
          <button>Preview impact</button>
        </form>
        {preview &&
          (impact.isPending ? (
            <Loading />
          ) : impact.error ? (
            <ErrorState
              error={impact.error}
              retry={() => void impact.refetch()}
            />
          ) : (
            <div className="prose" aria-live="polite">
              <h3>Records affected on {preview.day}</h3>
              <p>
                Episode recorded {instant(impact.data.recorded_at)}.{" "}
                {impact.data.order
                  ? `Official order ${impact.data.order.source_reference}, effective ${impact.data.order.effective_at ? instant(impact.data.order.effective_at) : impact.data.order.effective_on} and recorded ${instant(impact.data.order.recorded_at)}.`
                  : "No permanent departure order is on file."}
              </p>
              <h4>Applications and current quota</h4>
              {impact.data.applications.length ? (
                <ul>
                  {impact.data.applications.map((a) => (
                    <li key={a.id}>
                      {a.id} · {a.state} · {a.allocation || "No allocation"}{" "}
                      {a.pool_id && `in pool ${a.pool_id}`}
                      {a.open_reviews.length > 0 &&
                        ` · ${a.open_reviews.join(", ")}`}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No applications in this episode.</p>
              )}
              {impact.data.total > 20 && (
                <Pager
                  total={impact.data.total}
                  limit={20}
                  offset={preview.offset}
                  change={(offset) => setPreview({ ...preview, offset })}
                />
              )}
              <h4>Subject deadlines</h4>
              {impact.data.subjects.length ? (
                <ul>
                  {impact.data.subjects.map((s) => (
                    <li key={s.subject}>
                      {s.subject} · first assigned {s.first_assignment} ·
                      deadline {s.deadline || "Calendar policy pending"}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No recorded subject obligations by this date.</p>
              )}
              <h4>Office appointments extending past the proposed end</h4>
              {impact.data.offices.length ? (
                <ul>
                  {impact.data.offices.map((o) => (
                    <li key={o.office + o.valid_from}>
                      {o.office} · {instant(o.valid_from)} to{" "}
                      {instant(o.valid_until)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No affected office appointments.</p>
              )}
            </div>
          ))}
      </section>
      {(last?.ends_before || receipt) && (
        <section className="panel section-gap">
          <h2>Record a rehire</h2>
          {receipt && (
            <p role="status">
              New employment episode and home department recorded. Episode{" "}
              {receipt}.
            </p>
          )}
          {!!last?.ends_before && (
            <form
              className="source-form"
              onSubmit={(e) => {
                e.preventDefault();
                hire.mutate(new FormData(e.currentTarget));
              }}
            >
              <p>
                Previous episode ended {String(last.ends_before)}. This records
                a new appointment for the same person.
              </p>
              <Field
                label="Rehire start date"
                name="start"
                type="date"
                min={String(last.ends_before)}
                required
              />
              <SelectField
                label="New home department"
                name="department"
                required
                defaultValue=""
              >
                <option value="">Select department</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </SelectField>
              <SelectField
                label="New employment classification"
                name="classification"
                defaultValue=""
                required
              >
                <option value="">Select classification</option>
                <option value="faculty">Faculty</option>
                <option value="staff">Non-faculty staff</option>
              </SelectField>
              <Field
                label="Rehire order reference"
                name="source"
                required
                minLength={3}
                maxLength={300}
              />
              <Field
                label="Reason for rehire entry"
                name="reason"
                required
                minLength={5}
                maxLength={1000}
              />
              <CommandError error={hire.error} />
              <button className="primary" disabled={hire.isPending}>
                Record rehire
              </button>
            </form>
          )}
        </section>
      )}
    </>
  );
}
