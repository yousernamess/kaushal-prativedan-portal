import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DomainBreakdown } from "../../lib/analytics";

const DOMAIN_COLORS: Record<string, string> = {
  "Experiential Learning": "#2563eb",
  "Knowledge Base": "#16a34a",
  "Analytical": "#f59e0b",
};
const FALLBACK_COLOR = "#64748b";

export function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <h4 className="text-sm font-semibold text-slate-800">{title}</h4>
      {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
      <div className="mt-3">{children}</div>
    </div>
  );
}

export function SchoolComparisonBar({
  data,
}: {
  data: { schoolId: number; label: string; name: string; percentage: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
        <Tooltip
          formatter={(value: unknown) => [`${value}%`, "Avg score"] as [string, string]}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.name ?? ""}
        />
        <Bar dataKey="percentage" name="Average %" fill="#2563eb" radius={[4, 4, 0, 0]} maxBarSize={48} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DomainComparisonBar({
  schools,
}: {
  schools: { label: string; name: string; domains: DomainBreakdown[] }[];
}) {
  // Pivot: one row per school, one column per domain
  const domainNames = [...new Set(schools.flatMap((s) => s.domains.map((d) => d.domain)))];
  const data = schools.map((s) => {
    const row: Record<string, string | number> = { label: s.label, name: s.name };
    for (const d of s.domains) row[d.domain] = d.percentage;
    return row;
  });
  return (
    <ResponsiveContainer width="100%" height={340}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
        <Tooltip
          formatter={(value: unknown, name: unknown) => [`${value}%`, String(name)] as [string, string]}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.name ?? ""}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {domainNames.map((name) => (
          <Bar
            key={name}
            dataKey={name}
            fill={DOMAIN_COLORS[name] ?? FALLBACK_COLOR}
            radius={[4, 4, 0, 0]}
            maxBarSize={28}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ClassPerformanceBar({
  data,
}: {
  data: { label: string; name: string; percentage: number }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
        <Tooltip
          formatter={(value: unknown) => [`${value}%`, "Avg score"] as [string, string]}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.name ?? ""}
        />
        <Bar dataKey="percentage" name="Average %" fill="#16a34a" radius={[4, 4, 0, 0]} maxBarSize={48} />
      </BarChart>
    </ResponsiveContainer>
  );
}
