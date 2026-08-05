import { createBrowserRouter } from "react-router-dom";
import { AppLayout } from "../components/layout/app-layout";
import { AcademicYearsPage } from "../pages/academic-years-page";
import { AssessmentsPage } from "../pages/assessments-page";
import { DashboardPage } from "../pages/dashboard-page";
import { ProcessOmrPage } from "../pages/process-omr-page";
import { ReportsPage } from "../pages/reports-page";
import { SchoolsPage } from "../pages/schools-page";
import { SectionsPage } from "../pages/sections-page";
import { StudentsPage } from "../pages/students-page";

export const router = createBrowserRouter([{ path: "/", element: <AppLayout />, children: [
  { index: true, element: <DashboardPage /> }, { path: "schools", element: <SchoolsPage /> },
  { path: "academic-years", element: <AcademicYearsPage /> }, { path: "sections", element: <SectionsPage /> },
  { path: "students", element: <StudentsPage /> }, { path: "assessments", element: <AssessmentsPage /> },
  { path: "process-omr", element: <ProcessOmrPage /> }, { path: "reports", element: <ReportsPage /> },
] }]);
