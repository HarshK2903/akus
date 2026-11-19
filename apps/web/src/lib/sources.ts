export type Reference = {
  id: string;
  code: string;
  name: string;
  version: number;
  source_reference?: string;
};
export type References = {
  departments: Reference[];
  subjects: Reference[];
  aliases: {
    id: string;
    alias: string;
    version: number;
    subject_id: string;
    source_reference: string;
  }[];
  years: {
    id: string;
    label: string;
    starts_on: string;
    ends_on: string;
    source: string;
  }[];
};
export type Revision = {
  id: string;
  entity_type?: string;
  before: Record<string, unknown> | null;
  after: Record<string, unknown>;
  context: Record<string, string>;
  recorded_at: string;
};
export type Teaching = {
  id: string;
  external_key: string;
  person_id: string;
  staff_name: string;
  episode_id: string;
  subject_id: string;
  subject: string;
  department_id: string;
  department: string;
  academic_year_id: string;
  academic_year: string;
  term: string;
  starts_on: string;
  ends_before: string;
  source_reference: string;
  voided: boolean;
  version: number;
  recorded_at: string;
  first_official_date: string | null;
  provisional_deadline: string | null;
  acceptance: string;
  deadline_policy: string;
  compliance: string;
  status_at_separation: string | null;
  episode_closed: boolean;
  history?: Revision[];
};
export type ImportRecord = {
  id: string;
  kind: string;
  filename: string;
  source_reference: string;
  status: string;
  recorded_at: string;
  committed_at: string | null;
  row_count: number;
  error_count: number;
  rows?: {
    line: number;
    raw: Record<string, string>;
    normalized: Record<string, unknown>;
    errors: string[];
  }[];
};
export type SourceRecord = {
  id: string;
  source_version: number;
  [key: string]: unknown;
};
export type StaffSources = {
  person: SourceRecord;
  episodes: SourceRecord[];
  memberships: SourceRecord[];
  emails: SourceRecord[];
  offices: SourceRecord[];
  history: Revision[];
  identity_links: {
    id: string;
    linked_email: string;
    revoked_at: string | null;
  }[];
};
