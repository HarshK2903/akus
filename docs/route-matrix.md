# Complete page / route / role / API inventory

Source-generated; planned contracts are not implemented APIs. Phase status is tracked in traceability.md.

| Page | Route | Roles | Contract source line | Planned API |
|---|---|---|---|---|
| PUB-01 · Institutional sign-in | `/login` | All unauthed | 291 | GET /auth/login |
| PUB-02 · OAuth return | `/auth/callback` | Authenticated redirect | 303 | GET /auth/google/callback |
| PUB-03 · Access denied / not provisioned | `/access-denied` | All | 315 | GET /me |
| PUB-04 · Service unavailable | `/system-unavailable` | All | 327 | GET /health |
| PUB-05 · Not found | `/not-found` | All | 339 | Router + server resource lookup |
| SHR-01 · Task inbox | `/app/tasks` | F,D,H,P(R),A(scope) | 351 | GET /tasks |
| SHR-02 · Notifications | `/app/notifications` | F,D,H,P,A | 363 | GET /me/notifications |
| SHR-03 · Profile and authority | `/app/profile` | F,D,H,P,A | 375 | GET /me /me/roles |
| SHR-04 · Help and policy glossary | `/app/help` | F,D,H,P,A | 387 | GET /policy/help |
| SHR-05 · Global search | `/app/search` | F,D,H,P,A | 399 | GET /search |
| FAC-01 · Faculty overview | `/app/home` | F,D | 411 | GET /dashboard/faculty |
| FAC-02 · NPTEL course catalog | `/app/catalog` | F,D,H(R),P(R) | 423 | GET /nptel/courses |
| FAC-03 · Canonical course detail | `/app/catalog/:courseId` | F,D,H(R),P(R) | 435 | GET /nptel/courses/{id} |
| FAC-04 · Exact NPTEL offering | `/app/offerings/:offeringId` | F,D,H(R),P(R) | 447 | GET /nptel/offerings/{id} |
| FAC-05 · Application drafts and applications | `/app/applications` | F,D,H(R),P(R) | 459 | GET /applications |
| FAC-06 · New application — offering | `/app/applications/new/offering` | F,D | 471 | GET /nptel/offerings + POST /applications/drafts |
| FAC-07 · New application — eligibility | `/app/applications/new/eligibility` | F,D | 483 | PATCH /applications/drafts/{id} |
| FAC-08 · New application — evidence | `/app/applications/new/evidence` | F,D | 495 | POST /evidence + PATCH /drafts |
| FAC-09 · New application — review and submit | `/app/applications/new/review` | F,D | 507 | POST /applications/{id}/submit |
| FAC-10 · Application detail | `/app/applications/:applicationId` | F,D,H(scope),P(R) | 519 | GET /applications/{id} |
| FAC-11 · Application quota and movements | `/app/applications/:applicationId/quota` | F,D,H(scope),P(R) | 531 | GET /applications/{id}/quota-transfer-history |
| FAC-12 · Application evidence | `/app/applications/:applicationId/evidence` | F,D,H(scope),P(R) | 543 | GET /applications/{id}/evidence |
| FAC-13 · Application timeline and audit | `/app/applications/:applicationId/history` | F,D,H(scope),P(R) | 555 | GET /applications/{id}/timeline |
| FAC-14 · External participation evidence | `/app/participation/:applicationId` | F,D,H(scope),P(R) | 567 | POST /applications/{id}/enrollment-evidence /exam-evidence |
| FAC-15 · Prior attempts and repeat eligibility | `/app/previous-attempts` | F,D | 579 | GET /previous-attempts |
| FAC-16 · Prior-result verification request | `/app/previous-attempts/:attemptId` | F,D,H(scope) | 591 | POST /outcome-verifications |
| FAC-17 · Annual compliance overview | `/app/compliance/annual` | F,D,H(R),P(R) | 603 | GET /compliance/annual |
| FAC-18 · Annual academic year detail | `/app/compliance/annual/:yearId` | F,D,H(R),P(R) | 615 | GET /compliance/annual/{year} |
| FAC-19 · Subject-wise Silver list | `/app/compliance/silver` | F,D,H(R),P(R) | 627 | GET /compliance/silver |
| FAC-20 · Silver subject obligation detail | `/app/compliance/silver/:obligationId` | F,D,H(scope),P(R) | 639 | GET /compliance/silver/{id} |
| FAC-21 · Certificate library | `/app/certificates` | F,D,H(R),P(R) | 651 | GET /certificates |
| DRC-01 · DRC review queue | `/drc/reviews` | D | 663 | GET /reviews?stage=drc |
| DRC-02 · DRC application review | `/drc/reviews/:taskId` | D | 675 | GET/POST /reviews/{id} |
| DRC-03 · DRC decision history | `/drc/history` | D | 687 | GET /reviews/history |
| HOD-01 · Department overview | `/hod/home` | H | 699 | GET /dashboard/hod |
| HOD-02 · Final approval queue | `/hod/reviews` | H | 711 | GET /reviews?stage=hod |
| HOD-03 · Final decision workspace | `/hod/reviews/:taskId` | H | 723 | POST /reviews/{id}/decision |
| HOD-04 · Primary topic mappings | `/hod/topic-mappings` | H | 735 | GET /departments/{id}/topic-mappings |
| HOD-05 · Topic mapping requests | `/hod/topic-mappings/requests` | H | 747 | GET /departments/{id}/primary-topic-mapping-requests |
| HOD-06 · Mapping detail and revisions | `/hod/topic-mappings/:courseId` | H | 759 | GET /departments/{id}/.../history |
| HOD-07 · Approve or revise mapping | `/hod/topic-mappings/:courseId/edit` | H | 771 | POST /.../approve or /revise |
| HOD-08 · Canonical topic directory | `/hod/topics` | H,A(reference),P(R) | 783 | GET /nptel/topics |
| HOD-09 · Annual quota pools | `/hod/quotas` | H | 795 | GET /departments/{id}/quotas |
| HOD-10 · Quota pool detail | `/hod/quotas/:poolId` | H | 807 | GET /quotas/{id} |
| HOD-11 · Publish/revise annual quota | `/hod/quotas/:poolId/edit` | H | 819 | POST/PATCH /.../quota |
| HOD-12 · Quota allocation ledger | `/hod/quotas/:poolId/ledger` | H,P(R) | 831 | GET /quotas/{id}/ledger |
| HOD-13 · Quota transfer case inbox | `/hod/quota-transfers` | H | 843 | GET /quota-transfer-cases |
| HOD-14 · Quota transfer case detail | `/hod/quota-transfers/:caseId` | H,P(R) | 855 | GET/POST /quota-transfer-cases/{id} |
| HOD-15 · Prior-result verification inbox | `/hod/outcome-verifications` | H | 867 | GET /outcome-verifications |
| HOD-16 · Prior-result decision | `/hod/outcome-verifications/:caseId` | H | 879 | POST /outcome-verifications/{id}/decision |
| HOD-17 · Integrity-review inbox | `/hod/integrity` | H,P(R) | 891 | GET /integrity-cases |
| HOD-18 · Integrity-review detail | `/hod/integrity/:caseId` | H,P(R) | 903 | GET/POST /integrity-cases/{id} |
| HOD-19 · Separation-closure inbox | `/hod/separation-cases` | H | 915 | GET /separation-cases |
| HOD-20 · Separation chronology case | `/hod/separation-cases/:caseId` | H | 927 | POST /separation-cases/{id}/decision |
| HOD-21 · Department annual report | `/hod/reports/annual` | H,P(R) | 939 | GET /reports/annual |
| HOD-22 · Department Silver report | `/hod/reports/silver` | H,P(R) | 951 | GET /reports/silver |
| HOD-23 · Department application report | `/hod/reports/applications` | H,P(R) | 963 | GET /reports/applications |
| HOD-24 · HoD decision history | `/hod/decisions` | H | 975 | GET /decisions |
| PRN-01 · Institution overview | `/principal/home` | P | 987 | GET /dashboard/principal |
| PRN-02 · Departments overview | `/principal/departments` | P | 999 | GET /departments/overview |
| PRN-03 · Department drilldown | `/principal/departments/:departmentId` | P | 1011 | GET /departments/{id}/overview |
| PRN-04 · Institution-wide applications | `/principal/applications` | P | 1023 | GET /applications?scope=institution |
| PRN-05 · Institution topic quotas and mappings | `/principal/topics-quotas` | P | 1035 | GET /reports/topics-quotas |
| PRN-06 · Institution annual compliance | `/principal/reports/annual` | P | 1047 | GET /reports/institution/annual |
| PRN-07 · Institution Silver compliance | `/principal/reports/silver` | P | 1059 | GET /reports/institution/silver |
| PRN-08 · Institution exception monitoring | `/principal/exceptions` | P | 1071 | GET /reports/exceptions |
| PRN-09 · Institution audit and as-of reporting | `/principal/audit` | P | 1083 | GET /audit |
| ADM-01 · Administration overview | `/admin/home` | A | 1095 | GET /dashboard/admin |
| ADM-02 · Staff directory | `/admin/staff` | A | 1107 | GET/POST /admin/staff |
| ADM-03 · Staff detail | `/admin/staff/:staffId` | A | 1119 | GET /admin/staff/{id} |
| ADM-04 · Employment episodes | `/admin/staff/:staffId/employment` | A | 1131 | GET/POST /admin/employment |
| ADM-05 · Office appointments | `/admin/appointments` | A | 1143 | GET/POST /admin/appointments |
| ADM-06 · Teaching assignments | `/admin/teaching-assignments` | A | 1155 | GET/POST /admin/teaching-assignments |
| ADM-07 · Departments and canonical subjects | `/admin/academic-reference` | A | 1167 | GET/POST /admin/reference |
| ADM-08 · Academic years | `/admin/academic-years` | A | 1179 | GET/POST /admin/academic-years |
| ADM-09 · NPTEL provider synchronization | `/admin/nptel-sync` | A | 1191 | GET/POST /admin/nptel-sync |
| ADM-10 · Provider metadata versions | `/admin/nptel-offerings` | A | 1203 | GET /admin/nptel-offerings |
| ADM-11 · Work-ledger operations | `/admin/operations` | A | 1215 | GET/POST /admin/operations |
| ADM-12 · Notifications configuration | `/admin/notifications` | A | 1227 | GET/POST /admin/notifications |
| ADM-13 · Administrative audit | `/admin/audit` | A | 1239 | GET /admin/audit |
