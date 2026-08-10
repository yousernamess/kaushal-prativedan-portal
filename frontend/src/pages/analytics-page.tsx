import { useState, useEffect } from "react";
import { useQuery, useQueries } from "@tanstack/react-query";
import { analyticsApi, type StudentInSchool } from "../lib/analytics";
import { FilterBar } from "../components/analytics/filter-bar";
import { OverviewCards } from "../components/analytics/overview-cards";
import { DomainBreakdownChart } from "../components/analytics/domain-breakdown";
import { StudentRanking } from "../components/analytics/student-ranking";
import { StudentDetailModal } from "../components/analytics/student-detail-modal";
import { QuestionTable } from "../components/analytics/question-table";

export function AnalyticsPage() {
  // Filter state
  const [assessmentId, setAssessmentId] = useState("");
  const [schoolId, setSchoolId] = useState("");
  const [classNumber, setClassNumber] = useState("");
  const [section, setSection] = useState("");

  // Student detail modal
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);

  // Parse filter values
  const assessId = assessmentId ? Number(assessmentId) : 0;
  const schId = schoolId ? Number(schoolId) : undefined;
  const clsNum = classNumber ? Number(classNumber) : undefined;
  const sec = section || undefined;

  // Query params object (stable reference for React Query)
  const scopeParams = { school_id: schId, class_number: clsNum, section: sec };

  // ── Data fetching ──────────────────────────────────────────────

  const overviewQ = useQuery({
    queryKey: ["analytics", "overview", assessId, schId, clsNum, sec],
    queryFn: () => analyticsApi.overview(assessId, scopeParams),
    enabled: assessId > 0,
  });

  const questionsQ = useQuery({
    queryKey: ["analytics", "questions", assessId, schId, clsNum, sec],
    queryFn: () => analyticsApi.questionAnalytics(assessId, scopeParams),
    enabled: assessId > 0,
  });

  // For student ranking: if a specific school is selected, fetch that school's detail.
  // If "All Schools", fetch detail for each school from the overview and merge.
  const overview = overviewQ.data;
  const schoolIds = schId
    ? [schId]
    : (overview?.schools ?? []).map((s) => s.school_id);

  const schoolDetailQueries = useQueries({
    queries: schoolIds.map((sid) => ({
      queryKey: ["analytics", "schoolDetail", assessId, sid],
      queryFn: () => analyticsApi.schoolDetail(assessId, sid),
      enabled: assessId > 0 && sid > 0,
    })),
  });

  // Merge students from all school details
  const allStudents: StudentInSchool[] = schoolDetailQueries
    .filter((q) => q.data)
    .flatMap((q) => q.data!.students);

  // ── Loading / error states ─────────────────────────────────────

  const isLoading = overviewQ.isLoading || questionsQ.isLoading;
  const isError = overviewQ.isError || questionsQ.isError;

  // ── Render ─────────────────────────────────────────────────────

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      {/* Header */}
      <div>
        <p className="mb-2 text-sm font-medium text-primary">Portal</p>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Analytics</h2>
        <p className="mt-1 text-sm text-slate-500">
          Assessment performance insights and question analysis.
        </p>
      </div>

      {/* Filters */}
      <FilterBar
        assessmentId={assessmentId}
        schoolId={schoolId}
        classNumber={classNumber}
        section={section}
        onChangeAssessment={setAssessmentId}
        onChangeSchool={setSchoolId}
        onChangeClass={setClassNumber}
        onChangeSection={setSection}
      />

      {/* No assessment selected */}
      {!assessId && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <p className="text-sm text-slate-500">Select an assessment to view analytics.</p>
        </div>
      )}

      {/* Loading */}
      {assessId && isLoading && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => <div key={i} className="h-20 animate-pulse rounded-lg bg-slate-100" />)}
          </div>
          <div className="h-40 animate-pulse rounded-lg bg-slate-100" />
          <div className="h-60 animate-pulse rounded-lg bg-slate-100" />
        </div>
      )}

      {/* Error */}
      {assessId && isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-600">Failed to load analytics data. Please try again.</p>
        </div>
      )}

      {/* Content */}
      {assessId && !isLoading && !isError && overview && (
        <>
          {/* Overview Cards */}
          <section>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">Overview</h3>
            <OverviewCards
              studentsAssessed={overview.total_students_assessed}
              averagePercentage={overview.average_percentage}
              highestPercentage={overview.highest_percentage}
              lowestPercentage={overview.lowest_percentage}
            />
          </section>

          {/* Domain Performance */}
          {overview.domains.length > 0 && (
            <section>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
                Domain Performance
              </h3>
              <div className="rounded-lg border bg-white p-4 shadow-sm">
                <DomainBreakdownChart domains={overview.domains} />
              </div>
            </section>
          )}

          {/* Student Ranking */}
          <section>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
              Student Ranking
            </h3>
            <StudentRanking
              students={allStudents}
              onSelectStudent={setSelectedStudentId}
            />
          </section>

          {/* Question Analytics */}
          {questionsQ.data && (
            <section>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-slate-500">
                Question Analysis
              </h3>
              <QuestionTable
                assessmentId={assessId}
                questions={questionsQ.data.questions}
                schoolId={schId ?? null}
                classNumber={clsNum ?? null}
                section={sec ?? null}
              />
            </section>
          )}
        </>
      )}

      {/* Student Detail Modal */}
      {selectedStudentId && assessId > 0 && (
        <StudentDetailModal
          assessmentId={assessId}
          studentId={selectedStudentId}
          onClose={() => setSelectedStudentId(null)}
        />
      )}
    </div>
  );
}
