import type { ProcessingSession, ProcessingFile } from "../../lib/processing";
import {
  FILE_STATUS_LABELS,
  FILE_STATUS_COLORS,
  SESSION_STATUS_LABELS,
  SESSION_STATUS_COLORS,
} from "../../lib/processing";

type Props = {
  session: ProcessingSession;
};

export function StepReview({ session }: Props) {
  const validFiles = session.files.filter((f) => f.status === "VALID");
  const invalidFiles = session.files.filter((f) => f.status === "INVALID");

  return (
    <div className="space-y-6">
      {/* Session Metadata */}
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Session #{session.id}
          </p>
          <span
            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
              SESSION_STATUS_COLORS[session.status]
            }`}
          >
            {SESSION_STATUS_LABELS[session.status]}
          </span>
        </div>
        <div className="mt-2 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
          <div>
            <span className="text-slate-500">Assessment:</span>{" "}
            <span className="font-medium text-slate-900">{session.assessment.name}</span>
          </div>
          <div>
            <span className="text-slate-500">School:</span>{" "}
            <span className="font-medium text-slate-900">{session.school.name}</span>
          </div>
          <div>
            <span className="text-slate-500">Type:</span>{" "}
            <span className="font-medium text-slate-900">{session.assessment.assessment_type}</span>
          </div>
          <div>
            <span className="text-slate-500">Class:</span>{" "}
            <span className="font-medium text-slate-900">Class {session.assessment.class_number}</span>
          </div>
          <div>
            <span className="text-slate-500">Questions:</span>{" "}
            <span className="font-medium text-slate-900">{session.assessment.question_count}</span>
          </div>
          <div>
            <span className="text-slate-500">Total Files:</span>{" "}
            <span className="font-medium text-slate-900">{session.total_files}</span>
          </div>
        </div>
      </div>

      {/* Valid Files */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-green-100 text-xs font-bold text-green-700">
            {validFiles.length}
          </span>
          <h3 className="text-sm font-semibold text-slate-700">Valid Files</h3>
        </div>

        {validFiles.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-center text-sm text-slate-500">
            No valid files
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Filename</th>
                  <th className="px-4 py-3 font-medium">Roll Number</th>
                  <th className="px-4 py-3 font-medium">Student</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {validFiles.map((f: ProcessingFile) => (
                  <tr key={f.id} className="border-t">
                    <td className="px-4 py-3 font-medium text-slate-900">{f.original_filename}</td>
                    <td className="px-4 py-3 text-slate-700">{f.roll_number}</td>
                    <td className="px-4 py-3 text-slate-700">{f.student_name ?? "—"}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${FILE_STATUS_COLORS[f.status]}`}>
                        {FILE_STATUS_LABELS[f.status]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Invalid Files */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-red-100 text-xs font-bold text-red-700">
            {invalidFiles.length}
          </span>
          <h3 className="text-sm font-semibold text-slate-700">Invalid Files</h3>
        </div>

        {invalidFiles.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-4 text-center text-sm text-slate-500">
            No invalid files
          </div>
        ) : (
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
                {invalidFiles.map((f: ProcessingFile) => (
                  <tr key={f.id} className="border-t">
                    <td className="px-4 py-3 font-medium text-slate-900">{f.original_filename}</td>
                    <td className="px-4 py-3 text-slate-700">{f.roll_number || "—"}</td>
                    <td className="px-4 py-3 text-sm text-red-600">{f.error_message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Hint */}
      {invalidFiles.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
          <strong>Action required:</strong> Invalid files cannot be processed. Remove them and re-upload corrected files if needed. Only valid files will be processed.
        </div>
      )}
    </div>
  );
}
