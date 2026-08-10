type Props = {
  studentsAssessed: number;
  averagePercentage: number;
  highestPercentage: number;
  lowestPercentage: number;
};

export function OverviewCards({ studentsAssessed, averagePercentage, highestPercentage, lowestPercentage }: Props) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <Card label="Students Assessed" value={String(studentsAssessed)} />
      <Card label="Average" value={`${averagePercentage.toFixed(1)}%`} />
      <Card label="Highest" value={`${highestPercentage.toFixed(1)}%`} color="text-green-700" />
      <Card label="Lowest" value={`${lowestPercentage.toFixed(1)}%`} color="text-red-600" />
    </div>
  );
}

function Card({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="rounded-lg border bg-white p-4 text-center shadow-sm">
      <p className={`text-2xl font-bold ${color ?? "text-slate-900"}`}>{value}</p>
      <p className="mt-1 text-xs font-medium text-slate-500">{label}</p>
    </div>
  );
}
