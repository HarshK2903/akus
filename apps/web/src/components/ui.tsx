import type { ReactNode } from "react";
import { AlertCircle, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { ApiError } from "../lib/api";
export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <>
      <div className="breadcrumbs">
        Workspace <ChevronRight size={12} />
        <span>{title}</span>
      </div>
      <div className="page-header">
        <div>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        {action}
      </div>
    </>
  );
}
export function Loading() {
  return (
    <div className="loading" role="status">
      Loading current records…
    </div>
  );
}
export function ErrorState({
  error,
  retry,
}: {
  error: Error;
  retry: () => void;
}) {
  return (
    <div className="error-box" role="alert">
      <AlertCircle size={20} />
      <div>
        <h2>Unable to load this information</h2>
        <p>{error.message}. Your action has not been confirmed.</p>
        {error instanceof ApiError && error.correlationId && (
          <small>Reference: {error.correlationId}</small>
        )}
        <div>
          <button onClick={retry}>Try again</button>{" "}
          <Link to="/login">Return to sign-in</Link>
        </div>
      </div>
    </div>
  );
}
export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning";
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
