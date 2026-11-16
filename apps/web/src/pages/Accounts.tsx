import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { api, type Identity } from "../lib/api";
import { accessKey, command, type StaffPage } from "../lib/people";
import type { StaffSources } from "../lib/sources";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
import { CommandError, Pager } from "../components/PeopleUi";
import {
  Field,
  NoAdmin,
  SelectField,
  SourceFields,
} from "../components/SourceUi";
type AccountRequest = {
  id: string;
  email: string;
  status: string;
  reason: string;
  person_id: string | null;
  recorded_at: string;
};
export function Accounts() {
  const actor = useOutletContext<Identity>();
  const cache = useQueryClient();
  const [params, setParams] = useSearchParams();
  const offset = Math.max(0, Number(params.get("offset")) || 0);
  const [selected, setSelected] = useState<AccountRequest | null>(null);
  const [search, setSearch] = useState("");
  const [personId, setPersonId] = useState("");
  const [action, setAction] = useState("APPROVE");
  const query = useQuery({
    queryKey: ["accounts", offset, accessKey(actor)],
    queryFn: () =>
      api<{ items: AccountRequest[]; total: number }>(
        `/admin/account-requests?offset=${offset}`,
      ),
    enabled: actor.can_manage_people,
  });
  const staff = useQuery({
    queryKey: ["staff-choice", search, accessKey(actor)],
    queryFn: () =>
      api<StaffPage>(`/people/staff?q=${encodeURIComponent(search)}&limit=25`),
    enabled: actor.can_manage_people && !!selected,
  });
  const sources = useQuery({
    queryKey: ["staff-sources", personId, accessKey(actor)],
    queryFn: () => api<StaffSources>(`/people/staff/${personId}/sources`),
    enabled: actor.can_manage_people && !!personId,
  });
  const mutation = useMutation({
    mutationFn: (form: FormData) =>
      command(
        `/admin/account-requests/${selected?.id}/resolve`,
        {
          action,
          person_id: action === "APPROVE" ? personId : null,
          replace_identity_id: form.get("replace_identity_id") || null,
          source_reference: form.get("source_reference"),
          reason: form.get("reason"),
        },
        crypto.randomUUID(),
      ),
    onSuccess: () => {
      setSelected(null);
      setPersonId("");
      void cache.invalidateQueries();
    },
  });
  if (!actor.can_manage_people) return <NoAdmin />;
  return (
    <>
      <PageHeader
        title="Institutional account requests"
        description="Only genuinely verified Google identities can enter this review queue."
      />
      <section className="panel prose">
        <h2>Controlled linking</h2>
        <p>
          Approve only against an active, unambiguous institutional email record
          and authorized employment. A Google subject can never move to another
          person. Replacing a person’s current identity requires selecting the
          exact old link for revocation.
        </p>
        <p>
          For a duplicate-email case, first correct the authoritative roster. No
          account holder receives privileges from an email prefix.
        </p>
      </section>
      {selected && (
        <section className="panel prose section-gap">
          <h2>Resolve {selected.email}</h2>
          <form
            className="source-form"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate(new FormData(e.currentTarget));
            }}
          >
            <SelectField
              label="Account request decision"
              value={action}
              onChange={(e) => setAction(e.target.value)}
            >
              <option value="APPROVE">
                Approve / reconcile to approved staff
              </option>
              <option value="DENY">Deny access request</option>
            </SelectField>
            {action === "APPROVE" && (
              <>
                <Field
                  label="Find approved staff"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <SelectField
                  label="Approved staff identity"
                  required
                  value={personId}
                  onChange={(e) => setPersonId(e.target.value)}
                >
                  <option value="">Select staff</option>
                  {staff.data?.items.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.display_name} · {p.staff_key}
                    </option>
                  ))}
                </SelectField>
                <SelectField
                  label="Explicitly replace current Google link"
                  name="replace_identity_id"
                >
                  <option value="">Do not replace an existing link</option>
                  {sources.data?.identity_links
                    .filter((l) => !l.revoked_at)
                    .map((l) => (
                      <option key={l.id} value={l.id}>
                        Revoke {l.linked_email} · {l.id}
                      </option>
                    ))}
                </SelectField>
              </>
            )}
            <SourceFields />
            <CommandError error={mutation.error} />
            <button className="primary" disabled={mutation.isPending}>
              Record account decision
            </button>
            <button type="button" onClick={() => setSelected(null)}>
              Cancel review
            </button>
          </form>
        </section>
      )}
      <section className="panel section-gap">
        <div className="panel-header">
          <h2>Verified identity requests</h2>
        </div>
        {query.isPending ? (
          <Loading />
        ) : query.error ? (
          <ErrorState error={query.error} retry={() => void query.refetch()} />
        ) : (
          <>
            <ul className="record-cards">
              {query.data?.items.map((r) => (
                <li key={r.id}>
                  <strong>{r.email}</strong>
                  <Badge>{r.status}</Badge>
                  <span>{r.reason}</span>
                  {r.status === "PENDING" && (
                    <button
                      onClick={() => {
                        setSelected(r);
                        setPersonId("");
                      }}
                    >
                      Review {r.email}
                    </button>
                  )}
                </li>
              ))}
            </ul>
            {!query.data?.items.length && (
              <p className="empty-state">
                No verified account requests. An unconfigured Google provider
                does not create a request or a successful login.
              </p>
            )}
            <Pager
              total={query.data?.total ?? 0}
              offset={offset}
              limit={50}
              change={(n) => setParams({ offset: String(n) })}
            />
          </>
        )}
      </section>
    </>
  );
}
