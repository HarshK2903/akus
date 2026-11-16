import type { components } from "./schema";
export type Identity = components["schemas"]["Identity"];
export type Foundation = components["schemas"]["Foundation"];
export type Year = components["schemas"]["Year"];
export type Policy = components["schemas"]["PolicyHelp"];
export type AuthConfig = components["schemas"]["AuthConfig"];
export type LoginResult = components["schemas"]["LoginResult"];
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    public correlationId?: string,
  ) {
    super(code.replaceAll("_", " ").toLowerCase());
  }
}
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      body.error?.code ?? "SERVICE_UNAVAILABLE",
      body.error?.correlation_id,
    );
  }
  return response.status === 204
    ? (undefined as T)
    : (response.json() as Promise<T>);
}
export const roleLabels: Record<string, string> = {
  STAFF: "Staff",
  FACULTY: "Faculty",
  DRC_HEAD: "DRC Head",
  HOD: "HoD",
  PRINCIPAL: "Principal",
  ADMIN: "Admin",
};
export const roleHome = (role: string) =>
  ({
    DRC_HEAD: "/drc/home",
    HOD: "/hod/home",
    PRINCIPAL: "/principal/home",
    ADMIN: "/admin/home",
  })[role] ?? "/app/home";
