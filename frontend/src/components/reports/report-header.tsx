import type { StudentDetail } from "../../lib/analytics";

type Props = {
  data: StudentDetail;
};

export function ReportHeader({ data }: Props) {
  return (
    <div className="flex items-start justify-between border-b-2 border-blue-700 pb-4">
      <div>
        <h1 className="text-xl font-bold text-blue-800 tracking-tight">
          Kaushal Prativedan
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">Science Assessment Report</p>
      </div>
      <div className="text-right">
        <p className="text-sm font-semibold text-slate-800">{data.assessment_name}</p>
        <p className="text-xs text-slate-500">
          {data.assessment_type} · {data.academic_year_name}
        </p>
      </div>
    </div>
  );
}
