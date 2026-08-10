import type { StudentInSchool } from "../../lib/analytics";

type Props = {
  students: StudentInSchool[];
  onSelectStudent: (studentId: number) => void;
};

export function StudentRanking({ students, onSelectStudent }: Props) {
  if (students.length === 0) {
    return <p className="text-sm text-slate-500">No students have completed this assessment yet.</p>;
  }

  // Sort by percentage descending for ranking
  const sorted = [...students].sort((a, b) => b.percentage - a.percentage);

  // Compute competition ranks
  const rankMap = new Map<number, number>();
  let rank = 1;
  for (let i = 0; i < sorted.length; i++) {
    if (i > 0 && sorted[i].percentage < sorted[i - 1].percentage) {
      rank = i + 1;
    }
    rankMap.set(sorted[i].student_id, rank);
  }

  return (
    <div className="space-y-2">
      {/* Desktop table */}
      <div className="hidden overflow-x-auto rounded-lg border bg-white md:block">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Rank</th>
              <th className="px-4 py-3 font-medium">Student</th>
              <th className="px-4 py-3 font-medium">Roll</th>
              <th className="px-4 py-3 font-medium text-center">Score</th>
              <th className="px-4 py-3 font-medium text-center">Percentage</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((s) => (
              <tr
                key={s.student_id}
                className="cursor-pointer border-t transition-colors hover:bg-slate-50"
                onClick={() => onSelectStudent(s.student_id)}
              >
                <td className="px-4 py-3 font-medium text-slate-900">
                  #{rankMap.get(s.student_id)}
                </td>
                <td className="px-4 py-3 font-medium text-slate-900">{s.student_name}</td>
                <td className="px-4 py-3 text-slate-500">{s.roll_number}</td>
                <td className="px-4 py-3 text-center text-slate-700">
                  {s.score}/{s.total_questions}
                </td>
                <td className="px-4 py-3 text-center">
                  <PercentageBadge percentage={s.percentage} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="space-y-2 md:hidden">
        {sorted.map((s) => (
          <div
            key={s.student_id}
            className="cursor-pointer rounded-lg border bg-white p-3 shadow-sm transition-colors hover:bg-slate-50"
            onClick={() => onSelectStudent(s.student_id)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-100 text-xs font-bold text-slate-700">
                  #{rankMap.get(s.student_id)}
                </span>
                <div>
                  <p className="text-sm font-medium text-slate-900">{s.student_name}</p>
                  <p className="text-xs text-slate-500">Roll {s.roll_number}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-slate-900">{s.score}/{s.total_questions}</p>
                <PercentageBadge percentage={s.percentage} />
              </div>
            </div>
          </div>
        ))}
      </div>
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
