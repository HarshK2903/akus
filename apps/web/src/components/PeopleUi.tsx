import type { ReactNode } from "react";
import { ApiError } from "../lib/api";
import { commandError } from "../lib/people";
export function CommandError({ error }: { error: Error | null }) {
  return error ? (
    <div className="error-box" role="alert">
      {error instanceof ApiError ? commandError(error.code) : error.message}{" "}
      Changes have not been confirmed.
    </div>
  ) : null;
}
export function ScrollTable({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="table-wrap" role="region" aria-label={label} tabIndex={0}>
      {children}
    </div>
  );
}
export function Pager({
  total,
  offset,
  limit,
  change,
}: {
  total: number;
  offset: number;
  limit: number;
  change: (offset: number) => void;
}) {
  return (
    <div className="pager">
      <span>
        {total
          ? `${offset + 1}–${Math.min(offset + limit, total)} of ${total}`
          : "No records"}
      </span>
      <button
        disabled={!offset}
        onClick={() => change(Math.max(0, offset - limit))}
      >
        Previous
      </button>
      <button
        disabled={offset + limit >= total}
        onClick={() => change(offset + limit)}
      >
        Next
      </button>
    </div>
  );
}
