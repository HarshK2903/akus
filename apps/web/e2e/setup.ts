import { request, type FullConfig } from "@playwright/test";
// Recover only the explicitly fictional temporary office left by an interrupted
// version of this suite. Normal API commands preserve appointment and audit history.
export default async function setup(config: FullConfig) {
  const baseURL = String(config.projects[0].use.baseURL);
  const api = await request.newContext({
    baseURL,
    extraHTTPHeaders: { Origin: baseURL },
  });
  try {
    const response = await api.post("/api/v1/auth/demo-login", {
      data: { identity_key: "admin" },
    });
    if (!response.ok())
      throw new Error("E2E requires the explicit LOCAL/DEMO environment");
    const session = await response.json();
    for (let offset = 0; ; offset += 100) {
      const response = await api.get(
        `/api/v1/people/appointments?limit=100&offset=${offset}`,
      );
      const list = await response.json();
      for (const item of list.items) {
        if (
          item.source_reference === "LOCAL_E2E_TEMPORARY_OFFICE" &&
          item.person_name === "Mira Rao" &&
          item.status === "CURRENT"
        ) {
          const result = await api.post(
            `/api/v1/admin/appointments/${item.id}/end`,
            {
              headers: {
                "X-CSRF-Token": session.csrf_token,
                "Idempotency-Key": crypto.randomUUID(),
              },
              data: {
                expected_version: item.version,
                reason:
                  "LOCAL_E2E_RECOVERY: close temporary fixture left by interrupted browser verification",
              },
            },
          );
          if (!result.ok())
            throw new Error(
              "Unable to restore temporary E2E fixture authority",
            );
        }
      }
      if (offset + 100 >= list.total) break;
    }
  } finally {
    await api.dispose();
  }
}
