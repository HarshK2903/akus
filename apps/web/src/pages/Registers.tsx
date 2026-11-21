import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Link,
  useOutletContext,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
import { Pager, ScrollTable, CommandError } from "../components/PeopleUi";
import { api, type Identity } from "../lib/api";
import { instant, accessKey } from "../lib/people";
import { type Context, useCommand } from "../lib/academic";
import { sessionCsrf } from "../lib/session";
import { registers, type Register } from "../lib/registers";

type Row = {
  id: string;
  title: string;
  context: string;
  status: string;
  recorded_at: string | null;
  href: string | null;
  attempts?: number;
};
type RegisterPage = {
  items: Row[];
  total: number;
  initial_filter?: string;
  counts?: Record<string, number>;
};
type Version = {
  id: string;
  version: number;
  heading: string;
  reason: string;
  recorded_at: string;
};
type Settings = { default_heading: string; versions: Version[] };
const withPool = ["applications", "department-applications", "topics-quotas"];
const privateViews = ["tasks", "notifications", "operations", "search"];
const pretty = (s: string) => s.replaceAll("_", " ").toLowerCase();
function SettingsPage() {
  const actor = useOutletContext<Identity>();
  const q = useQuery({
    queryKey: ["notice-templates", ...accessKey(actor)],
    queryFn: () => api<Settings>("/admin/notification-settings"),
  });
  const save = useCommand();
  const send = useCommand();
  const current = q.data?.versions[0];
  return (
    <>
      <PageHeader
        title="Notification settings"
        description="Versioned in-app headings for application owners. Changes apply to future notices."
      />
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorState error={q.error} retry={() => void q.refetch()} />
      ) : (
        <>
          <section className="panel">
            <h2>Application updates</h2>
            <p>Channel · Personal in-app inbox</p>
            <form
              key={current?.id ?? "initial"}
              className="source-form"
              onSubmit={(e) => {
                e.preventDefault();
                const f = new FormData(e.currentTarget);
                save.mutate({
                  path: "/admin/notification-settings",
                  body: {
                    heading: f.get("heading"),
                    reason: f.get("reason"),
                    expected_version: current?.version ?? 0,
                  },
                });
              }}
            >
              <label>
                Notification heading
                <input
                  name="heading"
                  defaultValue={current?.heading ?? q.data.default_heading}
                  maxLength={100}
                  required
                />
              </label>
              <label>
                Reason for change
                <input name="reason" maxLength={500} required />
              </label>
              <button className="button primary" disabled={save.isPending}>
                Save template version
              </button>
            </form>
            <CommandError error={save.error} />
            {save.isSuccess && <p role="status">Template version saved.</p>}
            <button
              disabled={send.isPending}
              onClick={() =>
                send.mutate({
                  path: "/admin/notification-settings/test",
                  body: {},
                })
              }
            >
              Send preview to my inbox
            </button>
            {send.isSuccess && (
              <p role="status">
                Preview delivered.{" "}
                <Link to="/app/notifications">Open my notifications</Link>
              </p>
            )}
            <CommandError error={send.error} />
          </section>
          <section className="panel">
            <h2>Version history</h2>
            {!q.data.versions.length ? (
              <p>No edited versions.</p>
            ) : (
              <ol>
                {q.data.versions.map((v) => (
                  <li key={v.id}>
                    Version {v.version} · {v.heading} · {instant(v.recorded_at)}
                    <p>{v.reason}</p>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </>
      )}
    </>
  );
}

async function download(report: string, filters: Record<string, string>) {
  const response = await fetch("/api/v1/registers/" + report + "/export", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRF-Token": sessionCsrf.get(),
    },
    body: JSON.stringify(filters),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(pretty(err.error?.code ?? "EXPORT_FAILED"));
  }
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = "akus-" + report + ".csv";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function Listing({ report }: { report: Exclude<Register, "settings"> }) {
  const actor = useOutletContext<Identity>(),
    cache = useQueryClient();
  const { departmentId } = useParams(),
    [params, setParams] = useSearchParams();
  const [selected, setSelected] = useState<string | null>(null);
  const [, title, description] = registers[report];
  const offset = Math.max(0, Math.floor(Number(params.get("offset")) || 0));
  const filters: Record<string, string> = {};
  for (const k of [
    "search",
    "status",
    "department",
    "year",
    "topic",
    "since",
    "until",
  ])
    if (params.get(k)) filters[k] = params.get(k)!;
  if (departmentId) filters.department = departmentId;
  const set = (k: string, v: string) => {
    const next = new URLSearchParams(params);
    next.delete("offset");
    if (v) next.set(k, v);
    else next.delete(k);
    setSelected(null);
    setParams(next);
  };
  const filterDepartment =
    !!departmentId ||
    [
      "departments",
      "department-applications",
      "applications",
      "topics-quotas",
      "exceptions",
      "audit",
      "search",
    ].includes(report);
  const ctx = useQuery({
    queryKey: ["register-context", ...accessKey(actor)],
    queryFn: () => api<Context>("/nptel/context"),
    enabled: filterDepartment,
  });
  const inbox = report === "notifications";
  const query = new URLSearchParams({ ...filters, offset: String(offset) });
  const q = useQuery({
    queryKey: ["register", report, ...accessKey(actor), query.toString()],
    queryFn: () => api<RegisterPage>("/registers/" + report + "?" + query),
  });
  const health = useQuery({
    queryKey: ["worker-health", ...accessKey(actor)],
    queryFn: () => api<{ seen_at: string | null }>("/admin/worker-health"),
    enabled: report === "operations",
    refetchInterval: 30000,
  });
  const act = useCommand();
  const preference = useMutation({
    mutationFn: (initial_filter: string) =>
      api("/notifications/preference", {
        method: "POST",
        headers: { "X-CSRF-Token": sessionCsrf.get() },
        body: JSON.stringify({ initial_filter }),
      }),
    onSuccess: () =>
      void cache.invalidateQueries({ queryKey: ["register", "notifications"] }),
  });
  const csv = useMutation({ mutationFn: () => download(report, filters) });
  const dept = ctx.data?.departments.find((d) => d.id === departmentId);
  const row = q.data?.items.find((r) => r.id === selected);
  return (
    <>
      <PageHeader
        title={departmentId ? (dept?.name ?? "Department detail") : title}
        description={
          departmentId
            ? "Department applications and related oversight registers."
            : description
        }
        action={
          !privateViews.includes(report) && (
            <button
              disabled={!q.data || csv.isPending}
              onClick={() => csv.mutate()}
            >
              Export CSV
            </button>
          )
        }
      />
      <CommandError error={csv.error} />
      {departmentId && (
        <nav aria-label="Department reports" className="academic-links">
          {(
            ["departments", "topics-quotas", "exceptions", "audit"] as const
          ).map((r) => (
            <Link key={r} to={registers[r][0] + "?department=" + departmentId}>
              {registers[r][1]}
            </Link>
          ))}
          <Link to={"/principal/reports/annual?department=" + departmentId}>
            Annual compliance
          </Link>
          <Link to={"/principal/reports/silver?department=" + departmentId}>
            Subject-wise Silver
          </Link>
        </nav>
      )}
      {report === "operations" && (
        <section className="panel">
          <h2>Worker heartbeat</h2>
          {health.error ? (
            <ErrorState
              error={health.error}
              retry={() => void health.refetch()}
            />
          ) : health.isPending ? (
            <Loading />
          ) : (
            <p>
              {health.data?.seen_at
                ? instant(health.data.seen_at)
                : "Awaiting first heartbeat"}
            </p>
          )}
        </section>
      )}
      <section className="panel">
        <form
          key={params.toString()}
          className="source-form"
          onSubmit={(e) => {
            e.preventDefault();
            const form = new FormData(e.currentTarget);
            const next = new URLSearchParams(params);
            next.delete("offset");
            for (const [k, value] of form) {
              let v = String(value).trim();
              if (v && ["since", "until"].includes(k))
                v = new Date(v).toISOString();
              if (v) next.set(k, v);
              else next.delete(k);
            }
            setSelected(null);
            setParams(next);
          }}
        >
          <label>
            Search records
            <input
              type="search"
              name="search"
              defaultValue={filters.search}
              maxLength={160}
            />
          </label>
          {inbox || report === "search" || report === "topics-quotas" ? (
            <label>
              {report === "search" ? "Result type" : "Status"}
              <select
                aria-label={report === "search" ? "Result type" : "Status"}
                name="status"
                defaultValue={filters.status ?? (inbox ? "DEFAULT" : "")}
              >
                <option value={inbox ? "DEFAULT" : ""}>
                  {inbox ? "My default view" : "All"}
                </option>
                {(inbox
                  ? ["ALL", "UNREAD", "READ"]
                  : report === "search"
                    ? [
                        "COURSE",
                        "OFFERING",
                        "DOCUMENT",
                        "TOPIC",
                        "STAFF",
                        "APPLICATION",
                      ]
                    : ["CURRENT", "DRAFT", "PUBLISHED"]
                ).map((v) => (
                  <option key={v} value={v}>
                    {pretty(v)}
                  </option>
                ))}
              </select>
            </label>
          ) : (
            <label>
              Status or decision
              <input
                name="status"
                defaultValue={filters.status}
                maxLength={60}
              />
            </label>
          )}
          {filterDepartment && !departmentId && (
            <label>
              Department
              <select name="department" defaultValue={filters.department}>
                <option value="">All permitted departments</option>
                {ctx.data?.departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          {(withPool.includes(report) || report === "departments") && (
            <>
              <label>
                Academic year
                <select name="year" defaultValue={filters.year}>
                  <option value="">All years</option>
                  {ctx.data?.years.map((y) => (
                    <option key={y.id} value={y.id}>
                      {y.label}
                    </option>
                  ))}
                </select>
              </label>
              {report !== "departments" && (
                <label>
                  Charging topic
                  <select name="topic" defaultValue={filters.topic}>
                    <option value="">All topics</option>
                    {ctx.data?.topics.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </label>
              )}
            </>
          )}
          {["audit", "source-audit", "hod-history", "drc-history"].includes(
            report,
          ) &&
            ["since", "until"].map((k) => (
              <label key={k}>
                {k === "since" ? "Recorded after" : "Recorded through"}
                <input
                  type="datetime-local"
                  name={k}
                  defaultValue={
                    filters[k] && Number.isFinite(Date.parse(filters[k]))
                      ? new Date(
                          Date.parse(filters[k]) -
                            new Date(filters[k]).getTimezoneOffset() * 60000,
                        )
                          .toISOString()
                          .slice(0, 16)
                      : ""
                  }
                />
              </label>
            ))}
          <button className="button primary">Apply filters</button>
        </form>
        {ctx.error && (
          <ErrorState error={ctx.error} retry={() => void ctx.refetch()} />
        )}
        {inbox && q.data && (
          <label>
            Default inbox view
            <select
              value={q.data.initial_filter}
              disabled={preference.isPending}
              onChange={(e) => preference.mutate(e.target.value)}
            >
              <option value="ALL">All notices</option>
              <option value="UNREAD">Unread only</option>
            </select>
          </label>
        )}
        <CommandError error={preference.error} />
      </section>
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorState error={q.error} retry={() => void q.refetch()} />
      ) : (
        <section className="panel">
          <h2>
            {departmentId
              ? "Applications"
              : report === "search"
                ? "Search results"
                : "Records"}
          </h2>
          {q.data.counts && (
            <p>
              {Object.entries(q.data.counts)
                .map(([v, n]) => pretty(v) + " " + n)
                .join(" · ")}
            </p>
          )}
          {q.data.items.length ? (
            <ScrollTable label={title + " results"}>
              <table>
                <thead>
                  <tr>
                    <th>Record</th>
                    <th>Context</th>
                    <th>Status</th>
                    <th>Recorded</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {q.data.items.map((r) => (
                    <tr key={r.id}>
                      <td>
                        {r.href ? <Link to={r.href}>{r.title}</Link> : r.title}
                      </td>
                      <td>{r.context || "—"}</td>
                      <td>
                        <Badge>{pretty(r.status)}</Badge>
                      </td>
                      <td>{r.recorded_at ? instant(r.recorded_at) : "—"}</td>
                      <td>
                        <button
                          aria-label={"Inspect " + r.title}
                          onClick={() => setSelected(r.id)}
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </ScrollTable>
          ) : (
            <p>
              {report === "search" && !filters.search
                ? "Enter a search term to find accessible records."
                : "No records match this view."}
            </p>
          )}
          <Pager
            total={q.data.total}
            limit={25}
            offset={offset}
            change={(o) => set("offset", String(o))}
          />
          {row && (
            <section className="panel" aria-label="Selected record">
              <h3>{row.title}</h3>
              <p>{row.context}</p>
              <p>Record ID · {row.id}</p>
              {row.href && <Link to={row.href}>Open associated record</Link>}
              {inbox && row.status === "UNREAD" && (
                <button
                  disabled={act.isPending}
                  onClick={() =>
                    act.mutate({
                      path: "/notifications/" + row.id + "/read",
                      body: {},
                    })
                  }
                >
                  Mark read
                </button>
              )}
              {report === "operations" &&
                row.status === "DEAD" &&
                ["QUOTA_RECHECK", "PROVIDER_REFRESH", "OFFICE_INBOX"].includes(
                  row.title,
                ) && (
                  <form
                    className="source-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      act.mutate({
                        path: "/admin/work/" + row.id + "/retry",
                        body: {
                          expected_attempts: row.attempts,
                          reason: new FormData(e.currentTarget).get("reason"),
                        },
                      });
                    }}
                  >
                    <label>
                      Retry reason
                      <input name="reason" maxLength={500} required />
                    </label>
                    <button disabled={act.isPending}>Retry job</button>
                  </form>
                )}
            </section>
          )}
          <CommandError error={act.error} />
          {act.isSuccess && <p role="status">Change recorded.</p>}
        </section>
      )}
    </>
  );
}

export function WorkspaceRegister({ report }: { report: Register }) {
  return report === "settings" ? (
    <SettingsPage />
  ) : (
    <Listing key={report} report={report} />
  );
}
