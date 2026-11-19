import {
  AttemptList,
  AttemptDetail,
  NewAttempt,
} from "./pages/academic/Outcomes";
import {
  ExceptionDetail,
  ExceptionList,
  OfficeAlerts,
} from "./pages/academic/Exceptions";
import React from "react";
import {
  Applications,
  ApplicationDraft,
  ApplicationDetail,
} from "./pages/academic/Applications";
import {
  Catalog,
  CourseDetail,
  CourseForm,
  OfferingDetail,
  ProviderSources,
} from "./pages/academic/Catalog";
import {
  Topics,
  MappingList,
  MappingDetail,
  QuotaList,
  QuotaDetail,
} from "./pages/academic/Governance";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "./components/Shell";
import { Login } from "./pages/Login";
import { RoleDashboard, AcademicIntegration } from "./pages/Dashboards";
import { Imports, ImportDetail } from "./pages/Imports";
import { ReferenceSetup } from "./pages/ReferenceSetup";
import { TeachingList, TeachingDetail, TeachingForm } from "./pages/Teaching";
import { SourceCorrection } from "./pages/SourceCorrection";
import { Accounts } from "./pages/Accounts";
import { AuthComplete, AuthState } from "./pages/AuthState";
import { Overview } from "./pages/Overview";
import { StaffRecord } from "./pages/StaffRecord";
import { StaffDirectory } from "./pages/StaffDirectory";
import { StaffNew } from "./pages/StaffNew";
import { AppointmentRecord } from "./pages/AppointmentRecord";
import { Appointments } from "./pages/Appointments";
import { AppointmentNew } from "./pages/AppointmentNew";
import { Help } from "./pages/Help";
import { Recovery } from "./pages/Recovery";
import "./styles.css";
const client = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 10000 } },
});
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route element={<Shell />}>
            <Route path="/app/home" element={<RoleDashboard />} />
            <Route
              path="/drc/home"
              element={<RoleDashboard role="DRC_HEAD" />}
            />
            <Route path="/hod/home" element={<RoleDashboard role="HOD" />} />
            <Route
              path="/principal/home"
              element={<RoleDashboard role="PRINCIPAL" />}
            />
            <Route
              path="/admin/home"
              element={<RoleDashboard role="ADMIN" />}
            />
            <Route
              path="/hod/integrity"
              element={<ExceptionList kind="integrity" />}
            />
            <Route
              path="/hod/integrity/:caseId"
              element={<ExceptionDetail kind="integrity" />}
            />
            <Route
              path="/hod/separation-cases"
              element={<ExceptionList kind="separation" />}
            />
            <Route
              path="/hod/separation-cases/:caseId"
              element={<ExceptionDetail kind="separation" />}
            />
            <Route
              path="/app/review-office-alerts"
              element={<OfficeAlerts />}
            />
            <Route path="/app/system" element={<Overview />} />
            <Route path="/app/previous-attempts" element={<AttemptList />} />
            <Route
              path="/app/previous-attempts/new/:offeringId"
              element={<NewAttempt />}
            />
            <Route
              path="/app/previous-attempts/:attemptId"
              element={<AttemptDetail />}
            />
            <Route
              path="/hod/outcome-verifications"
              element={<AttemptList inbox />}
            />
            <Route
              path="/hod/outcome-verifications/:attemptId"
              element={<AttemptDetail inbox />}
            />
            <Route path="/app/catalog" element={<Catalog />} />
            <Route path="/app/catalog/:courseId" element={<CourseDetail />} />
            <Route
              path="/app/offerings/:offeringId"
              element={<OfferingDetail />}
            />
            <Route path="/admin/catalog/new" element={<CourseForm />} />
            <Route path="/admin/nptel-sync" element={<ProviderSources />} />
            <Route
              path="/admin/nptel-offerings"
              element={<ProviderSources versions />}
            />
            <Route path="/hod/topics" element={<Topics />} />
            <Route path="/hod/topics/:topicId" element={<Topics />} />
            <Route path="/hod/topic-mappings" element={<MappingList />} />
            <Route
              path="/hod/topic-mappings/requests"
              element={<MappingList requests />}
            />
            <Route
              path="/hod/topic-mappings/:courseId"
              element={<MappingDetail />}
            />
            <Route
              path="/hod/topic-mappings/:courseId/edit"
              element={<MappingDetail editing />}
            />
            <Route path="/hod/quotas/new" element={<QuotaDetail creating />} />
            <Route path="/hod/quotas/:poolId" element={<QuotaDetail />} />
            <Route
              path="/hod/quotas/:poolId/edit"
              element={<QuotaDetail editing />}
            />
            <Route
              path="/hod/quotas/:poolId/ledger"
              element={<QuotaDetail ledger />}
            />
            {[
              "/app/teaching",
              "/people/teaching",
              "/hod/teaching",
              "/principal/teaching",
              "/admin/teaching",
            ].map((path) => (
              <Route key={path} path={path} element={<TeachingList />} />
            ))}
            <Route
              path="/people/teaching/:teachingId"
              element={<TeachingDetail />}
            />
            <Route path="/admin/teaching/new" element={<TeachingForm />} />
            <Route
              path="/admin/teaching/:teachingId/correct"
              element={<TeachingForm />}
            />
            <Route path="/admin/imports" element={<Imports />} />
            <Route path="/admin/imports/:importId" element={<ImportDetail />} />
            <Route path="/admin/reference" element={<ReferenceSetup />} />
            <Route path="/people/reference" element={<ReferenceSetup />} />
            <Route
              path="/admin/teaching-assignments"
              element={<TeachingList />}
            />
            <Route
              path="/admin/academic-reference"
              element={<ReferenceSetup />}
            />
            <Route
              path="/admin/academic-years"
              element={<ReferenceSetup initialKind="year" />}
            />
            <Route path="/admin/accounts" element={<Accounts />} />
            <Route
              path="/admin/staff/:staffId/sources"
              element={<SourceCorrection />}
            />
            <Route path="/app/applications" element={<Applications />} />
            <Route
              path="/app/compliance"
              element={<AcademicIntegration area="compliance" />}
            />
            <Route path="/drc/reviews" element={<Applications review />} />
            <Route path="/hod/reviews" element={<Applications review />} />
            <Route path="/hod/quotas" element={<QuotaList />} />
            <Route
              path="/app/applications/new/*"
              element={<ApplicationDraft />}
            />
            {["offering", "eligibility", "evidence", "review"].map((step) => (
              <Route
                key={step}
                path={`/app/applications/new/${step}`}
                element={<ApplicationDraft />}
              />
            ))}
            <Route
              path="/app/applications/:appId"
              element={<ApplicationDetail />}
            />
            <Route
              path="/app/applications/:appId/quota"
              element={<ApplicationDetail />}
            />
            <Route
              path="/app/applications/:appId/history"
              element={<ApplicationDetail />}
            />
            <Route
              path="/app/applications/:appId/evidence"
              element={<ApplicationDetail />}
            />
            <Route
              path="/app/participation/:appId"
              element={<ApplicationDetail />}
            />
            <Route path="/drc/reviews/:appId" element={<ApplicationDetail />} />
            <Route path="/hod/reviews/:appId" element={<ApplicationDetail />} />
            <Route
              path="/hod/quota-transfers"
              element={<Applications reconciliation />}
            />
            <Route
              path="/hod/quota-transfers/:caseId"
              element={<ApplicationDetail caseView />}
            />
            <Route
              path="/principal/reports"
              element={<AcademicIntegration area="reports" />}
            />
            <Route path="/app/profile" element={<StaffRecord own />} />
            <Route path="/admin/staff" element={<StaffDirectory />} />
            <Route path="/people/staff" element={<StaffDirectory />} />
            <Route path="/admin/staff/new" element={<StaffNew />} />
            <Route path="/admin/staff/:staffId" element={<StaffRecord />} />
            <Route path="/people/staff/:staffId" element={<StaffRecord />} />
            <Route
              path="/admin/staff/:staffId/employment"
              element={<SourceCorrection />}
            />
            <Route path="/admin/appointments" element={<Appointments />} />
            <Route path="/people/appointments" element={<Appointments />} />
            <Route
              path="/admin/appointments/new"
              element={<AppointmentNew />}
            />
            <Route
              path="/admin/appointments/:appointmentId"
              element={<AppointmentRecord />}
            />
            <Route
              path="/people/appointments/:appointmentId"
              element={<AppointmentRecord />}
            />
            <Route path="/app/help" element={<Help />} />
          </Route>
          <Route path="/auth/complete" element={<AuthComplete />} />
          <Route path="/auth/*" element={<AuthState />} />
          <Route path="*" element={<Recovery />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
