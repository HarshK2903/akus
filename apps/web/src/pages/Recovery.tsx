import { useQuery } from "@tanstack/react-query";
import { Link, useLocation } from "react-router-dom";
import { api } from "../lib/api";
import { Badge } from "../components/ui";
export function Recovery() {
  const path = useLocation().pathname;
  const status = useQuery({
    queryKey: ["public-health"],
    queryFn: () => api<{ status: string }>("/health/ready"),
    enabled: path === "/system-unavailable",
    retry: false,
  });
  const title =
    path === "/access-denied"
      ? "Access is not available"
      : path === "/system-unavailable"
        ? "Service availability"
        : path === "/auth/callback"
          ? "Institutional sign-in is not configured"
          : "Page not found";
  return (
    <main className="recovery">
      <span className="wordmark">AKUS.</span>
      <h1>{title}</h1>
      <p>
        {path === "/auth/callback"
          ? "No Google identity has been authenticated. Use the clearly marked local demo entry."
          : "This route is unavailable in your current workspace. Return to sign-in to continue."}
      </p>
      {path === "/system-unavailable" && (
        <p>
          <Badge>
            {status.data?.status ??
              (status.isPending ? "Checking…" : "Unavailable")}
          </Badge>{" "}
          <button onClick={() => void status.refetch()}>
            Retry health check
          </button>
        </p>
      )}
      <Link className="button primary" to="/login">
        Return to sign-in
      </Link>
    </main>
  );
}
