import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, LockKeyhole } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, roleHome, roleLabels } from "../lib/api";
import type { AuthConfig, Identity, LoginResult } from "../lib/api";
import { sessionCsrf } from "../lib/session";
import { ErrorState, Loading } from "../components/ui";
export function Login() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const cache = useQueryClient();
  const [key, setKey] = useState("faculty");
  const config = useQuery({
    queryKey: ["auth-config"],
    queryFn: () => api<AuthConfig>("/auth/config"),
  });
  const people = useQuery({
    queryKey: ["demo-identities"],
    queryFn: () => api<Identity[]>("/auth/demo-identities"),
    enabled: config.data?.demo_enabled === true,
  });
  const login = useMutation({
    mutationFn: () =>
      api<LoginResult>("/auth/demo-login", {
        method: "POST",
        body: JSON.stringify({ identity_key: key }),
      }),
    onSuccess: (data) => {
      cache.clear();
      sessionCsrf.set(data.csrf_token);
      cache.setQueryData(["me"], data.identity);
      navigate(roleHome(data.identity.role));
    },
  });
  return (
    <main className="login-layout">
      <div className="login-brand">
        <span className="wordmark">
          AKUS<span className="brand-dot">.</span>
        </span>
        <span>NPTEL participation & compliance</span>
      </div>
      <section className="login-panel">
        <div className="eyebrow">INSTITUTIONAL WORKSPACE</div>
        <h1>
          A clear record.
          <br />
          Every step of the way.
        </h1>
        <p className="lead">
          Your faculty development, academic reviews and compliance, in one
          accountable workspace.
        </p>
        <div className="login-divider" />
        <h2>Sign in to AKUS</h2>
        <p>{config.data?.institution_label ?? "Institutional access"}</p>
        <button
          className="sso"
          disabled={!config.data?.google_enabled}
          aria-describedby="google-status"
          onClick={() => {
            window.location.assign(
              `/api/v1/auth/google/begin?return_to=${encodeURIComponent(params.get("return_to") ?? "/auth/complete")}`,
            );
          }}
        >
          <LockKeyhole size={17} /> Continue with Google
        </button>
        <p className="small" id="google-status">
          {config.data?.google_enabled
            ? "Use your verified cmrit.ac.in Workspace account. Institutional records determine access."
            : "CONFIGURATION REQUIRED · Institutional Google sign-in is not configured."}
        </p>
        <div className="demo-signin">
          <span className="eyebrow">LOCAL / DEMO ONLY</span>
          <p>
            Explore with a fictional identity. This is not institutional
            authentication.
          </p>
          {config.isPending ? (
            <Loading />
          ) : config.error ? (
            <ErrorState
              error={config.error}
              retry={() => void config.refetch()}
            />
          ) : !config.data?.demo_enabled ? (
            <p>Local demo access is disabled.</p>
          ) : people.isPending ? (
            <Loading />
          ) : people.error ? (
            <ErrorState
              error={people.error}
              retry={() => void people.refetch()}
            />
          ) : (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                login.mutate();
              }}
            >
              <label htmlFor="identity">Demo identity</label>
              <select
                id="identity"
                value={key}
                onChange={(event) => setKey(event.target.value)}
              >
                {people.data?.map((person) => (
                  <option key={person.key} value={person.key}>
                    {person.name} · {roleLabels[person.role]}
                  </option>
                ))}
              </select>
              <button
                className="primary full"
                disabled={login.isPending || !people.data?.length}
              >
                {login.isPending
                  ? "Starting session…"
                  : "Enter local workspace"}
                <ArrowRight size={17} />
              </button>
            </form>
          )}
          {login.error && (
            <p role="alert" className="error-text">
              Sign-in failed: {login.error.message}
            </p>
          )}
        </div>
        <p className="login-footnote">
          People & access · Institutional source authority
          <br />
          AKUS does not enroll you on NPTEL or verify certificates
          automatically.
        </p>
      </section>
      <footer>Automated Knowledge Upgrade System</footer>
    </main>
  );
}
