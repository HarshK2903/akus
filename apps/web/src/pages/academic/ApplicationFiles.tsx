import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { api, type Identity } from "../../lib/api";
import { accessKey, instant } from "../../lib/people";
import { reasonFields, useCommand } from "../../lib/academic";
import { preparePdf } from "../../lib/pdf";
import { ErrorState, Loading, Badge } from "../../components/ui";
import { CommandError, Pager } from "../../components/PeopleUi";
import { SourceFields } from "../../components/SourceUi";

type Revision = {
  id: string;
  series_id: string;
  version: number;
  kind: string;
  filename: string;
  source_reference: string;
  reason: string;
  digest: string;
  size_bytes: number;
  scan: string;
  recorded_at: string;
  current: boolean;
  submitted: boolean;
  can_download: boolean;
};
type Files = {
  can_upload: boolean;
  can_remove: boolean;
  application_version: number;
  total: number;
  items: Revision[];
};
export function ApplicationFiles({ aid }: { aid: string }) {
  const actor = useOutletContext<Identity>(),
    [params, setParams] = useSearchParams();
  const offset = Math.max(0, Number(params.get("fileOffset")) || 0);
  const path = "/applications/" + aid + "/attachments";
  const q = useQuery({
    queryKey: ["application-files", ...accessKey(actor), aid, offset],
    queryFn: () => api<Files>(path + "?offset=" + offset),
  });
  const action = useCommand();
  const [busy, setBusy] = useState(false),
    [problem, setProblem] = useState("");
  return (
    <section
      className="panel prose section-gap"
      aria-label="Private application files"
    >
      <h2>Application attachments</h2>
      {q.isPending ? (
        <Loading />
      ) : q.error ? (
        <ErrorState error={q.error} retry={() => void q.refetch()} />
      ) : (
        <>
          {q.data.can_upload && (
            <details>
              <summary>Add or replace a PDF</summary>
              <form
                className="source-form"
                onSubmit={async (e) => {
                  e.preventDefault();
                  const form = e.currentTarget;
                  const f = new FormData(form);
                  setProblem("");
                  setBusy(true);
                  try {
                    const file = f.get("file");
                    if (!(file instanceof File))
                      throw new Error("Choose a PDF.");
                    const pdf = await preparePdf(file);
                    await action.mutateAsync({
                      path,
                      body: {
                        expected_version: q.data.application_version,
                        previous_id: f.get("previous_id") || null,
                        kind: f.get("kind"),
                        filename: file.name,
                        document_digest: pdf.digest,
                        attachment: pdf.attachment,
                        ...reasonFields(f),
                      },
                    });
                    form.reset();
                  } catch (err) {
                    setProblem(
                      err instanceof Error ? err.message : "Upload failed.",
                    );
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                <label>
                  Evidence purpose
                  <select name="kind">
                    {[
                      "ACADEMIC_RELEVANCE",
                      "ENROLLMENT",
                      "SCHEDULE",
                      "PRIOR_RESULT",
                      "OTHER",
                    ].map((k) => (
                      <option key={k} value={k}>
                        {k.replaceAll("_", " ").toLowerCase()}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Revision to replace
                  <select name="previous_id">
                    <option value="">New attachment</option>
                    {q.data.items
                      .filter((r) => r.current)
                      .map((r) => (
                        <option key={r.id} value={r.id}>
                          {r.filename} · version {r.version}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  Application PDF (up to 2 MiB)
                  <input
                    type="file"
                    accept="application/pdf"
                    name="file"
                    required
                  />
                </label>
                <p>
                  Files await a clean scan before download. Uploading a file
                  records an assertion. Independent verification follows the
                  applicable evidence workflow.
                </p>
                <SourceFields />
                <button
                  className="button primary"
                  disabled={busy || action.isPending}
                >
                  Save attachment
                </button>
              </form>
            </details>
          )}
          {!q.data.total && <p>No application files recorded.</p>}
          {q.data.items.map((r) => (
            <details key={r.id} className="section-gap">
              <summary>
                {r.filename} · version {r.version} · {r.scan.toLowerCase()}
              </summary>
              <p>
                <Badge>
                  {r.current ? "Current revision" : "Historical revision"}
                </Badge>{" "}
                {r.submitted && "Included in original submission"}
              </p>
              <dl>
                <dt>Purpose</dt>
                <dd>{r.kind.replaceAll("_", " ").toLowerCase()}</dd>
                <dt>Recorded</dt>
                <dd>{instant(r.recorded_at)}</dd>
                <dt>Size</dt>
                <dd>{r.size_bytes} bytes</dd>
                <dt>Source</dt>
                <dd>{r.source_reference}</dd>
                <dt>Reason</dt>
                <dd>{r.reason}</dd>
                <dt>SHA-256</dt>
                <dd className="wrap-anywhere">{r.digest}</dd>
              </dl>
              {r.can_download && (
                <a href={"/api/v1" + path + "/" + r.id + "/content"}>
                  Download PDF
                </a>
              )}
              {q.data.can_remove && r.current && (
                <form
                  className="source-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    action.mutate({
                      path: path + "/" + r.id + "/remove",
                      body: {
                        ...reasonFields(new FormData(e.currentTarget)),
                        expected_version: q.data.application_version,
                      },
                    });
                  }}
                >
                  <SourceFields />
                  <button disabled={action.isPending}>Remove from draft</button>
                </form>
              )}
            </details>
          ))}
          {q.data.total > 25 && (
            <Pager
              total={q.data.total}
              limit={25}
              offset={offset}
              change={(n) =>
                setParams({
                  ...Object.fromEntries(params),
                  fileOffset: String(n),
                })
              }
            />
          )}
          {action.isSuccess && <p role="status">Attachment history saved.</p>}
          <CommandError error={action.error} />
          {problem && !action.error && <p role="alert">{problem}</p>}
        </>
      )}
    </section>
  );
}
