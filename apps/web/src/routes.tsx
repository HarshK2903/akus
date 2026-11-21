import React from "react";

import { createRoutesFromElements, Navigate, Route } from "react-router-dom";
import { Shell } from "./components/Shell";
import { Login } from "./pages/Login";

import { AuthComplete, AuthState } from "./pages/AuthState";
import { Overview } from "./pages/Overview";

import { Help } from "./pages/Help";
import { Recovery } from "./pages/Recovery";
import { registers, type Register } from "./lib/registers";
const WorkspaceRegister = React.lazy(() =>
  import("./pages/Registers").then((m) => ({ default: m.WorkspaceRegister })),
);
const EmploymentHistory = React.lazy(() =>
  import("./pages/academic/EmploymentHistory").then((m) => ({
    default: m.EmploymentHistory,
  })),
);
const CertificateLibrary = React.lazy(() =>
  import("./pages/academic/Credentials").then((m) => ({
    default: m.CertificateLibrary,
  })),
);
const CertificateDetail = React.lazy(() =>
  import("./pages/academic/Credentials").then((m) => ({
    default: m.CertificateDetail,
  })),
);
const Compliance = React.lazy(() =>
  import("./pages/academic/Compliance").then((m) => ({
    default: m.Compliance,
  })),
);
const AttemptList = React.lazy(() =>
  import("./pages/academic/Outcomes").then((m) => ({ default: m.AttemptList })),
);
const AttemptDetail = React.lazy(() =>
  import("./pages/academic/Outcomes").then((m) => ({
    default: m.AttemptDetail,
  })),
);
const NewAttempt = React.lazy(() =>
  import("./pages/academic/Outcomes").then((m) => ({ default: m.NewAttempt })),
);
const ExceptionDetail = React.lazy(() =>
  import("./pages/academic/Exceptions").then((m) => ({
    default: m.ExceptionDetail,
  })),
);
const ExceptionList = React.lazy(() =>
  import("./pages/academic/Exceptions").then((m) => ({
    default: m.ExceptionList,
  })),
);
const OfficeAlerts = React.lazy(() =>
  import("./pages/academic/Exceptions").then((m) => ({
    default: m.OfficeAlerts,
  })),
);
const Applications = React.lazy(() =>
  import("./pages/academic/Applications").then((m) => ({
    default: m.Applications,
  })),
);
const ApplicationDraft = React.lazy(() =>
  import("./pages/academic/Applications").then((m) => ({
    default: m.ApplicationDraft,
  })),
);
const ApplicationDetail = React.lazy(() =>
  import("./pages/academic/Applications").then((m) => ({
    default: m.ApplicationDetail,
  })),
);
const Catalog = React.lazy(() =>
  import("./pages/academic/Catalog").then((m) => ({ default: m.Catalog })),
);
const CourseDetail = React.lazy(() =>
  import("./pages/academic/Catalog").then((m) => ({ default: m.CourseDetail })),
);
const CourseForm = React.lazy(() =>
  import("./pages/academic/Catalog").then((m) => ({ default: m.CourseForm })),
);
const OfferingDetail = React.lazy(() =>
  import("./pages/academic/Catalog").then((m) => ({
    default: m.OfferingDetail,
  })),
);
const ProviderSources = React.lazy(() =>
  import("./pages/academic/Catalog").then((m) => ({
    default: m.ProviderSources,
  })),
);
const Topics = React.lazy(() =>
  import("./pages/academic/Governance").then((m) => ({ default: m.Topics })),
);
const MappingList = React.lazy(() =>
  import("./pages/academic/Governance").then((m) => ({
    default: m.MappingList,
  })),
);
const MappingDetail = React.lazy(() =>
  import("./pages/academic/Governance").then((m) => ({
    default: m.MappingDetail,
  })),
);
const QuotaList = React.lazy(() =>
  import("./pages/academic/Governance").then((m) => ({ default: m.QuotaList })),
);
const QuotaDetail = React.lazy(() =>
  import("./pages/academic/Governance").then((m) => ({
    default: m.QuotaDetail,
  })),
);
const RoleDashboard = React.lazy(() =>
  import("./pages/Dashboards").then((m) => ({ default: m.RoleDashboard })),
);
const Imports = React.lazy(() =>
  import("./pages/Imports").then((m) => ({ default: m.Imports })),
);
const ImportDetail = React.lazy(() =>
  import("./pages/Imports").then((m) => ({ default: m.ImportDetail })),
);
const ReferenceSetup = React.lazy(() =>
  import("./pages/ReferenceSetup").then((m) => ({ default: m.ReferenceSetup })),
);
const TeachingList = React.lazy(() =>
  import("./pages/Teaching").then((m) => ({ default: m.TeachingList })),
);
const TeachingDetail = React.lazy(() =>
  import("./pages/Teaching").then((m) => ({ default: m.TeachingDetail })),
);
const TeachingForm = React.lazy(() =>
  import("./pages/Teaching").then((m) => ({ default: m.TeachingForm })),
);
const SourceCorrection = React.lazy(() =>
  import("./pages/SourceCorrection").then((m) => ({
    default: m.SourceCorrection,
  })),
);
const Accounts = React.lazy(() =>
  import("./pages/Accounts").then((m) => ({ default: m.Accounts })),
);
const StaffRecord = React.lazy(() =>
  import("./pages/StaffRecord").then((m) => ({ default: m.StaffRecord })),
);
const StaffDirectory = React.lazy(() =>
  import("./pages/StaffDirectory").then((m) => ({ default: m.StaffDirectory })),
);
const StaffNew = React.lazy(() =>
  import("./pages/StaffNew").then((m) => ({ default: m.StaffNew })),
);
const AppointmentRecord = React.lazy(() =>
  import("./pages/AppointmentRecord").then((m) => ({
    default: m.AppointmentRecord,
  })),
);
const Appointments = React.lazy(() =>
  import("./pages/Appointments").then((m) => ({ default: m.Appointments })),
);
const AppointmentNew = React.lazy(() =>
  import("./pages/AppointmentNew").then((m) => ({ default: m.AppointmentNew })),
);

export const routes = createRoutesFromElements(
  <>
    <Route path="/" element={<Navigate to="/login" replace />} />
    <Route path="/login" element={<Login />} />
    <Route element={<Shell />}>
      {(Object.keys(registers) as Register[]).map((name) => (
        <Route
          key={name}
          path={registers[name][0]}
          element={<WorkspaceRegister report={name} />}
        />
      ))}
      <Route
        path="/principal/departments/:departmentId"
        element={<WorkspaceRegister report="applications" />}
      />
      <Route path="/app/home" element={<RoleDashboard />} />
      <Route path="/drc/home" element={<RoleDashboard role="DRC_HEAD" />} />
      <Route path="/hod/home" element={<RoleDashboard role="HOD" />} />
      <Route
        path="/principal/home"
        element={<RoleDashboard role="PRINCIPAL" />}
      />
      <Route path="/admin/home" element={<RoleDashboard role="ADMIN" />} />
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
      <Route path="/app/review-office-alerts" element={<OfficeAlerts />} />
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
      <Route path="/app/certificates" element={<CertificateLibrary />} />
      <Route path="/app/certificates/:aid" element={<CertificateDetail />} />
      {["/app/compliance", "/hod/reports", "/principal/reports"].flatMap(
        (base) =>
          ["annual", "silver"].map((kind) => (
            <Route
              key={base + kind}
              path={base + "/" + kind + "/:itemId?"}
              element={<Compliance />}
            />
          )),
      )}
      <Route path="/app/catalog" element={<Catalog />} />
      <Route path="/app/catalog/:courseId" element={<CourseDetail />} />
      <Route path="/app/offerings/:offeringId" element={<OfferingDetail />} />
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
      <Route path="/hod/topic-mappings/:courseId" element={<MappingDetail />} />
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
      <Route path="/people/teaching/:teachingId" element={<TeachingDetail />} />
      <Route path="/admin/teaching/new" element={<TeachingForm />} />
      <Route
        path="/admin/teaching/:teachingId/correct"
        element={<TeachingForm />}
      />
      <Route path="/admin/imports" element={<Imports />} />
      <Route path="/admin/imports/:importId" element={<ImportDetail />} />
      <Route path="/admin/reference" element={<ReferenceSetup />} />
      <Route path="/people/reference" element={<ReferenceSetup />} />
      <Route path="/admin/teaching-assignments" element={<TeachingList />} />
      <Route path="/admin/academic-reference" element={<ReferenceSetup />} />
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
      <Route path="/app/history" element={<EmploymentHistory />} />
      <Route path="/app/compliance" element={<Compliance />} />
      <Route path="/drc/reviews" element={<Applications review />} />
      <Route path="/hod/reviews" element={<Applications review />} />
      <Route path="/hod/quotas" element={<QuotaList />} />
      <Route path="/app/applications/new/*" element={<ApplicationDraft />} />
      {["offering", "eligibility", "evidence", "review"].map((step) => (
        <Route
          key={step}
          path={`/app/applications/new/${step}`}
          element={<ApplicationDraft />}
        />
      ))}
      <Route path="/app/applications/:appId" element={<ApplicationDetail />} />
      <Route
        path="/app/applications/:appId/quota"
        element={<ApplicationDetail section="quota" />}
      />
      <Route
        path="/app/applications/:appId/history"
        element={<ApplicationDetail section="history" />}
      />
      <Route
        path="/app/applications/:appId/evidence"
        element={<ApplicationDetail section="evidence" />}
      />
      <Route
        path="/app/participation/:appId"
        element={<ApplicationDetail section="participation" />}
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
      <Route path="/principal/reports" element={<Compliance />} />
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
      <Route path="/admin/appointments/new" element={<AppointmentNew />} />
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
    <Route path="/auth/callback" element={<AuthComplete />} />
    {["/not-found", "/access-denied", "/system-unavailable"].map((path) => (
      <Route key={path} path={path} element={<Recovery />} />
    ))}
    <Route path="/auth/complete" element={<AuthComplete />} />
    <Route path="/auth/*" element={<AuthState />} />
    <Route path="*" element={<Recovery />} />
  </>,
);
