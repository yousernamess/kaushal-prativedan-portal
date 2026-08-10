import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { processingApi } from "../../lib/processing";
import type { ProcessingProgress } from "../../lib/processing";

type Props = {
  sessionId: number;
  onProgress: (progress: ProcessingProgress) => void;
};

export function StepProcessing({ sessionId, onProgress }: Props) {
  const progressQ = useQuery({
    queryKey: ["processing-progress", sessionId],
    queryFn: () => processingApi.progress(sessionId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "PROCESSING") return 2000;
      return false;
    },
  });

  const progress = progressQ.data;

  useEffect(() => {
    if (progress) {
      onProgress(progress);
    }
  }, [progress, onProgress]);

  const total = progress?.total ?? 0;
  const processed = progress?.processed ?? 0;
  const successful = progress?.successful ?? 0;
  const failed = progress?.failed ?? 0;
  const remaining = progress?.remaining ?? 0;
  const percent = total > 0 ? Math.round((processed / total) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-sm font-medium text-slate-700">
            Processing OMR sheets...
          </p>
          <p className="text-sm text-slate-500">{percent}%</p>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
          <div
            className="h-full rounded-full bg-blue-600 transition-all duration-300"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      {/* Counters */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <CounterCard label="Total" value={total} color="bg-slate-100 text-slate-700" />
        <CounterCard label="Processed" value={processed} color="bg-blue-100 text-blue-700" />
        <CounterCard label="Successful" value={successful} color="bg-green-100 text-green-700" />
        <CounterCard label="Failed" value={failed} color="bg-red-100 text-red-700" />
      </div>

      {/* Remaining */}
      {remaining > 0 && (
        <div className="text-center text-sm text-slate-500">
          {remaining} file{remaining !== 1 ? "s" : ""} remaining
        </div>
      )}

      {/* Loading indicator */}
      {progressQ.isPending && (
        <div className="flex items-center justify-center gap-2 py-4 text-sm text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
          Starting processing...
        </div>
      )}
    </div>
  );
}

function CounterCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={`rounded-lg p-3 text-center ${color}`}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs font-medium">{label}</p>
    </div>
  );
}
