import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { assessmentApi } from "../lib/assessments";
import { analyticsApi } from "../lib/analytics";
import type { Assessment } from "../lib/assessments";
import type { StudentInSchool } from "../lib/analytics";
import { FileBarChart, Search } from "lucide-react";

export function ReportsPage() {
  const [assessmentId, setAssessmentId] = useState("");
  const [schoolId, setSchoolId] = useState("");

  const aid = Number(assessmentId);
  const sid = Number(schoolId);

  const assessmentsQ = useQuery({ queryKey: ["assessments"], queryFn: assessmentApi.list });
  const assessments = (assessmentsQ.data ?? []).filter((a: Assessment) => !a.is_deleted);

  // Fetch overview to get school list for the selected assessment
  const overviewQ = useQuery({
    queryKey: ["analytics", "overview", aid],
    queryFn: () => analyticsApi.overview(aid),
    enabled: aid > 0,
  });
  const schools = overviewQ.data?.schools ?? [];

  // Fetch school detail for student list
  const schoolDetailQ = useQuery({
    queryKey: ["analytics", "schoolDetail", aid, sid],
    queryFn: () => analyticsApi.schoolDetail(aid, sid),
    enabled: aid > 0 && sid > 0,
  });
  const students: StudentInSchool[] = schoolDetailQ.data?.students ?? [];

  // Sort students by roll number
  const sortedStudents = [...students].sort((a, b) => a.roll_number - b.roll_number);

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Header */}
      <div>
        <p className="mb-2 text-sm font-medium text-primary">Portal</p>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Reports</h2>
        <p className="mt-1 text-sm text-slate-500">
          Select an assessment and school to view student reports.
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={assessmentId}
          onChange={(e) => { setAssessmentId(e.target.value); setSchoolId(""); }}
          className="h-10 rounded-md border bg-white px-3 text-sm min-w-[220px]"
        >
          <option value="">Select Assessment...</option>
          {assessments.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name} ({a.assessment_type}) — Class {a.class_number}
            </option>
          ))}
        </select>

        {aid > 0 && (
          <select
            value={schoolId}
            onChange={(e) => setSchoolId(e.target.value)}
            className="h-10 rounded-md border bg-white px-3 text-sm min-w-[180px]"
          >
            <option value="">Select School...</option>
            {schools.map((s) => (
              <option key={s.school_id} value={s.school_id}>
                {s.school_name} ({s.students_assessed} students)
              </option>
            ))}
          </select>
        )}
      </div>

      {/* No assessment selected */}
      {!aid && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-12 text-center">
          <FileBarChart className="mx-auto mb-3 text-slate-300" size={40} />
          <p className="text-sm text-slate-500">Select an assessment to get started.</p>
        </div>
      )}

      {/* Assessment selected but no school */}
      {aid > 0 && !sid && !overviewQ.isLoading && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <Search className="mx-auto mb-3 text-slate-300" size={32} />
          <p className="text-sm text-slate-500">Select a school to view student reports.</p>
        </div>
      )}

      {/* Loading */}
      {aid > 0 && sid > 0 && schoolDetailQ.isLoading && (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      )}

      {/* Student list */}
      {aid > 0 && sid > 0 && !schoolDetailQ.isLoading && sortedStudents.length > 0 && (
        <div className="overflow-x-auto rounded-lg border bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Roll No.</th>
                <th className="px-4 py-3 font-medium">Student Name</th>
                <th className="px-4 py-3 font-medium text-center">Score</th>
                <th className="px-4 py-3 font-medium text-center">Percentage</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {sortedStudents.map((s) => (
                <tr key={s.student_id} className="border-t transition-colors hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-800">{s.roll_number}</td>
                  <td className="px-4 py-3 text-slate-700">{s.student_name}</td>
                  <td className="px-4 py-3 text-center text-slate-700">
                    {s.score}/{s.total_questions}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <PercentageBadge percentage={s.percentage} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/reports/students/${s.student_id}/assessments/${aid}`}
                      className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 transition-colors"
                    >
                      <FileBarChart size={14} />
                      View Report
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty school */}
      {aid > 0 && sid > 0 && !schoolDetailQ.isLoading && sortedStudents.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <p className="text-sm text-slate-500">No students have completed this assessment at this school.</p>
        </div>
      )}
    </div>
  );
}

function PercentageBadge({ percentage }: { percentage: number }) {
  const color =
    percentage >= 80 ? "bg-green-100 text-green-700" :
    percentage >= 60 ? "bg-blue-100 text-blue-700" :
    percentage >= 40 ? "bg-amber-100 text-amber-700" :
    "bg-red-100 text-red-700";

  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${color}`}>
      {percentage.toFixed(1)}%
    </span>
  );
}
