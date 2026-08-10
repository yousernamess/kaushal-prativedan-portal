import type { DomainBreakdown } from "../../lib/analytics";

type Props = {
  domains: DomainBreakdown[];
};

export function DomainBreakdownChart({ domains }: Props) {
  if (domains.length === 0) {
    return <p className="text-sm text-slate-500">No domain data available.</p>;
  }

  return (
    <div className="space-y-3">
      {domains.map((d) => (
        <div key={d.domain}>
          <div className="mb-1 flex items-center justify-between text-sm">
            <span className="font-medium text-slate-700">{d.domain}</span>
            <span className="text-slate-500">
              {d.correct}/{d.total} ({d.percentage.toFixed(1)}%)
            </span>
          </div>
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-blue-600 transition-all duration-300"
              style={{ width: `${Math.min(d.percentage, 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
