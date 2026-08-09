import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "../components/layout/app-layout";
import { AssessmentsPage } from "../pages/assessments-page";
import { DashboardPage } from "../pages/dashboard-page";
import { MasterDataPage } from "../pages/master-data-page";
import { ProcessOmrPage } from "../pages/process-omr-page";
import { ReportsPage } from "../pages/reports-page";

export const router = createBrowserRouter([{ path: "/", element: <AppLayout />, children: [
  { index: true, element: <DashboardPage /> },
  { path: "master-data", element: <MasterDataPage /> },
  { path: "assessments", element: <AssessmentsPage /> },
  { path: "process-omr", element: <ProcessOmrPage /> },
  { path: "reports", element: <ReportsPage /> },
]}]);
