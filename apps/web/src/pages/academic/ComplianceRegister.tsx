import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams, useOutletContext } from "react-router-dom";
import { api, type Identity } from "../../lib/api";
import { accessKey } from "../../lib/people";
import { words } from "../../lib/compliance";
import { Loading, ErrorState } from "../../components/ui";
import { Field, SelectField } from "../../components/SourceUi";
import { Pager } from "../../components/PeopleUi";
type Register = {
  total: number;
  year_id: string | null;
  years: { id: string; label: string }[];
  items: {
    episode_id: string;
    name: string;
    snapshot_id: string | null;
    coverage: string;
    records: { id: string; label: string; status: string }[];
  }[];
};
export function ComplianceRegister({
  scope,
  silver,
  base,
}: {
  scope: string;
  silver: boolean;
  base: string;
}) {
  const [params, set] = useSearchParams(),
    actor = useOutletContext<Identity>();
  const kind = silver ? "silver" : "annual",
    period = params.get("period") || "",
    cutoff = params.get("cutoff") || "",
    search = params.get("search") || "",
    offset = Number(params.get("registerOffset")) || 0;
  const qs = new URLSearchParams({
    kind,
    scope,
    search,
    offset: String(offset),
  });
  if (params.get("department")) qs.set("department", params.get("department")!);
  if (period) qs.set("year_id", period);
  if (cutoff && Number.isFinite(Date.parse(cutoff)))
    qs.set("as_of", new Date(cutoff).toISOString());
  const q = useQuery({
    queryKey: ["compliance-register", accessKey(actor), qs.toString()],
    queryFn: () => api<Register>("/compliance/register?" + qs),
  });
  function change(changes: Record<string, string>) {
    set(
      Object.fromEntries(
        Object.entries({
          ...Object.fromEntries(params),
          registerOffset: "0",
          ...changes,
        }).filter(([, v]) => v !== ""),
      ),
    );
  }
  return (
    <section className="panel source-form section-gap">
      <h2>
        {silver ? "Subject Silver register" : "Annual compliance register"}
      </h2>
      <Field
        label="Saved observations through (local time)"
        type="datetime-local"
        value={cutoff}
        onChange={(e) => change({ cutoff: e.target.value })}
      />
      {q.isPending ? (
        <Loading />
      ) : q.isError ? (
        <ErrorState error={q.error} retry={() => void q.refetch()} />
      ) : (
        <>
          {!silver && (
            <SelectField
              label="Reporting year"
              value={period || q.data.year_id || ""}
              onChange={(e) => change({ period: e.target.value })}
            >
              {q.data.years.map((y) => (
                <option key={y.id} value={y.id}>
                  {y.label}
                </option>
              ))}
            </SelectField>
          )}
          <ul className="record-cards">
            {q.data.items.map((row) => (
              <li key={row.episode_id}>
                <strong>{row.name}</strong>
                {row.records.map((r) => (
                  <Link
                    key={r.id}
                    to={
                      base +
                      "/" +
                      kind +
                      "/" +
                      r.id +
                      "?" +
                      new URLSearchParams({
                        episode: row.episode_id,
                        ...(row.snapshot_id
                          ? { snapshot: row.snapshot_id }
                          : {}),
                      })
                    }
                  >
                    {r.label} · {words(r.status)}
                  </Link>
                ))}
                {!row.records.length && (
                  <span>
                    {row.coverage === "NO_SAVED_OBSERVATION"
                      ? "No saved observation at this cutoff."
                      : "No matching obligations in this episode."}
                  </span>
                )}
              </li>
            ))}
          </ul>
          <Pager
            offset={offset}
            total={q.data.total}
            limit={20}
            change={(v) => change({ registerOffset: String(v) })}
          />
        </>
      )}
    </section>
  );
}
