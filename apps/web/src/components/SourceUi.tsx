import { useId } from "react";
import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";
import { Badge } from "./ui";
import { instant } from "../lib/people";
import type { Revision } from "../lib/sources";
export function Field({
  label,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  const id = useId();
  return (
    <div className="source-field">
      <label htmlFor={id}>{label}</label>
      <input id={id} {...props} />
    </div>
  );
}
export function SelectField({
  label,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  children: ReactNode;
}) {
  const id = useId();
  return (
    <div className="source-field">
      <label htmlFor={id}>{label}</label>
      <select id={id} {...props}>
        {children}
      </select>
    </div>
  );
}
export function SourceFields() {
  return (
    <>
      <Field
        label="Official source reference"
        name="source_reference"
        required
        minLength={3}
        maxLength={300}
      />
      <label className="source-field">
        Reason for this source change
        <textarea
          name="reason"
          required
          minLength={5}
          maxLength={1000}
          rows={3}
        />
      </label>
    </>
  );
}
export function SourceHistory({ history }: { history: Revision[] }) {
  return (
    <section className="panel section-gap">
      <div className="panel-header">
        <h2>Source revision history</h2>
        <Badge>Immutable · latest 100</Badge>
      </div>
      {history.length ? (
        <ol className="source-timeline">
          {history.map((r) => (
            <li key={r.id}>
              <strong>
                {r.before ? "Source correction" : "Source recorded"}
              </strong>
              <time>{instant(r.recorded_at)}</time>
              <p>{r.context.reason}</p>
              <details>
                <summary>View recorded facts</summary>
                <dl className="revision-facts">
                  {Object.entries(r.after)
                    .filter(
                      ([k]) =>
                        !["demo_identity_id", "office_group"].includes(k),
                    )
                    .map(([k, v]) => (
                      <div key={k}>
                        <dt>{k.replaceAll("_", " ")}</dt>
                        <dd>
                          {r.before &&
                            JSON.stringify(r.before[k]) !==
                              JSON.stringify(v) && (
                              <del>
                                {String(r.before[k] ?? "Open-ended")} →{" "}
                              </del>
                            )}
                          {String(v ?? "Open-ended")}
                        </dd>
                      </div>
                    ))}
                </dl>
              </details>
            </li>
          ))}
        </ol>
      ) : (
        <p className="empty-state">No recorded revisions.</p>
      )}
    </section>
  );
}
export function NoAdmin() {
  return (
    <div className="error-box" role="alert">
      <h1>Administration access required</h1>
      <p>Your current source records do not grant this action.</p>
    </div>
  );
}
