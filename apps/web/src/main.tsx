import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider, createBrowserRouter } from "react-router-dom";
import { WorkspaceLoading } from "./components/ui";
import { routes } from "./routes";
import "./styles.css";
const router = createBrowserRouter(routes);
const client = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 10000 } },
});
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      <React.Suspense fallback={<WorkspaceLoading />}>
        <RouterProvider router={router} />
      </React.Suspense>
    </QueryClientProvider>
  </React.StrictMode>,
);
