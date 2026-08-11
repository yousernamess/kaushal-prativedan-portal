import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "../components/layout/app-layout";
import { AnalyticsPage } from "../pages/analytics-page";
import { AssessmentsPage } from "../pages/assessments-page";
import { AssessmentDetailPage } from "../pages/assessment-detail-page";
import { DashboardPage } from "../pages/dashboard-page";
import { MasterDataPage } from "../pages/master-data-page";
import { ProcessOmrPage } from "../pages/process-omr-page";
import { ReportsPage } from "../pages/reports-page";
import { StudentReportPage } from "../pages/student-report-page";

export const router = createBrowserRouter([{ path: "/", element: <AppLayout />, children: [
  { index: true, element: <DashboardPage /> },
  { path: "master-data", element: <MasterDataPage /> },
  { path: "assessments", element: <AssessmentsPage /> },
  { path: "assessments/:id", element: <AssessmentDetailPage /> },
  { path: "process-omr", element: <ProcessOmrPage /> },
  { path: "analytics", element: <AnalyticsPage /> },
  { path: "reports", element: <ReportsPage /> },
  { path: "reports/students/:studentId/assessments/:assessmentId", element: <StudentReportPage /> },
]}]);
