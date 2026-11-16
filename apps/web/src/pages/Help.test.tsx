import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Help } from "./Help";
afterEach(() => vi.unstubAllGlobals());
function show() {
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <MemoryRouter>
        <Help />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
describe("policy help", () => {
  it("keeps unresolved decisions visibly pending and searches real API records", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => [
          {
            id: "P-51",
            title: "One Silver certificate across subjects",
            status: "POLICY_PENDING",
            summary: "Await an institutional decision.",
          },
        ],
      }),
    );
    show();
    expect(await screen.findByText("Policy pending")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Find a policy or term"), {
      target: { value: "no match" },
    });
    expect(screen.getByText("No matching policies")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "clear your search" }));
    expect(
      screen.getByRole("heading", {
        name: "One Silver certificate across subjects",
      }),
    ).toBeInTheDocument();
  });
  it("reports failure without fabricated policy records", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ error: { code: "DATABASE_UNAVAILABLE" } }),
      }),
    );
    show();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to load",
    );
    expect(screen.queryByText("Confirmed")).not.toBeInTheDocument();
  });
});
