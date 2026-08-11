import type { DomainBreakdown } from "../../lib/analytics";
import { ReportRadarChart } from "./radar-chart";

// Fixed domain order
const DOMAIN_ORDER = ["Knowledge", "Understanding", "Application", "Analysis", "Evaluation"];

type Props = {
  domains: DomainBreakdown[];
  schoolDomains: DomainBreakdown[];
  overallDomains: DomainBreakdown[];
};

export function DomainPerformance({ domains, schoolDomains, overallDomains }: Props) {
  const domainMap = new Map(domains.map((d) => [d.domain, d]));
  const ordered = DOMAIN_ORDER.map((name) => domainMap.get(name)).filter(Boolean) as DomainBreakdown[];

  return (
    <div>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Domain Performance
      </h3>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Bars */}
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <div className="space-y-3">
            {ordered.map((d) => (
              <div key={d.domain}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-medium text-slate-700">{d.domain}</span>
                  <span className="text-xs text-slate-500">
                    {d.correct}/{d.total} ({d.percentage.toFixed(1)}%)
                  </span>
                </div>
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.min(d.percentage, 100)}%`,
                      backgroundColor: barColor(d.percentage),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Radar Chart */}
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <ReportRadarChart
            studentDomains={domains}
            schoolDomains={schoolDomains}
            overallDomains={overallDomains}
          />
        </div>
      </div>
    </div>
  );
}

function barColor(pct: number): string {
  if (pct >= 80) return "#16a34a";
  if (pct >= 60) return "#2563eb";
  if (pct >= 40) return "#d97706";
  return "#dc2626";
}
