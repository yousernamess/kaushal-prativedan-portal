import type { StudentDetail } from "../../lib/analytics";

type Props = {
  data: StudentDetail;
};

export function PerformanceSummary({ data }: Props) {
  const pct = data.percentage;
  const pctColor =
    pct >= 80 ? "text-green-700" : pct >= 60 ? "text-blue-700" : pct >= 40 ? "text-amber-700" : "text-red-700";

  return (
    <div>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Performance Summary
      </h3>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatBox label="Score" value={String(data.score)} sub={`/ ${data.total_questions}`} />
        <StatBox label="Percentage" value={`${data.percentage.toFixed(1)}%`} color={pctColor} highlight />
        <StatBox label="Total Questions" value={String(data.total_questions)} />
        <StatBox label="Wrong" value={String(data.wrong)} color="text-red-600" />
      </div>
    </div>
  );
}

function StatBox({
  label,
  value,
  sub,
  color,
  highlight,
}: {
  label: string;
  value: string;
  sub?: string;
  color?: string;
  highlight?: boolean;
}) {
  return (
    <div className={`rounded-lg border p-3 text-center ${highlight ? "border-blue-200 bg-blue-50" : "border-slate-200 bg-white"}`}>
      <p className={`text-xl font-bold ${color ?? "text-slate-900"}`}>
        {value}
        {sub && <span className="text-sm font-normal text-slate-400">{sub}</span>}
      </p>
      <p className="mt-0.5 text-xs text-slate-500">{label}</p>
    </div>
  );
}
