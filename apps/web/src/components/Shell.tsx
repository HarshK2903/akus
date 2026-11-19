import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Navigate,
  NavLink,
  Outlet,
  useNavigate,
  useLocation,
} from "react-router-dom";
import * as Dialog from "@radix-ui/react-dialog";
import {
  BookOpen,
  LayoutDashboard,
  LogOut,
  Menu,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";
import { api, roleHome, roleLabels } from "../lib/api";
import type { Identity } from "../lib/api";
import { sessionCsrf } from "../lib/session";
import { ApiError } from "../lib/api";
import { ErrorState, Loading } from "./ui";
export function Shell() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const cache = useQueryClient();
  const me = useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const identity = await api<Identity>("/me");
      if (identity.mode === "INSTITUTIONAL") {
        const session = await api<{ csrf_token: string }>("/auth/session");
        sessionCsrf.set(session.csrf_token);
      }
      return identity;
    },
    retry: false,
    refetchOnWindowFocus: true,
    refetchInterval: 15000,
  });
  const logout = useMutation({
    mutationFn: () =>
      api<void>("/auth/logout", {
        method: "POST",
        headers: { "X-CSRF-Token": sessionCsrf.get() },
      }),
    onSuccess: () => {
      sessionCsrf.clear();
      cache.clear();
      navigate("/login");
    },
  });
  if (me.isPending) return <Loading />;
  if (me.error instanceof ApiError && [401, 404].includes(me.error.status))
    return (
      <Navigate
        to={`/login?return_to=${encodeURIComponent(location.pathname + location.search)}`}
        replace
      />
    );
  if (me.error instanceof ApiError && [403, 423].includes(me.error.status))
    return <Navigate to="/access-denied" replace />;
  if (me.error)
    return <ErrorState error={me.error} retry={() => void me.refetch()} />;
  if (!me.data) return null;
  const person = me.data;
  const nav = (
    <>
      <div className="nav-group-label">WORKSPACE</div>
      <nav aria-label="Main navigation">
        <NavLink to={roleHome(person.role)} onClick={() => setOpen(false)}>
          <LayoutDashboard size={18} />
          Overview
        </NavLink>
        <NavLink to="/app/catalog" onClick={() => setOpen(false)}>
          <BookOpen size={18} />
          Course catalog
        </NavLink>
        {person.roles?.some((r) =>
          ["HOD", "PRINCIPAL", "ADMIN"].includes(r),
        ) && (
          <NavLink
            to="/app/review-office-alerts"
            onClick={() => setOpen(false)}
          >
            <BookOpen size={18} />
            Review office alerts
          </NavLink>
        )}
        {person.roles?.some((r) => r === "HOD" || r === "PRINCIPAL") && (
          <>
            <NavLink to="/hod/separation-cases" onClick={() => setOpen(false)}>
              <BookOpen size={18} />
              Separation cases
            </NavLink>
            <NavLink to="/hod/integrity" onClick={() => setOpen(false)}>
              <ShieldCheck size={18} />
              Integrity reviews
            </NavLink>
          </>
        )}
        {person.applicant_eligible && (
          <NavLink to="/app/previous-attempts" onClick={() => setOpen(false)}>
            <BookOpen size={18} />
            My prior attempts
          </NavLink>
        )}
        {person.roles?.includes("HOD") && (
          <>
            <NavLink
              to="/hod/outcome-verifications"
              onClick={() => setOpen(false)}
            >
              <BookOpen size={18} />
              Prior-result verification
            </NavLink>
            <NavLink to="/hod/topic-mappings" onClick={() => setOpen(false)}>
              <BookOpen size={18} />
              Topic mappings
            </NavLink>
            <NavLink to="/hod/quotas" onClick={() => setOpen(false)}>
              <BookOpen size={18} />
              Annual quotas
            </NavLink>
          </>
        )}
        <NavLink to="/app/profile" onClick={() => setOpen(false)}>
          <UserRound size={18} />
          Profile & access
        </NavLink>
        <NavLink to="/app/help" onClick={() => setOpen(false)}>
          <BookOpen size={18} />
          Policy guide
        </NavLink>
        {person.can_read_directory && (
          <NavLink
            to={person.can_manage_people ? "/admin/staff" : "/people/staff"}
            onClick={() => setOpen(false)}
          >
            <UserRound size={18} />
            Staff directory
          </NavLink>
        )}
        {person.can_read_directory && (
          <NavLink
            to={
              person.can_manage_people
                ? "/admin/appointments"
                : "/people/appointments"
            }
            onClick={() => setOpen(false)}
          >
            <ShieldCheck size={18} />
            Office appointments
          </NavLink>
        )}
        <NavLink to="/people/teaching" onClick={() => setOpen(false)}>
          <BookOpen size={18} />
          Teaching allocations
        </NavLink>
        {person.can_manage_people && (
          <>
            <NavLink to="/admin/imports" onClick={() => setOpen(false)}>
              <BookOpen size={18} />
              Source imports
            </NavLink>
            <NavLink to="/admin/reference" onClick={() => setOpen(false)}>
              <BookOpen size={18} />
              Reference setup
            </NavLink>
            <NavLink to="/admin/accounts" onClick={() => setOpen(false)}>
              <ShieldCheck size={18} />
              Account requests
            </NavLink>
            <NavLink to="/admin/nptel-sync" onClick={() => setOpen(false)}>
              <BookOpen size={18} />
              NPTEL provider sources
            </NavLink>
          </>
        )}
      </nav>
      <div className="nav-note">
        <ShieldCheck size={20} />
        <strong>Accountable academic decisions</strong>
        <p>
          Source evidence, current authority and immutable history guide each
          decision.
        </p>
        <span>AKUS · INSTITUTIONAL RECORDS</span>
      </div>
    </>
  );
  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="topbar">
        <div className="brand">
          <span className="wordmark">
            AKUS<span className="brand-dot">.</span>
          </span>
          <span className="brand-product">NPTEL</span>
        </div>
        <span className="environment-tag">
          {person.mode === "LOCAL_DEMO" ? "LOCAL / DEMO" : "INSTITUTIONAL"}
        </span>
        <div className="top-account">
          <span>
            {person.name}
            <small>{roleLabels[person.role]}</small>
          </span>
          <span className="avatar">
            {person.name
              .split(" ")
              .slice(0, 2)
              .map((s) => s[0])
              .join("")}
          </span>
        </div>
        <Dialog.Root open={open} onOpenChange={setOpen}>
          <Dialog.Trigger asChild>
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
            >
              <Menu size={20} />
            </button>
          </Dialog.Trigger>
          <Dialog.Portal>
            <Dialog.Overlay className="nav-overlay" />
            <Dialog.Content className="mobile-nav">
              <Dialog.Title>AKUS navigation</Dialog.Title>
              <Dialog.Description>
                Open your local workspace pages.
              </Dialog.Description>
              <Dialog.Close asChild>
                <button
                  className="icon-button close-nav"
                  aria-label="Close navigation"
                >
                  <X />
                </button>
              </Dialog.Close>
              {nav}
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </header>
      <aside className="sidebar">
        {nav}
        <button
          className="signout"
          onClick={() => logout.mutate()}
          disabled={logout.isPending}
        >
          <LogOut size={17} />
          {logout.isPending ? "Signing out…" : "Sign out"}
        </button>
      </aside>
      <div className="app-body">
        {person.mode === "LOCAL_DEMO" && (
          <div
            className="demo-banner"
            role="region"
            aria-label="Local demonstration notice"
          >
            <span className="demo-dot" />
            Local demonstration{" "}
            <span className="banner-detail">
              Fictional identities. Provider observations are labeled
              separately; no verified enrollment or certificate is implied.
            </span>
          </div>
        )}
        <main id="main-content" tabIndex={-1}>
          {logout.error && (
            <p role="alert" className="error-text">
              Sign out failed: {logout.error.message}. Sign in again to renew
              the demo session.
            </p>
          )}
          <Outlet context={person} />
          <button className="mobile-signout" onClick={() => logout.mutate()}>
            Sign out
          </button>
        </main>
        <footer className="app-footer">
          <span>AKUS · NPTEL participation & compliance</span>
          <span>Evidence · Authority · History</span>
        </footer>
      </div>
    </>
  );
}
