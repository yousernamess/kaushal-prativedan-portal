import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { DomainBreakdown } from "../../lib/analytics";

// Fixed domain order for consistent radar chart display
const DOMAIN_ORDER = ["Knowledge", "Understanding", "Application", "Analysis", "Evaluation"];

type Props = {
  studentDomains: DomainBreakdown[];
  schoolDomains: DomainBreakdown[];
  overallDomains: DomainBreakdown[];
};

export function ReportRadarChart({ studentDomains, schoolDomains, overallDomains }: Props) {
  const toMap = (arr: DomainBreakdown[] | undefined) => new Map((arr ?? []).map((d) => [d.domain, d.percentage]));

  const sMap = toMap(studentDomains);
  const schMap = toMap(schoolDomains);
  const oMap = toMap(overallDomains);

  const chartData = DOMAIN_ORDER.map((name) => ({
    domain: name,
    you: sMap.get(name) ?? 0,
    school: schMap.get(name) ?? 0,
    overall: oMap.get(name) ?? 0,
    fullMark: 100,
  }));

  const hasData = chartData.some((d) => d.you > 0 || d.school > 0 || d.overall > 0);

  if (!hasData) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-slate-400">
        No domain data available
      </div>
    );
  }

  return (
    <div className="radar-chart-container">
      <ResponsiveContainer width="100%" height={280}>
        <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="#e2e8f0" strokeDasharray="3 3" />
          <PolarAngleAxis
            dataKey="domain"
            tick={{ fontSize: 11, fill: "#475569" }}
            tickLine={false}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 9, fill: "#94a3b8" }}
            tickCount={4}
            axisLine={false}
          />
          <Radar
            name="You"
            dataKey="you"
            stroke="#2563eb"
            fill="#2563eb"
            fillOpacity={0.15}
            strokeWidth={2}
            dot={{ r: 3, fill: "#2563eb" }}
          />
          <Radar
            name="School Average"
            dataKey="school"
            stroke="#f59e0b"
            fill="#f59e0b"
            fillOpacity={0.08}
            strokeWidth={1.5}
            strokeDasharray="4 3"
            dot={false}
          />
          <Radar
            name="All Schools Average"
            dataKey="overall"
            stroke="#94a3b8"
            fill="#94a3b8"
            fillOpacity={0.05}
            strokeWidth={1.5}
            strokeDasharray="2 2"
            dot={false}
          />
          <Legend
            verticalAlign="bottom"
            wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
          />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
            formatter={(value: number) => `${value.toFixed(1)}%`}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
