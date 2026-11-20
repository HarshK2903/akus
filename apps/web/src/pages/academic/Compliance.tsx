import { useQuery } from "@tanstack/react-query";
import {
  Link,
  useLocation,
  useOutletContext,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { api, type Identity } from "../../lib/api";
import { accessKey, instant } from "../../lib/people";
import { useCommand } from "../../lib/academic";
import { Field, SelectField } from "../../components/SourceUi";
import { Pager, CommandError } from "../../components/PeopleUi";
import { Loading, ErrorState, PageHeader, Badge } from "../../components/ui";
import { ComplianceRegister } from "./ComplianceRegister";
import { words } from "../../lib/compliance";

type Episode = {
  id: string;
  name: string;
  starts_on: string;
  ends_before: string | null;
};
type Candidate = {
  event_id: string;
  application_id: string;
  course: string;
  duration_weeks: number;
  actual_exam_on: string | null;
  scheduled_exam_on: string;
  issued_on: string | null;
  score_percent: number | null;
  eligibility: string;
  recorded_at: string;
  relevance_basis: string | null;
};
type Annual = {
  id: string;
  year: string;
  starts_on: string;
  ends_on: string;
  status: string;
  obligation: string;
  allocations: string[];
  candidates: Candidate[];
};
type Silver = {
  id: string;
  subject: string;
  first_assignment: string;
  deadline: string | null;
  source_reference: string | null;
  status_at_separation?: string;
  monitoring: string;
  status: string;
  allocation: string | null;
  candidates: Candidate[];
};
type Report = {
  name: string;
  episode_id: string;
  annual: Annual[];
  silver: Silver[];
  as_of: string;
  view: string;
  snapshots: { id: string; recorded_at: string }[];
};

function Evidence({ rows }: { rows: Candidate[] }) {
  return (
    <>
      {rows.length ? (
        <ul className="record-cards">
          {rows.map((c) => (
            <li key={c.event_id}>
              <strong>{c.course}</strong>
              <span>
                {c.duration_weeks} weeks · actual exam{" "}
                {c.actual_exam_on || "unconfirmed"} · scheduled{" "}
                {c.scheduled_exam_on}
              </span>
              <span>
                Issued {c.issued_on || "pending"} ·{" "}
                {c.score_percent === null
                  ? "score pending"
                  : c.score_percent + "%"}{" "}
                · recorded {instant(c.recorded_at)}
              </span>
              <span>
                {words(c.eligibility)}
                {c.relevance_basis ? " · " + c.relevance_basis : ""}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p>No qualifying or pending evidence recorded for this assessment.</p>
      )}
    </>
  );
}
export function Compliance() {
  const actor = useOutletContext<Identity>(),
    loc = useLocation(),
    { itemId } = useParams();
  const [params, set] = useSearchParams();
  const scope = loc.pathname.startsWith("/principal")
    ? "institution"
    : loc.pathname.startsWith("/hod")
      ? "department"
      : "personal";
  const base =
    scope === "personal"
      ? "/app/compliance"
      : scope === "department"
        ? "/hod/reports"
        : "/principal/reports";
  const silver = loc.pathname.includes("/silver");
  const offset = Math.max(0, Number(params.get("offset")) || 0),
    search = params.get("search") || "";
  const epq = useQuery({
    queryKey: ["compliance-episodes", scope, accessKey(actor), offset, search],
    queryFn: () =>
      api<{ items: Episode[]; total: number }>(
        `/compliance/episodes?${new URLSearchParams({ scope, offset: String(offset), search })}`,
      ),
  });
  const eid = params.get("episode") || epq.data?.items[0]?.id,
    snapshot = params.get("snapshot") || "";
  const rq = useQuery({
    queryKey: ["episode-assessment", accessKey(actor), scope, eid, snapshot],
    enabled: !!eid,
    queryFn: () =>
      api<Report>(
        `/compliance/episodes/${eid}?scope=${scope}${snapshot ? "&snapshot_id=" + snapshot : ""}`,
      ),
  });
  const cmd = useCommand((id) =>
    set(
      new URLSearchParams({
        ...Object.fromEntries(params),
        episode: eid || "",
        snapshot: id,
      }),
    ),
  );
  function switchFilters(changes: Record<string, string>) {
    set(
      Object.fromEntries(
        Object.entries({ ...Object.fromEntries(params), ...changes }).filter(
          ([, v]) => v !== "",
        ),
      ),
    );
  }
  const data = rq.data;
  const title = silver ? "Subject-wise Silver" : "Annual NPTEL compliance";
  const suffix =
    "?" +
    new URLSearchParams({
      ...Object.fromEntries(params),
      episode: eid || "",
    }).toString();
  return (
    <>
      <PageHeader
        title={title}
        description={
          silver
            ? "Teaching obligations follow the first official assignment in each employment episode."
            : "Examination dates determine the July–June year. Each qualifying course requires independent verification."
        }
        action={
          <Link to={base + (silver ? "/annual" : "/silver") + suffix}>
            {silver ? "Annual compliance" : "Subject-wise Silver"}
          </Link>
        }
      />
      {epq.isPending ? (
        <Loading />
      ) : epq.isError ? (
        <ErrorState error={epq.error} retry={() => void epq.refetch()} />
      ) : (
        <>
          <section className="panel source-form">
            <h2>
              {scope === "personal"
                ? "Employment episodes"
                : scope === "department"
                  ? "Department records"
                  : "Institution records"}
            </h2>
            {scope !== "personal" && (
              <Field
                label="Find staff by name"
                type="search"
                value={search}
                onChange={(e) =>
                  switchFilters({
                    search: e.target.value,
                    episode: "",
                    offset: "0",
                    snapshot: "",
                  })
                }
              />
            )}
            {epq.data.total > 0 ? (
              <>
                <SelectField
                  label="Staff and employment episode"
                  value={eid || ""}
                  onChange={(e) =>
                    switchFilters({ episode: e.target.value, snapshot: "" })
                  }
                >
                  {epq.data.items.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.name} · {e.starts_on} – {e.ends_before || "current"}
                    </option>
                  ))}
                </SelectField>
                <Pager
                  offset={offset}
                  limit={20}
                  total={epq.data.total}
                  change={(v) =>
                    switchFilters({
                      offset: String(v),
                      episode: "",
                      snapshot: "",
                    })
                  }
                />
              </>
            ) : (
              <p>No faculty episodes match this selection.</p>
            )}
          </section>
          {scope !== "personal" && !itemId && (
            <ComplianceRegister scope={scope} base={base} silver={silver} />
          )}
          {eid &&
            (rq.isPending ? (
              <Loading />
            ) : rq.isError ? (
              <ErrorState error={rq.error} retry={() => void rq.refetch()} />
            ) : (
              data && (
                <>
                  <section className="panel source-form section-gap">
                    <h2>Assessment history</h2>
                    <SelectField
                      label="Report observation"
                      value={snapshot}
                      onChange={(e) =>
                        switchFilters({ snapshot: e.target.value })
                      }
                    >
                      <option value="">Latest verified evidence</option>
                      {data.snapshots.map((s) => (
                        <option key={s.id} value={s.id}>
                          {instant(s.recorded_at)}
                        </option>
                      ))}
                    </SelectField>
                    <p>
                      {data.view === "SAVED"
                        ? "Saved observation"
                        : "Latest assessment"}{" "}
                      · {instant(data.as_of)}
                    </p>
                    {scope !== "institution" && !snapshot && (
                      <button
                        disabled={cmd.isPending}
                        onClick={() =>
                          cmd.mutate({
                            path: "/compliance/snapshots?scope=" + scope,
                            body: { episode_id: eid },
                          })
                        }
                      >
                        Save current observation
                      </button>
                    )}
                    <CommandError error={cmd.error} />
                  </section>
                  <section className="panel section-gap">
                    <h2>
                      {silver
                        ? "Teaching subject obligations"
                        : "Academic years"}{" "}
                      · {data.name}
                    </h2>
                    {itemId && (
                      <Link
                        to={base + (silver ? "/silver" : "/annual") + suffix}
                      >
                        Show all {silver ? "subjects" : "years"}
                      </Link>
                    )}
                    {silver
                      ? data.silver
                          .filter((r) => !itemId || r.id === itemId)
                          .map((r) => (
                            <article className="section-gap" key={r.id}>
                              <h3>
                                <Link to={base + "/silver/" + r.id + suffix}>
                                  {r.subject}
                                </Link>
                              </h3>
                              <Badge>{words(r.status)}</Badge>
                              <p>
                                First assignment {r.first_assignment} · deadline{" "}
                                {r.deadline || "awaiting leap-day policy"} ·
                                monitoring {words(r.monitoring)}
                              </p>
                              {r.status_at_separation && (
                                <p>
                                  At separation ·{" "}
                                  {words(r.status_at_separation)}
                                </p>
                              )}
                              {r.source_reference && (
                                <p>Teaching source · {r.source_reference}</p>
                              )}
                              {itemId && <Evidence rows={r.candidates} />}
                            </article>
                          ))
                      : data.annual
                          .filter((r) => !itemId || r.id === itemId)
                          .map((r) => (
                            <article className="section-gap" key={r.id}>
                              <h3>
                                <Link to={base + "/annual/" + r.id + suffix}>
                                  {r.year}
                                </Link>
                              </h3>
                              <Badge>{words(r.status)}</Badge>
                              <p>
                                {r.starts_on} – {r.ends_on} ·{" "}
                                {words(r.obligation)} · {r.allocations.length}{" "}
                                contribution
                                {r.allocations.length === 1 ? "" : "s"}
                              </p>
                              {itemId && <Evidence rows={r.candidates} />}
                            </article>
                          ))}
                    {!(silver ? data.silver : data.annual).some(
                      (r) => !itemId || r.id === itemId,
                    ) && (
                      <p>
                        {silver
                          ? "No matching official subject obligation in this episode."
                          : "No matching configured academic year for this episode."}
                      </p>
                    )}
                  </section>
                </>
              )
            ))}
        </>
      )}
    </>
  );
}
