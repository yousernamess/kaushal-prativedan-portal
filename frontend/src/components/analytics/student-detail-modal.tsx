import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "../../lib/analytics";
import { DomainBreakdownChart } from "./domain-breakdown";

type Props = {
  assessmentId: number;
  studentId: number;
  onClose: () => void;
};

export function StudentDetailModal({ assessmentId, studentId, onClose }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics", "student", assessmentId, studentId],
    queryFn: () => analyticsApi.studentDetail(assessmentId, studentId),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Student Analytics</h3>
            {data && (
              <p className="text-sm text-slate-500">
                {data.student_name} · Code {data.student_code}
              </p>
            )}
          </div>
          <button onClick={onClose} className="rounded-md p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600" aria-label="Close">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4">
          {isLoading && <LoadingSkeleton />}
          {error && <p className="text-sm text-red-600">Failed to load student data.</p>}
          {data && (
            <div className="space-y-5">
              {/* School info */}
              <p className="text-sm text-slate-500">
                {data.school_name} · Class {data.current_class} · Section {data.current_section}
              </p>

              {/* Main stats */}
              <div className="grid grid-cols-3 gap-3">
                <StatBox label="Score" value={`${data.score}/${data.total_questions}`} />
                <StatBox label="Percentage" value={`${data.percentage.toFixed(1)}%`} highlight />
                <StatBox label="Wrong" value={String(data.wrong)} />
              </div>

              {/* Averages and ranks */}
              <div className="grid grid-cols-3 gap-3">
                <StatBox label="School Avg" value={`${data.school_average.toFixed(1)}%`} />
                <StatBox label="Overall Avg" value={`${data.overall_average.toFixed(1)}%`} />
                <StatBox label="School Rank" value={`#${data.school_rank}`} />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <StatBox label="Overall Rank" value={`#${data.overall_rank}`} />
                <StatBox label="School Percentile" value={`${data.school_percentile.toFixed(1)}%`} />
                <StatBox label="Overall Percentile" value={`${data.overall_percentile.toFixed(1)}%`} />
              </div>

              {/* Domain breakdown */}
              <div>
                <h4 className="mb-2 text-sm font-semibold text-slate-700">Domain Performance</h4>
                <DomainBreakdownChart domains={data.domains} />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3 text-center">
      <p className={`text-lg font-bold ${highlight ? "text-blue-600" : "text-slate-900"}`}>{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-4 w-48 rounded bg-slate-200" />
      <div className="grid grid-cols-3 gap-3">
        {[1, 2, 3].map((i) => <div key={i} className="h-16 rounded-lg bg-slate-100" />)}
      </div>
      <div className="grid grid-cols-3 gap-3">
        {[1, 2, 3].map((i) => <div key={i} className="h-16 rounded-lg bg-slate-100" />)}
      </div>
    </div>
  );
}
