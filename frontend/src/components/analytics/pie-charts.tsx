import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { DomainBreakdown } from "../../lib/analytics";

const PALETTE = ["#2563eb", "#16a34a", "#f59e0b", "#ef4444", "#8b5cf6", "#0ea5e9"];

const DOMAIN_COLORS: Record<string, string> = {
  "Experiential Learning": "#2563eb",
  "Knowledge Base": "#16a34a",
  "Analytical": "#f59e0b",
};

const BAND_COLORS: Record<string, string> = {
  "Excellent (75%+)": "#16a34a",
  "Good (60-74%)": "#0ea5e9",
  "Average (40-59%)": "#f59e0b",
  "Needs Improvement (<40%)": "#ef4444",
};

export function DomainSharePie({ domains }: { domains: DomainBreakdown[] }) {
  const data = domains
    .filter((d) => d.total > 0)
    .map((d) => ({ name: d.domain, value: d.correct }));
  if (data.length === 0) {
    return <p className="py-10 text-center text-sm text-slate-500">No data yet.</p>;
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={2}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={DOMAIN_COLORS[entry.name] ?? PALETTE[0]} />
          ))}
        </Pie>
        <Tooltip formatter={(value: unknown, name: unknown) => [`${value} correct answers`, String(name)] as [string, string]} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function PerformanceBandPie({ percentages }: { percentages: number[] }) {
  if (percentages.length === 0) {
    return <p className="py-10 text-center text-sm text-slate-500">No data yet.</p>;
  }
  const bands = [
    { name: "Excellent (75%+)", min: 75, max: Infinity },
    { name: "Good (60-74%)", min: 60, max: 75 },
    { name: "Average (40-59%)", min: 40, max: 60 },
    { name: "Needs Improvement (<40%)", min: -Infinity, max: 40 },
  ].map((band) => ({
    name: band.name,
    value: percentages.filter((p) => p >= band.min && p < band.max).length,
  })).filter((b) => b.value > 0);

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={bands} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={2}>
          {bands.map((entry) => (
            <Cell key={entry.name} fill={BAND_COLORS[entry.name] ?? PALETTE[1]} />
          ))}
        </Pie>
        <Tooltip formatter={(value: unknown, name: unknown) => [`${value} student${Number(value) === 1 ? "" : "s"}`, String(name)] as [string, string]} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
