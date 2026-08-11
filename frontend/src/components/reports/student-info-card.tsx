import type { StudentDetail } from "../../lib/analytics";

type Props = {
  data: StudentDetail;
};

export function StudentInfoCard({ data }: Props) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Student Information
      </h3>
      <div className="grid grid-cols-1 gap-x-8 gap-y-2 sm:grid-cols-2">
        <InfoRow label="Name" value={data.student_name} />
        <InfoRow label="School" value={data.school_name} />
        <InfoRow label="Roll Number" value={String(data.roll_number)} />
        <InfoRow label="Class" value={`Class ${data.current_class}`} />
        <InfoRow label="Section" value={data.current_section} />
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2">
      <span className="text-xs text-slate-500 w-24 shrink-0">{label}</span>
      <span className="text-sm font-medium text-slate-800">{value}</span>
    </div>
  );
}
