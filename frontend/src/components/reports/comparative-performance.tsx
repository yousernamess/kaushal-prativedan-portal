import type { StudentDetail } from "../../lib/analytics";

type Props = {
  data: StudentDetail;
};

export function ComparativePerformance({ data }: Props) {
  return (
    <div>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Comparative Performance
      </h3>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <CompareCard
          label="Average"
          schoolValue={`${data.school_average.toFixed(1)}%`}
          overallValue={`${data.overall_average.toFixed(1)}%`}
        />
        <CompareCard
          label="Rank"
          schoolValue={`#${data.school_rank}`}
          overallValue={`#${data.overall_rank}`}
        />
        <CompareCard
          label="Percentile"
          schoolValue={`${data.school_percentile.toFixed(1)}`}
          overallValue={`${data.overall_percentile.toFixed(1)}`}
        />
      </div>
    </div>
  );
}

function CompareCard({
  label,
  schoolValue,
  overallValue,
}: {
  label: string;
  schoolValue: string;
  overallValue: string;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <p className="mb-2 text-xs font-medium text-slate-500">{label}</p>
      <div className="flex justify-between">
        <div className="text-center flex-1">
          <p className="text-base font-bold text-slate-800">{schoolValue}</p>
          <p className="text-[10px] text-slate-400">School</p>
        </div>
        <div className="mx-2 w-px bg-slate-200" />
        <div className="text-center flex-1">
          <p className="text-base font-bold text-slate-800">{overallValue}</p>
          <p className="text-[10px] text-slate-400">Overall</p>
        </div>
      </div>
    </div>
  );
}
