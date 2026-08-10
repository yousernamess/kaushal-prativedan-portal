import { api } from "./api";

// ── Types ──────────────────────────────────────────────────────────

export type AssessmentType = "Baseline" | "Endline";

export type Question = {
  id: number;
  assessment_id: number;
  question_number: number;
  question_text?: string | null;
  option_a?: string | null;
  option_b?: string | null;
  option_c?: string | null;
  option_d?: string | null;
  correct_option: "A" | "B" | "C" | "D";
  domain: string;
};

export type Assessment = {
  id: number;
  name: string;
  assessment_type: AssessmentType;
  academic_year_id: number;
  academic_year_name?: string;
  class_number: number;
  is_deleted: boolean;
  created_at: string;
  updated_at: string;
  questions: Question[];
};

export type AssessmentCreatePayload = {
  name: string;
  assessment_type: AssessmentType;
  academic_year_id: number;
  class_number: number;
  questions?: {
    question_number: number;
    question_text?: string | null;
    option_a?: string | null;
    option_b?: string | null;
    option_c?: string | null;
    option_d?: string | null;
    correct_option: string;
    domain: string;
  }[];
};

export type AssessmentUpdatePayload = {
  name: string;
  assessment_type: AssessmentType;
  academic_year_id: number;
  class_number: number;
};

export type QuestionCreatePayload = {
  question_number: number;
  question_text?: string | null;
  option_a?: string | null;
  option_b?: string | null;
  option_c?: string | null;
  option_d?: string | null;
  correct_option: "A" | "B" | "C" | "D";
  domain: string;
};

export type QuestionUpdatePayload = {
  question_number: number;
  question_text?: string | null;
  option_a?: string | null;
  option_b?: string | null;
  option_c?: string | null;
  option_d?: string | null;
  correct_option: "A" | "B" | "C" | "D";
  domain: string;
};

// ── Constants ──────────────────────────────────────────────────────

export const ASSESSMENT_TYPES: { value: AssessmentType; label: string }[] = [
  { value: "Baseline", label: "Baseline" },
  { value: "Endline", label: "Endline" },
];

export const CLASS_OPTIONS = [
  { value: 6, label: "Class 6" },
  { value: 7, label: "Class 7" },
  { value: 8, label: "Class 8" },
];

export const ANSWER_OPTIONS = ["A", "B", "C", "D"];

export const DOMAIN_OPTIONS = [
  { value: "Knowledge", label: "Knowledge" },
  { value: "Understanding", label: "Understanding" },
  { value: "Application", label: "Application" },
  { value: "Analysis", label: "Analysis" },
  { value: "Evaluation", label: "Evaluation" },
];

// ── API Functions ──────────────────────────────────────────────────

export const assessmentApi = {
  // List assessments with optional filters
  list: (params?: { academic_year_id?: number; class_number?: number }) =>
    api.get<Assessment[]>("/assessments", { params }).then((r) => r.data),

  // Get single assessment with questions
  get: (id: number) =>
    api.get<Assessment>(`/assessments/${id}`).then((r) => r.data),

  // Create assessment
  create: (payload: AssessmentCreatePayload) =>
    api.post<Assessment>("/assessments", payload).then((r) => r.data),

  // Update assessment
  update: (id: number, payload: AssessmentUpdatePayload) =>
    api.put<Assessment>(`/assessments/${id}`, payload).then((r) => r.data),

  // Delete assessment (soft delete)
  delete: (id: number) =>
    api.delete(`/assessments/${id}`),

  // Duplicate assessment
  duplicate: (id: number) =>
    api.post<Assessment>(`/assessments/${id}/duplicate`).then((r) => r.data),

  // Add question to assessment
  addQuestion: (assessmentId: number, payload: QuestionCreatePayload) =>
    api.post<Question>(`/assessments/${assessmentId}/questions`, payload).then((r) => r.data),

  // Update question
  updateQuestion: (questionId: number, payload: QuestionUpdatePayload) =>
    api.put<Question>(`/assessments/questions/${questionId}`, payload).then((r) => r.data),

  // Delete question
  deleteQuestion: (questionId: number) =>
    api.delete(`/assessments/questions/${questionId}`),

  // Export assessment questions as CSV (downloads a file)
  exportCsv: async (assessmentId: number, fileName: string) => {
    const res = await api.get(`/assessments/${assessmentId}/export`, {
      responseType: "blob",
    });
    // Construct a download URL from the blob and trigger a click.
    const url = window.URL.createObjectURL(res.data as Blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${fileName}-questions.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  // Import questions into an assessment from a CSV file (replaces existing)
  importCsv: (assessmentId: number, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api
      .post<Assessment>(`/assessments/${assessmentId}/import`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
};
