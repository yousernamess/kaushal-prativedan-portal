import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "../../lib/analytics";

type Props = {
  assessmentId: number;
  questionId: number;
  schoolId: number | null;
  classNumber: number | null;
  section: string | null;
};

export function QuestionHistory({ assessmentId, questionId, schoolId, classNumber, section }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics", "history", assessmentId, questionId, schoolId, classNumber, section],
    queryFn: () => analyticsApi.questionHistory(assessmentId, questionId, {
      school_id: schoolId ?? undefined,
      class_number: classNumber ?? undefined,
      section: section ?? undefined,
    }),
  });

  if (isLoading) {
    return <div className="h-16 animate-pulse rounded bg-slate-100" />;
  }

  if (error) {
    return <p className="text-sm text-red-600">Failed to load question history.</p>;
  }

  if (!data) return null;

  // Build scope label
  const scopeParts: string[] = [];
  if (schoolId) {
    // We don't have the school name here, but the API response scope might have it
    scopeParts.push("Selected School");
  }
  if (classNumber) scopeParts.push(`Class ${classNumber}`);
  if (section) scopeParts.push(`Section ${section}`);
  const scopeLabel = scopeParts.length > 0 ? scopeParts.join(" · ") : "All Schools";

  return (
    <div className="space-y-4">
      {/* Question info */}
      <div>
        <p className="text-sm font-semibold text-slate-900">
          Q{data.question_number}: {data.question_text ?? "(no text)"}
        </p>
        <p className="text-xs text-slate-500">
          Domain: {data.domain} · Scope: {scopeLabel}
        </p>
      </div>

      {/* Current assessment */}
      <div>
        <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">Current</h4>
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-900">
                {data.current.assessment_name}
              </p>
              <p className="text-xs text-slate-500">
                {data.current.academic_year} · {data.current.assessment_type}
              </p>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-blue-700">{data.current.percentage.toFixed(1)}%</p>
              <p className="text-xs text-slate-500">{data.current.assessed} students</p>
            </div>
          </div>
        </div>
      </div>

      {/* Historical appearances */}
      {data.history.length > 0 ? (
        <div>
          <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Historical Appearances ({data.history.length})
          </h4>
          <div className="space-y-2">
            {data.history.map((h) => (
              <div key={`${h.assessment_id}-${h.question_number}`} className="rounded-lg border bg-white p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{h.assessment_name}</p>
                    <p className="text-xs text-slate-500">
                      {h.academic_year} · {h.assessment_type}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-slate-900">{h.percentage.toFixed(1)}%</p>
                    <p className="text-xs text-slate-500">{h.assessed} students</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-sm text-slate-500">No previous appearances found for this question in the selected scope.</p>
      )}
    </div>
  );
}
