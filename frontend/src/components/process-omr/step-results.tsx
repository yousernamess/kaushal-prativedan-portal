import { useMutation, useQueryClient } from "@tanstack/react-query";
import { processingApi } from "../../lib/processing";
import type { ProcessingSession, ProcessingFile } from "../../lib/processing";
import { FILE_STATUS_LABELS, FILE_STATUS_COLORS } from "../../lib/processing";
import { Button } from "../ui/button";
import { useToast } from "../common/toast";

type Props = {
  session: ProcessingSession;
  onNewSession: () => void;
};

export function StepResults({ session, onNewSession }: Props) {
  const toast = useToast();
  const qc = useQueryClient();

  const retryMutation = useMutation({
    mutationFn: (fileIds: number[]) => processingApi.retry(session.id, fileIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["processing-sessions"] });
      qc.invalidateQueries({ queryKey: ["processing-progress", session.id] });
      toast("Retry started for failed files");
    },
    onError: (err: unknown) => {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "Retry failed";
      toast(msg ?? "Retry failed");
    },
  });

  const files = session.files ?? [];
  const failedFiles = files.filter((f) => f.status === "FAILED");
  const retriableFiles = failedFiles.filter((f) => f.retry_count < 3);

  const handleRetry = () => {
    retryMutation.mutate(retriableFiles.map((f) => f.id));
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <SummaryCard
          label="Successful"
          value={session.successful_files}
          color="bg-green-50 border-green-200 text-green-800"
        />
        <SummaryCard
          label="Failed"
          value={session.failed_files}
          color="bg-red-50 border-red-200 text-red-800"
        />
        <SummaryCard
          label="Invalid"
          value={session.invalid_files}
          color="bg-orange-50 border-orange-200 text-orange-800"
        />
      </div>

      {/* Successful Files */}
      {session.successful_files > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-green-700">
            ✅ Successfully Processed ({session.successful_files})
          </h3>
          <div className="overflow-x-auto rounded-lg border bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Roll Number</th>
                  <th className="px-4 py-3 font-medium">Student</th>
                  <th className="px-4 py-3 font-medium text-center">Score</th>
                  <th className="px-4 py-3 font-medium text-center">Percentage</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {files
                  .filter((f) => f.status === "PROCESSED")
                  .map((f: ProcessingFile) => {
                    const att = f.attempt;
                    return (
                      <tr key={f.id} className="border-t">
                        <td className="px-4 py-3 text-slate-700">{f.roll_number}</td>
                        <td className="px-4 py-3 font-medium text-slate-900">{f.student_name ?? "—"}</td>
                        <td className="px-4 py-3 text-center font-medium text-slate-900">
                          {att ? `${att.score}/${att.total_questions}` : "—"}
                        </td>
                        <td className="px-4 py-3 text-center">
                          {att ? (
                            <span className={`font-semibold ${
                              (att.percentage ?? 0) >= 60 ? "text-green-700" : (att.percentage ?? 0) >= 40 ? "text-amber-700" : "text-red-700"
                            }`}>
                              {Number(att.percentage ?? 0).toFixed(1)}%
                            </span>
                          ) : "—"}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${FILE_STATUS_COLORS[f.status]}`}>
                            {FILE_STATUS_LABELS[f.status]}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Failed Files (processing failures) */}
      {failedFiles.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-semibold text-red-700">
              ❌ Processing Failed ({failedFiles.length})
            </h3>
            {retriableFiles.length > 0 && (
              <Button
                onClick={handleRetry}
                disabled={retryMutation.isPending}
                className="bg-amber-600 text-white hover:bg-amber-700"
              >
                {retryMutation.isPending ? "Retrying..." : `Retry ${retriableFiles.length} file${retriableFiles.length !== 1 ? "s" : ""}`}
              </Button>
            )}
          </div>
          <div className="overflow-x-auto rounded-lg border bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Filename</th>
                  <th className="px-4 py-3 font-medium">Roll Number</th>
                  <th className="px-4 py-3 font-medium">Error</th>
                  <th className="px-4 py-3 font-medium">Retries</th>
                </tr>
              </thead>
              <tbody>
                {failedFiles.map((f: ProcessingFile) => (
                  <tr key={f.id} className="border-t">
                    <td className="px-4 py-3 font-medium text-slate-900">{f.original_filename}</td>
                    <td className="px-4 py-3 text-slate-700">{f.roll_number}</td>
                    <td className="px-4 py-3 text-sm text-red-600">{f.error_message}</td>
                    <td className="px-4 py-3 text-slate-500">{f.retry_count}/{3}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
            These files failed during OMR extraction. You can retry them using the same uploaded files — no re-upload needed.
          </div>
        </div>
      )}

      {/* Invalid Files (validation failures) */}
      {session.invalid_files > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-orange-700">
            ⚠️ Validation Failed ({session.invalid_files})
          </h3>
          <div className="overflow-x-auto rounded-lg border bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Filename</th>
                  <th className="px-4 py-3 font-medium">Roll Number</th>
                  <th className="px-4 py-3 font-medium">Reason</th>
                </tr>
              </thead>
              <tbody>
                {files
                  .filter((f) => f.status === "INVALID")
                  .map((f: ProcessingFile) => (
                    <tr key={f.id} className="border-t">
                      <td className="px-4 py-3 font-medium text-slate-900">{f.original_filename}</td>
                      <td className="px-4 py-3 text-slate-700">{f.roll_number || "—"}</td>
                      <td className="px-4 py-3 text-sm text-orange-600">{f.error_message}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <div className="mt-2 rounded-lg border border-orange-200 bg-orange-50 p-3 text-sm text-orange-700">
            These files failed validation before processing. To fix: remove them and re-upload corrected files in a new session.
          </div>
        </div>
      )}

      {/* New Session Button */}
      <div className="flex justify-center pt-4">
        <Button onClick={onNewSession} variant="ghost">
          Start New Session
        </Button>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={`rounded-lg border p-4 text-center ${color}`}>
      <p className="text-3xl font-bold">{value}</p>
      <p className="text-sm font-medium">{label}</p>
    </div>
  );
}
