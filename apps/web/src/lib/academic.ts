import { useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { api } from "./api";
import { command } from "./people";

export type Event = {
  id: string;
  kind: string;
  recorded_at: string;
  data: Record<string, unknown>;
};
export type Context = {
  home_department_id: string;
  can_source: boolean;
  can_apply: boolean;
  hod_departments: string[];
  departments: { id: string; name: string; code: string }[];
  topics: { id: string; code: string; name: string }[];
  years: { id: string; label: string; starts_on: string }[];
};
export type Metadata = {
  title: string;
  description: string;
  categories: string[];
  duration_weeks: number | null;
  starts_on: string | null;
  ends_on: string | null;
  enrollment_ends_on: string | null;
  exam_registration_ends_on: string | null;
  scheduled_exam_on: string | null;
  timezone: string;
  precision: string;
};
export type Pool = {
  id: string;
  department_id: string;
  topic_id: string;
  topic: string;
  academic_year_id: string;
  academic_year: string;
  maximum: number;
  occupied: number;
  available: number | null;
  status: string;
  version: number;
  history?: Event[];
  allocations?: {
    application_id: string;
    applicant: string;
    state: string;
    allocation_state: string;
  }[];
  ledger?: Movement[];
  reconciliation?: {
    stored_count: number;
    counted_allocations: number;
    ledger_balance: number;
    matches_current: boolean | null;
    as_of: string | null;
  };
  visibility?: string;
};
export type Offering = {
  id: string;
  course_id: string;
  provider_id: string;
  version: number;
  source_status: string;
  snapshot_id: string | null;
  metadata: Metadata | null;
  source_url: string | null;
  observed_at: string | null;
  trust: string | null;
  fresh: boolean;
  department_id: string;
  mapping_revision_id: string | null;
  mapping_version: number | null;
  topic_id: string | null;
  topic: string | null;
  expected_exam_year: string | null;
  quota: Pool | null;
  blockers: string[];
  course?: Course;
  observations?: {
    id: string;
    metadata: Metadata;
    observed_at: string;
    source_url: string;
    trust: string;
    digest: string;
  }[];
  history?: Event[];
  fetches?: { status: string; error: string | null; observed_at: string }[];
};
export type Course = {
  id: string;
  code: string;
  title: string;
  description: string;
  source_reference: string;
  version: number;
  offerings: Offering[];
  history?: Event[];
};
export type Topic = {
  id: string;
  code: string;
  name: string;
  version: number;
  source_reference: string;
  aliases: { label: string; source_reference: string }[];
  history: Event[];
};
export type Mapping = {
  course: Course;
  department_id: string;
  version: number;
  revisions: {
    id: string;
    version: number;
    topic_id: string;
    topic: string;
    snapshot_id: string;
    valid_from: string;
    valid_until: string | null;
    reason: string;
    source_reference: string;
    office_id: string;
  }[];
  candidates: {
    snapshot_id: string;
    provider_id: string;
    categories: string[];
    topic_ids: string[];
    source_url: string;
    observed_at: string;
  }[];
  history: Event[];
  existing_allocation_policy: string;
};

export function useContextData() {
  return useQuery({
    queryKey: ["academic-context"],
    queryFn: () => api<Context>("/nptel/context"),
    staleTime: 0,
  });
}
export function useDepartment(context?: Context) {
  const [params, setParams] = useSearchParams();
  const department =
    params.get("department") ||
    context?.hod_departments[0] ||
    context?.home_department_id ||
    "";
  return {
    department,
    params,
    setParams,
    choose: (value: string) =>
      setParams((previous) => {
        const next = new URLSearchParams(previous);
        next.set("department", value);
        return next;
      }),
  };
}
export function useCommand(onSuccess?: (id: string) => void) {
  const cache = useQueryClient();
  const retry = useRef<{ signature: string; key: string } | null>(null);
  return useMutation({
    mutationFn: ({ path, body }: { path: string; body: unknown }) => {
      const signature = path + JSON.stringify(body);
      if (retry.current?.signature !== signature)
        retry.current = { signature, key: crypto.randomUUID() };
      return command(path, body, retry.current.key);
    },
    onSuccess: (data) => {
      void cache.invalidateQueries();
      onSuccess?.(data.id);
    },
  });
}
export const reasonFields = (form: FormData) => ({
  source_reference: String(form.get("source_reference") ?? ""),
  reason: String(form.get("reason") ?? ""),
});

export type Movement = {
  id: string;
  movement_id: string;
  application_id: string;
  pool_id: string;
  delta: number;
  kind: string;
  snapshot_id: string;
  recorded_at: string;
};
export type ApplicationRecord = {
  actual_exam?: string;
  annual_compliance?: string;
  participation?: ParticipationRecord;
  draft_revisions?: {
    version: number;
    recorded_at: string;
    declarations: Record<string, unknown>;
  }[];
  id: string;
  person_id: string;
  applicant: string;
  course: string;
  course_id: string;
  offering_id: string;
  provider_id: string;
  department_id: string;
  state: string;
  version: number;
  next_office: string | null;
  submitted_at: string | null;
  enrollment_deadline_passed: boolean;
  can_review: boolean;
  own: boolean;
  source_eligible: boolean;
  personal_schedule: {
    id: string;
    version: number;
    scheduled_exam_on: string;
    source_reference: string;
    document_digest: string;
    observed_at: string;
    verified_at: string;
    verification: string;
  } | null;
  allocation: { state: string; version: number; pool: Pool } | null;
  declarations: {
    academic_relevance?: string;
    score_sharing_yes: boolean;
    not_yet_enrolled: boolean;
    prior_attempt: string;
    emerging_technology_exception: boolean;
    acknowledgement: boolean;
  };
  offering: Offering;
  submission: {
    original_pool_id: string;
    submitted_at: string;
    facts: {
      academic_year: string;
      route: string[];
      metadata: Metadata;
      trust: string;
      topic_id: string;
    };
  } | null;
  cases: {
    id: string;
    kind: string;
    status: string;
    reason: string;
    context: Record<string, unknown>;
    updated_at: string;
  }[];
  ledger: Movement[];
  history: Event[];
  notifications: {
    kind: string;
    facts: Record<string, unknown>;
    created_at: string;
  }[];
};

export type EnrollmentEvidence = {
  id: string;
  version: number;
  enrolled_at: string | null;
  enrolled_on: string | null;
  source_reference: string;
  document_digest: string;
  observed_at: string;
  recorded_at: string;
  reason: string;
  outcome?: string;
  chronology?: string;
  claim_id?: string;
};
export type ParticipationRecord = {
  claim_version: number;
  finding_version: number;
  claims: EnrollmentEvidence[];
  findings: EnrollmentEvidence[];
  verified_submission_first: boolean;
  pending_withdrawal: {
    id: string;
    reason: string;
    source_reference: string;
    recorded_at: string;
  } | null;
};
