import { useQuery } from "@tanstack/react-query";
import { Link, Navigate, useLocation } from "react-router-dom";
import { api, roleHome, type Identity } from "../lib/api";
import { sessionCsrf } from "../lib/session";
import { ErrorState, Loading } from "../components/ui";
const states: Record<string, [string, string]> = {
  "configuration-required": [
    "Google configuration required",
    "The operator must configure the institutional Google Web OAuth client and private session key. No Google sign-in has been completed.",
  ],
  "account-pending": [
    "Institutional account pending",
    "Google verified your identity, but no unambiguous authorized staff record is ready for linking. Contact your institution’s Admin with your staff reference. Sign in again after the roster is approved.",
  ],
  "account-not-authorized": [
    "Account not authorized",
    "This institutional access request has not been authorized. Contact your institution’s Admin for a source-record review.",
  ],
  "account-disabled": [
    "Account access disabled",
    "The staff account, employment episode or Google link is inactive. An authorized source correction is required before sign-in can succeed.",
  ],
  "duplicate-link": [
    "Account link needs reconciliation",
    "Conflicting roster records or an existing Google link prevent automatic linking. Contact your institution’s Admin. Your identity has not been moved to another staff record.",
  ],
  "consent-denied": [
    "Google sign-in was not completed",
    "Consent was denied or no authorization code was returned. You may start sign-in again when ready.",
  ],
  "provider-unavailable": [
    "Google is temporarily unavailable",
    "The institutional sign-in service could not reach Google securely. Try again later or contact your institution’s Admin.",
  ],
  "sign-in-failed": [
    "Sign-in could not be verified",
    "The sign-in attempt expired, was already used, or failed identity verification. Start a new Google sign-in. No account access was granted.",
  ],
  "contact-admin": [
    "Contact your institution’s Admin",
    "Use your institution’s established support channel and provide your staff reference and the error shown. Do not send passwords, tokens or OAuth secrets. No support address has been configured in this build.",
  ],
};
export function AuthState() {
  const path = useLocation().pathname.split("/").at(-1) ?? "sign-in-failed";
  const [title, description] = states[path] ?? states["sign-in-failed"];
  return (
    <main className="recovery-page">
      <span className="wordmark">AKUS.</span>
      <h1>{title}</h1>
      <p>{description}</p>
      <div className="record-links">
        <Link className="button primary" to="/login">
          Return to sign-in
        </Link>
        <Link to="/auth/contact-admin">Contact Admin guidance</Link>
      </div>
    </main>
  );
}
export function AuthComplete() {
  const query = useQuery({
    queryKey: ["auth-complete"],
    retry: false,
    queryFn: async () => {
      const result = await api<{ identity: Identity; csrf_token: string }>(
        "/auth/session",
      );
      sessionCsrf.set(result.csrf_token);
      return result.identity;
    },
  });
  if (query.isPending) return <Loading />;
  if (query.error)
    return (
      <ErrorState error={query.error} retry={() => void query.refetch()} />
    );
  return query.data ? (
    <Navigate to={roleHome(query.data.role)} replace />
  ) : null;
}
