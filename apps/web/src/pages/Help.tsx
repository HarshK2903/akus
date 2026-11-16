import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { Search } from "lucide-react";
import { api } from "../lib/api";
import type { Policy } from "../lib/api";
import { Badge, ErrorState, Loading, PageHeader } from "../components/ui";
export function Help() {
  const [params, setParams] = useSearchParams();
  const search = params.get("q") ?? "";
  const policies = useQuery({
    queryKey: ["policy-help"],
    queryFn: () => api<Policy[]>("/policy/help"),
  });
  const visible = policies.data?.filter((p) =>
    `${p.title} ${p.summary} ${p.id}`
      .toLowerCase()
      .includes(search.toLowerCase()),
  );
  return (
    <>
      <PageHeader
        title="Policy guide"
        description="Approved rules and open decisions, kept visibly distinct. Based on the binding V2.4 specification."
      />
      <div className="help-toolbar">
        <label htmlFor="policy-search">Find a policy or term</label>
        <div className="search-field">
          <Search size={17} />
          <input
            id="policy-search"
            value={search}
            placeholder="Try quota, Silver or HoD…"
            onChange={(e) =>
              setParams(e.target.value ? { q: e.target.value } : {}, {
                replace: true,
              })
            }
          />
        </div>
      </div>
      {policies.isPending ? (
        <Loading />
      ) : policies.error ? (
        <ErrorState
          error={policies.error}
          retry={() => void policies.refetch()}
        />
      ) : (
        <div className="help-layout">
          <aside className="help-index">
            <strong>IN THIS GUIDE</strong>
            {visible?.map((p) => (
              <a key={p.id} href={`#${p.id}`}>
                {p.title}
              </a>
            ))}
          </aside>
          <div className="policy-articles">
            {visible?.length === 0 && (
              <div className="panel prose">
                <h2>No matching policies</h2>
                <p>
                  Try another term or{" "}
                  <button onClick={() => setParams({})}>
                    clear your search
                  </button>
                  .
                </p>
              </div>
            )}
            {visible?.map((p) => (
              <article id={p.id} className="panel policy-article" key={p.id}>
                <div className="article-meta">
                  <span>{p.id}</span>
                  <Badge
                    tone={p.status === "POLICY_PENDING" ? "warning" : "neutral"}
                  >
                    {p.status === "POLICY_PENDING"
                      ? "Policy pending"
                      : "Confirmed"}
                  </Badge>
                </div>
                <h2>{p.title}</h2>
                <p>{p.summary}</p>
              </article>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
