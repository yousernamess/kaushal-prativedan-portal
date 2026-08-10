import { useQuery } from "@tanstack/react-query";
import { assessmentApi, CLASS_OPTIONS, ASSESSMENT_TYPES } from "../../lib/assessments";
import { masterApi } from "../../lib/master-data";
import type { Assessment } from "../../lib/assessments";
import type { AcademicYear, School } from "../../lib/master-data";

type Props = {
  assessmentId: string;
  schoolId: string;
  onSelectAssessment: (id: string) => void;
  onSelectSchool: (id: string) => void;
};

export function StepAssessmentSchool({
  assessmentId,
  schoolId,
  onSelectAssessment,
  onSelectSchool,
}: Props) {
  const assessmentsQ = useQuery({
    queryKey: ["assessments"],
    queryFn: () => assessmentApi.list(),
  });

  const schoolsQ = useQuery({
    queryKey: ["schools"],
    queryFn: () => masterApi.schools(),
  });

  const yearsQ = useQuery({
    queryKey: ["academic-years"],
    queryFn: () => masterApi.years(),
  });

  const assessments = assessmentsQ.data ?? [];
  const schools = schoolsQ.data ?? [];
  const years = yearsQ.data ?? [];

  const selectedAssessment = assessments.find((a) => String(a.id) === assessmentId);
  const selectedSchool = schools.find((s) => String(s.id) === schoolId);

  const yearName = (yearId: number) =>
    years.find((y: AcademicYear) => y.id === yearId)?.name ?? "—";

  const questionCount = selectedAssessment?.questions?.length ?? 0;

  return (
    <div className="space-y-6">
      {/* Assessment Selection */}
      <label className="block text-sm">
        <span className="font-medium text-slate-700">
          Assessment <span className="text-red-500">*</span>
        </span>
        <select
          className="mt-1 h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm"
          value={assessmentId}
          onChange={(e) => onSelectAssessment(e.target.value)}
        >
          <option value="">Select an assessment</option>
          {assessments.map((a: Assessment) => (
            <option key={a.id} value={a.id}>
              {a.name} ({a.assessment_type}) — Class {a.class_number}, {yearName(a.academic_year_id)} — {a.questions.length} questions
            </option>
          ))}
        </select>
      </label>

      {/* Assessment Metadata (read-only) */}
      {selectedAssessment && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Assessment Details</p>
          <div className="mt-2 grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-slate-500">Name:</span>{" "}
              <span className="font-medium text-slate-900">{selectedAssessment.name}</span>
            </div>
            <div>
              <span className="text-slate-500">Type:</span>{" "}
              <span className="font-medium text-slate-900">{selectedAssessment.assessment_type}</span>
            </div>
            <div>
              <span className="text-slate-500">Academic Year:</span>{" "}
              <span className="font-medium text-slate-900">{yearName(selectedAssessment.academic_year_id)}</span>
            </div>
            <div>
              <span className="text-slate-500">Class:</span>{" "}
              <span className="font-medium text-slate-900">
                {CLASS_OPTIONS.find((c) => c.value === selectedAssessment.class_number)?.label ?? selectedAssessment.class_number}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Questions:</span>{" "}
              <span className="font-medium text-slate-900">{questionCount}</span>
            </div>
          </div>
        </div>
      )}

      {/* School Selection */}
      <label className="block text-sm">
        <span className="font-medium text-slate-700">
          School <span className="text-red-500">*</span>
        </span>
        <select
          className="mt-1 h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm"
          value={schoolId}
          onChange={(e) => onSelectSchool(e.target.value)}
        >
          <option value="">Select a school</option>
          {schools.map((s: School) => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.student_count} students)
            </option>
          ))}
        </select>
      </label>

      {/* Loading states */}
      {(assessmentsQ.isPending || schoolsQ.isPending) && (
        <div className="flex items-center gap-2 py-4 text-sm text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
          Loading data...
        </div>
      )}

      {/* Empty states */}
      {!assessmentsQ.isPending && assessments.length === 0 && (
        <div className="rounded-lg border border-dashed border-amber-300 bg-amber-50 p-4 text-sm text-amber-700">
          No assessments found. Create an assessment first before processing OMR sheets.
        </div>
      )}

      {!schoolsQ.isPending && schools.length === 0 && (
        <div className="rounded-lg border border-dashed border-amber-300 bg-amber-50 p-4 text-sm text-amber-700">
          No schools found. Add a school in Master Data first.
        </div>
      )}
    </div>
  );
}
