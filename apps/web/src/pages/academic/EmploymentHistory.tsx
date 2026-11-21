import { useQuery } from "@tanstack/react-query";
import { Link, useOutletContext, useSearchParams } from "react-router-dom";
import { api, type Identity } from "../../lib/api";
import { accessKey, instant } from "../../lib/people";
import { PageHeader, Loading, ErrorState } from "../../components/ui";
import { Pager } from "../../components/PeopleUi";
import { SelectField } from "../../components/SourceUi";

type Episode = { id: string; starts_on: string; ends_before: string | null };
type History = Episode & {
  recorded_at: string;
  source_reference: string;
  order: {
    effective_on: string;
    effective_at: string | null;
    recorded_at: string;
    source_reference: string;
  } | null;
  frozen_at: string | null;
  frozen_subjects: {
    subject_id: string;
    subject: string;
    first_assignment: string;
    deadline: string | null;
    status_at_separation: string;
  }[];
  total: number;
  items: {
    id: string;
    course: string;
    state: string;
    allocation: string | null;
    closure: string | null;
    decided_at: string | null;
  }[];
};

export function EmploymentHistory() {
  const actor = useOutletContext<Identity>(),
    [params, setParams] = useSearchParams();
  const page = Math.max(0, Number(params.get("page")) || 0),
    offset = Math.max(0, Number(params.get("offset")) || 0);
  const episodes = useQuery({
    queryKey: ["my-episodes", accessKey(actor), page],
    queryFn: () =>
      api<{ items: Episode[]; total: number }>(
        `/compliance/episodes?scope=personal&offset=${page}`,
      ),
  });
  const eid = params.get("episode") || episodes.data?.items[0]?.id;
  const history = useQuery({
    queryKey: ["my-episode-history", accessKey(actor), eid, offset],
    enabled: !!eid,
    queryFn: () =>
      api<History>(`/me/employment-episodes/${eid}/history?offset=${offset}`),
  });
  const h = history.data;
  return (
    <>
      <PageHeader
        title="My employment history"
        description="Applications, closure decisions and assessments for each employment episode."
      />
      {episodes.isPending ? (
        <Loading />
      ) : episodes.error ? (
        <ErrorState
          error={episodes.error}
          retry={() => void episodes.refetch()}
        />
      ) : !episodes.data.items.length ? (
        <p>No faculty episodes recorded.</p>
      ) : (
        <section className="panel section-gap">
          <SelectField
            label="Employment episode"
            value={eid}
            onChange={(e) =>
              setParams({ episode: e.target.value, page: String(page) })
            }
          >
            {episodes.data.items.map((ep) => (
              <option key={ep.id} value={ep.id}>
                {ep.starts_on} to {ep.ends_before || "present"}
              </option>
            ))}
          </SelectField>
          {episodes.data.total > 20 && (
            <Pager
              offset={page}
              limit={20}
              total={episodes.data.total}
              change={(n) => setParams({ page: String(n) })}
            />
          )}
          {history.isPending ? (
            <Loading />
          ) : history.error ? (
            <ErrorState
              error={history.error}
              retry={() => void history.refetch()}
            />
          ) : (
            h && (
              <>
                <h2>Employment record</h2>
                <p>
                  {h.starts_on} to {h.ends_before || "present"} ·{" "}
                  {h.source_reference}. Recorded {instant(h.recorded_at)}.
                </p>
                {h.order && (
                  <p>
                    Permanent departure effective{" "}
                    {h.order.effective_at
                      ? instant(h.order.effective_at)
                      : h.order.effective_on}
                    . Recorded {instant(h.order.recorded_at)} under{" "}
                    {h.order.source_reference}.
                  </p>
                )}
                {h.frozen_at && (
                  <p>Separation assessment preserved {instant(h.frozen_at)}.</p>
                )}
                {h.frozen_subjects.length > 0 && (
                  <>
                    <h3>Subject status recorded at separation</h3>
                    <ul className="record-cards">
                      {h.frozen_subjects.map((s) => (
                        <li key={s.subject_id}>
                          <strong>{s.subject}</strong>
                          <span>
                            First assignment {s.first_assignment} · original
                            deadline {s.deadline || "Calendar policy pending"}
                          </span>
                          <span>
                            {s.status_at_separation
                              .replaceAll("_", " ")
                              .toLowerCase()}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
                <div className="record-links">
                  <Link to={`/app/compliance/annual?episode=${eid}`}>
                    Annual assessment
                  </Link>
                  <Link to={`/app/compliance/silver?episode=${eid}`}>
                    Subject-wise Silver assessment
                  </Link>
                </div>
                <h2>Applications in this episode</h2>
                {h.items.length ? (
                  <ul className="record-cards">
                    {h.items.map((a) => (
                      <li key={a.id}>
                        <Link to={`/app/applications/${a.id}/history`}>
                          {a.course}
                        </Link>
                        <span>
                          {a.state} · {a.allocation || "No allocation"}
                        </span>
                        {a.closure && (
                          <span>
                            {a.closure} decision recorded{" "}
                            {instant(a.decided_at)}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No applications recorded for this episode.</p>
                )}
                {h.total > 20 && (
                  <Pager
                    offset={offset}
                    limit={20}
                    total={h.total}
                    change={(n) =>
                      setParams({
                        episode: eid!,
                        offset: String(n),
                        page: String(page),
                      })
                    }
                  />
                )}
              </>
            )
          )}
        </section>
      )}
    </>
  );
}
