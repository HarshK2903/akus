import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Link,
  useNavigate,
  useOutletContext,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { api, ApiError, type Identity } from "../lib/api";
import { sessionCsrf } from "../lib/session";
import { accessKey, instant } from "../lib/people";
import type { ImportRecord } from "../lib/sources";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
import { CommandError, Pager, ScrollTable } from "../components/PeopleUi";
import { Field, NoAdmin, SelectField } from "../components/SourceUi";
export function Imports() {
  const actor = useOutletContext<Identity>();
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const offset = Math.max(0, Number(params.get("offset")) || 0);
  const [kind, setKind] = useState("staff");
  const query = useQuery({
    queryKey: ["imports", offset, accessKey(actor)],
    queryFn: () =>
      api<{ items: ImportRecord[]; total: number }>(
        `/admin/imports?offset=${offset}`,
      ),
    enabled: actor.can_manage_people,
  });
  const upload = useMutation({
    mutationFn: async (form: FormData) => {
      const response = await fetch("/api/v1/admin/imports", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRF-Token": sessionCsrf.get() },
        body: form,
      });
      const body = await response.json();
      if (!response.ok)
        throw new ApiError(
          response.status,
          body.error?.code ?? "IMPORT_FAILED",
        );
      return body as ImportRecord;
    },
    onSuccess: (result) => navigate(`/admin/imports/${result.id}`),
  });
  if (!actor.can_manage_people) return <NoAdmin />;
  const columns =
    kind === "staff"
      ? "staff_key,display_name,department_code,starts_on,ends_before,is_faculty,email,email_valid_from"
      : "external_key,staff_key,episode_starts_on,subject_code,department_code,academic_year_start,term,starts_on,ends_before";
  return (
    <>
      <PageHeader
        title="Official source imports"
        description="Stage, inspect and explicitly commit an authorized institutional source."
      />
      <div className="overview-grid">
        <section className="panel prose">
          <h2>Upload a source file</h2>
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              upload.mutate(new FormData(e.currentTarget));
            }}
          >
            <SelectField
              label="Source type"
              name="kind"
              value={kind}
              onChange={(e) => setKind(e.target.value)}
            >
              <option value="staff">Staff roster</option>
              <option value="teaching">Teaching assignments</option>
            </SelectField>
            <Field
              label="Official source reference"
              name="source_reference"
              required
              minLength={3}
              maxLength={300}
            />
            <Field
              label="CSV or XLSX file"
              name="file"
              type="file"
              accept=".csv,.xlsx"
              required
            />
            <CommandError error={upload.error} />
            <button className="primary" disabled={upload.isPending}>
              {upload.isPending ? "Validating…" : "Upload and preview"}
            </button>
          </form>
        </section>
        <section className="panel prose">
          <h2>File requirements</h2>
          <p>
            UTF-8 CSV or one-sheet XLSX. Up to 500 data rows and 4 MB; formulas,
            macros and external workbook links are rejected.
          </p>
          <p>
            Dates use YYYY-MM-DD. Institutional email validity uses an explicit
            timestamp with timezone. Employment end dates are exclusive; blank
            means open-ended. Faculty classification must be true or false.
          </p>
          <p>Required column names:</p>
          <code className="wrap-code">{columns}</code>
          <p>
            Staff email columns are optional. Existing staff keys and teaching
            keys require a source correction, not another import. No roles are
            inferred from email addresses.
          </p>
          <p>
            {actor.mode === "LOCAL_DEMO"
              ? "LOCAL / DEMO: email fixtures must use example.test. Real institutional rosters cannot be imported in demo mode."
              : "Institutional email records require approved cmrit.ac.in source data."}
          </p>
          <p>
            Teaching acceptance remains <strong>POLICY_PENDING · IO-02</strong>.
          </p>
        </section>
      </div>
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Import history</h2>
        </div>
        {query.isPending ? (
          <Loading />
        ) : query.error ? (
          <ErrorState error={query.error} retry={() => void query.refetch()} />
        ) : (
          <>
            <ScrollTable label="Import history">
              <table>
                <thead>
                  <tr>
                    <th>File / source</th>
                    <th>Type</th>
                    <th>Rows</th>
                    <th>Status</th>
                    <th>Recorded</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data?.items.map((r) => (
                    <tr key={r.id}>
                      <td>
                        <Link to={`/admin/imports/${r.id}`}>{r.filename}</Link>
                        <small className="cell-meta">
                          {r.source_reference}
                        </small>
                      </td>
                      <td>{r.kind}</td>
                      <td>{r.row_count}</td>
                      <td>
                        <Badge>{r.status}</Badge>
                      </td>
                      <td>{instant(r.recorded_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </ScrollTable>
            <Pager
              total={query.data?.total ?? 0}
              offset={offset}
              limit={25}
              change={(n) => setParams({ offset: String(n) })}
            />
          </>
        )}
      </section>
    </>
  );
}
export function ImportDetail() {
  const actor = useOutletContext<Identity>();
  const { importId } = useParams();
  const cache = useQueryClient();
  const [confirmed, setConfirmed] = useState(false);
  const query = useQuery({
    queryKey: ["import", importId, accessKey(actor)],
    queryFn: () => api<ImportRecord>(`/admin/imports/${importId}`),
    enabled: actor.can_manage_people,
  });
  const commit = useMutation({
    mutationFn: () =>
      api<ImportRecord>(`/admin/imports/${importId}/commit`, {
        method: "POST",
        headers: { "X-CSRF-Token": sessionCsrf.get() },
        body: JSON.stringify({ confirm_authoritative_source: confirmed }),
      }),
    onSettled: () => {
      void cache.invalidateQueries();
    },
  });
  if (!actor.can_manage_people) return <NoAdmin />;
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorState error={query.error} retry={() => void query.refetch()} />
    );
  const data = query.data;
  if (!data) return null;
  return (
    <>
      <PageHeader
        title="Import preview"
        description={`${data.filename} · ${data.source_reference}`}
        action={
          <Badge tone={data.status === "COMMITTED" ? "success" : "warning"}>
            {data.status}
          </Badge>
        }
      />
      <Link to="/admin/imports">← Import history and upload</Link>
      <section className="panel prose section-gap">
        <h2>
          {data.status === "COMMITTED"
            ? "Source records committed"
            : "Review before committing"}
        </h2>
        <p>
          {data.row_count} rows · {data.error_count} rows with validation
          errors.
        </p>
        <p>
          Commit is atomic: all rows must pass. Current source facts and
          authority are checked again at commit. Correct invalid rows in the
          source file and stage a new version; this preview remains available.
        </p>
        {data.kind === "teaching" && (
          <p>
            Recording these assignments does not resolve IO-02 or award
            compliance credit.
          </p>
        )}
        <CommandError error={commit.error} />
        {data.status === "COMMITTED" ? (
          <p role="status" className="success-notice">
            Committed at {instant(data.committed_at)}. Safe retries will not
            duplicate these records.
          </p>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              commit.mutate();
            }}
          >
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              I confirm these are authorized official source records.
            </label>
            <button
              className="primary"
              disabled={!confirmed || data.error_count > 0 || commit.isPending}
            >
              {commit.isPending ? "Committing…" : "Commit validated import"}
            </button>
          </form>
        )}
      </section>
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Row-level preview</h2>
        </div>
        <ScrollTable label="Import rows">
          <table>
            <thead>
              <tr>
                <th>Line</th>
                <th>Source fields</th>
                <th>Validation</th>
              </tr>
            </thead>
            <tbody>
              {data.rows?.map((row) => (
                <tr key={row.line}>
                  <td>{row.line}</td>
                  <td>
                    <dl className="import-fields">
                      {Object.entries(row.raw).map(([key, value]) => (
                        <div key={key}>
                          <dt>{key.replaceAll("_", " ")}</dt>
                          <dd>{value || "—"}</dd>
                        </div>
                      ))}
                    </dl>
                    <details>
                      <summary>Normalized record</summary>
                      <pre>{JSON.stringify(row.normalized, null, 2)}</pre>
                    </details>
                  </td>
                  <td>
                    {row.errors.length ? (
                      <ul className="error-text">
                        {row.errors.map((error) => (
                          <li key={error}>{error.replaceAll("_", " ")}</li>
                        ))}
                      </ul>
                    ) : (
                      <Badge tone="success">Validated</Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </ScrollTable>
      </section>
    </>
  );
}
