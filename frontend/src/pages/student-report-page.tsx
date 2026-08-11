import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { analyticsApi } from "../lib/analytics";
import { ReportHeader } from "../components/reports/report-header";
import { StudentInfoCard } from "../components/reports/student-info-card";
import { PerformanceSummary } from "../components/reports/performance-summary";
import { ComparativePerformance } from "../components/reports/comparative-performance";
import { DomainPerformance } from "../components/reports/domain-performance";
import { QuestionAnalysisTable } from "../components/reports/question-analysis-table";
import { ReportFooter } from "../components/reports/report-footer";
import { Printer, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/button";

export function StudentReportPage() {
  const { studentId, assessmentId } = useParams<{
    studentId: string;
    assessmentId: string;
  }>();

  const sid = Number(studentId);
  const aid = Number(assessmentId);

  const detailQ = useQuery({
    queryKey: ["analytics", "student", aid, sid],
    queryFn: () => analyticsApi.studentDetail(aid, sid),
    enabled: aid > 0 && sid > 0,
  });

  const questionsQ = useQuery({
    queryKey: ["analytics", "studentReportQuestions", aid, sid],
    queryFn: () => analyticsApi.studentReportQuestions(aid, sid),
    enabled: aid > 0 && sid > 0,
  });

  const isLoading = detailQ.isLoading || questionsQ.isLoading;
  const isError = detailQ.isError || questionsQ.isError;

  const handlePrint = () => {
    window.print();
  };

  // Invalid params
  if (!sid || !aid) {
    return (
      <div className="mx-auto max-w-3xl p-8 text-center">
        <p className="text-slate-500">Invalid report URL.</p>
        <Link to="/reports" className="text-blue-600 text-sm mt-2 inline-block">
          Back to Reports
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl">
      {/* Controls — hidden on print */}
      <div className="no-print mb-6 flex items-center justify-between">
        <Link
          to="/reports"
          className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
        >
          <ArrowLeft size={16} />
          Reports
        </Link>
        {!isLoading && !isError && detailQ.data && (
          <div className="flex items-center gap-2">
            <Button variant="default" size="default" onClick={handlePrint} className="gap-2 text-sm no-print">
              <Printer size={16} />
              Print / Save as PDF
            </Button>
          </div>
        )}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-4">
          <div className="h-16 animate-pulse rounded-lg bg-slate-100" />
          <div className="h-24 animate-pulse rounded-lg bg-slate-100" />
          <div className="grid grid-cols-4 gap-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-100" />
            ))}
          </div>
          <div className="h-60 animate-pulse rounded-lg bg-slate-100" />
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-sm text-red-600">
            Could not load report data. The assessment or student may not exist,
            or no completed attempt was found.
          </p>
          <Link to="/reports" className="text-blue-600 text-sm mt-3 inline-block">
            Back to Reports
          </Link>
        </div>
      )}

      {/* Report Content */}
      {!isLoading && !isError && detailQ.data && (
        <div
          id="student-report"
          className="rounded-xl border border-slate-200 bg-white shadow-sm print:rounded-none print:border-0 print:shadow-none"
        >
          <div className="p-6 sm:p-8 print:p-6">
            {/* Header */}
            <ReportHeader data={detailQ.data} />

            {/* Student Info */}
            <div className="mt-6">
              <StudentInfoCard data={detailQ.data} />
            </div>

            {/* Performance Summary */}
            <div className="mt-6">
              <PerformanceSummary data={detailQ.data} />
            </div>

            {/* Comparative Performance */}
            <div className="mt-6">
              <ComparativePerformance data={detailQ.data} />
            </div>

            {/* Domain Performance + Radar Chart */}
            <div className="mt-6 domain-section">
              <DomainPerformance
                domains={detailQ.data.domains}
                schoolDomains={detailQ.data.school_domains}
                overallDomains={detailQ.data.overall_domains}
              />
            </div>

            {/* Question Analysis */}
            <div className="mt-8 question-section">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Question Analysis
              </h3>
              {questionsQ.data && (
                <QuestionAnalysisTable questions={questionsQ.data.questions} />
              )}
              {questionsQ.isLoading && (
                <div className="h-40 animate-pulse rounded-lg bg-slate-100" />
              )}
              {questionsQ.isError && (
                <p className="text-sm text-red-500">Failed to load question data.</p>
              )}
            </div>

            {/* Footer */}
            <ReportFooter />
          </div>
        </div>
      )}
    </div>
  );
}
