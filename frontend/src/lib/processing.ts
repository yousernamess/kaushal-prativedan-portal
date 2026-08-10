import { api } from "./api";

// ── Types ──────────────────────────────────────────────────────────

export type ProcessingSessionStatus =
  | "PENDING"
  | "VALIDATING"
  | "READY"
  | "PROCESSING"
  | "COMPLETED"
  | "PARTIAL"
  | "FAILED";

export type ProcessingFileStatus =
  | "PENDING"
  | "VALID"
  | "INVALID"
  | "PROCESSED"
  | "FAILED"
  | "RETRYING";

export type AssessmentSummary = {
  id: number;
  name: string;
  assessment_type: "Baseline" | "Endline";
  academic_year_name: string;
  class_number: number;
  question_count: number;
};

export type SchoolSummary = {
  id: number;
  name: string;
  student_count: number;
};

export type AttemptQuestion = {
  id: number;
  attempt_id: number;
  question_id: number;
  detected_answer: string | null;
  correct_answer: string;
  is_correct: boolean;
  domain: string;
};

export type Attempt = {
  id: number;
  assessment_id: number;
  student_id: number;
  processing_session_id: number;
  score: number;
  total_questions: number;
  percentage: number;
  status: "COMPLETED" | "FAILED";
  created_at: string;
  completed_at: string | null;
  questions: AttemptQuestion[];
};

export type ProcessingFile = {
  id: number;
  session_id: number;
  original_filename: string;
  roll_number: number;
  student_id: number | null;
  student_name: string | null;
  status: ProcessingFileStatus;
  error_message: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
  attempt: Attempt | null;
};

export type ProcessingSession = {
  id: number;
  assessment_id: number;
  school_id: number;
  status: ProcessingSessionStatus;
  total_files: number;
  valid_files: number;
  invalid_files: number;
  processed_files: number;
  successful_files: number;
  failed_files: number;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  assessment: AssessmentSummary;
  school: SchoolSummary;
  files: ProcessingFile[];
};

export type ProcessingProgress = {
  session_id: number;
  status: ProcessingSessionStatus;
  total: number;
  processed: number;
  successful: number;
  failed: number;
  remaining: number;
};

// ── Status Helpers ─────────────────────────────────────────────────

export const SESSION_STATUS_LABELS: Record<ProcessingSessionStatus, string> = {
  PENDING: "Pending",
  VALIDATING: "Validating",
  READY: "Ready",
  PROCESSING: "Processing",
  COMPLETED: "Completed",
  PARTIAL: "Partial",
  FAILED: "Failed",
};

export const FILE_STATUS_LABELS: Record<ProcessingFileStatus, string> = {
  PENDING: "Pending",
  VALID: "Valid",
  INVALID: "Invalid",
  PROCESSED: "Processed",
  FAILED: "Failed",
  RETRYING: "Retrying",
};

export const SESSION_STATUS_COLORS: Record<ProcessingSessionStatus, string> = {
  PENDING: "bg-slate-100 text-slate-700",
  VALIDATING: "bg-blue-100 text-blue-700",
  READY: "bg-green-100 text-green-700",
  PROCESSING: "bg-amber-100 text-amber-700",
  COMPLETED: "bg-green-100 text-green-700",
  PARTIAL: "bg-orange-100 text-orange-700",
  FAILED: "bg-red-100 text-red-700",
};

export const FILE_STATUS_COLORS: Record<ProcessingFileStatus, string> = {
  PENDING: "bg-slate-100 text-slate-700",
  VALID: "bg-green-100 text-green-700",
  INVALID: "bg-red-100 text-red-700",
  PROCESSED: "bg-green-100 text-green-700",
  FAILED: "bg-red-100 text-red-700",
  RETRYING: "bg-amber-100 text-amber-700",
};

// ── API Functions ──────────────────────────────────────────────────

export const processingApi = {
  /** Create a new processing session with uploaded files. */
  create: (assessmentId: number, schoolId: number, files: File[]) => {
    const formData = new FormData();
    formData.append("assessment_id", String(assessmentId));
    formData.append("school_id", String(schoolId));
    files.forEach((file) => formData.append("files", file));
    return api
      .post<ProcessingSession>("/processing-sessions", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        params: { assessment_id: assessmentId, school_id: schoolId },
      })
      .then((r) => r.data);
  },

  /** List all processing sessions. */
  list: (params?: { assessment_id?: number; school_id?: number }) =>
    api.get<ProcessingSession[]>("/processing-sessions", { params }).then((r) => r.data),

  /** Get a single processing session with all files. */
  get: (id: number) =>
    api.get<ProcessingSession>(`/processing-sessions/${id}`).then((r) => r.data),

  /** Delete a processing session and its files. */
  delete: (id: number) =>
    api.delete(`/processing-sessions/${id}`),

  /** Validate all pending files in a session. */
  validate: (id: number) =>
    api.post<ProcessingSession>(`/processing-sessions/${id}/validate`).then((r) => r.data),

  /** Start processing valid files in a session. */
  process: (id: number) =>
    api.post<ProcessingSession>(`/processing-sessions/${id}/process`).then((r) => r.data),

  /** Get processing progress for a session. */
  progress: (id: number) =>
    api.get<ProcessingProgress>(`/processing-sessions/${id}/progress`).then((r) => r.data),

  /** Retry failed files in a session. */
  retry: (id: number, fileIds: number[]) =>
    api.post<ProcessingSession>(`/processing-sessions/${id}/retry`, { file_ids: fileIds }).then((r) => r.data),

  /** Delete a single file from a session. */
  deleteFile: (sessionId: number, fileId: number) =>
    api.delete(`/processing-sessions/${sessionId}/files/${fileId}`),
};
