import { api } from "./api";

// ── Types ──────────────────────────────────────────────────────────

export type DomainBreakdown = {
  domain: string;
  correct: number;
  total: number;
  percentage: number;
};

export type SchoolSummaryForAnalytics = {
  school_id: number;
  school_name: string;
  students_assessed: number;
  average_score: number;
  average_percentage: number;
  highest_percentage: number;
  lowest_percentage: number;
  domains: DomainBreakdown[];
  school_rank: number;
};

export type StudentInSchool = {
  student_id: number;
  student_name: string;
  roll_number: number;
  score: number;
  total_questions: number;
  percentage: number;
};

export type AssessmentOverview = {
  assessment_id: number;
  total_students_assessed: number;
  average_score: number;
  average_percentage: number;
  highest_percentage: number;
  lowest_percentage: number;
  domains: DomainBreakdown[];
  schools: SchoolSummaryForAnalytics[];
};

export type SchoolDetail = {
  assessment_id: number;
  school_id: number;
  school_name: string;
  students_assessed: number;
  average_score: number;
  average_percentage: number;
  highest_percentage: number;
  lowest_percentage: number;
  domains: DomainBreakdown[];
  school_rank: number | null;
  students: StudentInSchool[];
};

export type StudentDetail = {
  assessment_id: number;
  student_id: number;
  student_name: string;
  roll_number: number;
  school_id: number;
  school_name: string;
  current_class: number;
  current_section: string;
  score: number;
  total_questions: number;
  wrong: number;
  percentage: number;
  domains: DomainBreakdown[];
  school_average: number;
  overall_average: number;
  school_rank: number;
  overall_rank: number;
  school_percentile: number;
  overall_percentile: number;
};

export type QuestionItem = {
  question_id: number;
  question_number: number;
  question_text: string | null;
  domain: string;
  assessed: number;
  correct: number;
  wrong: number;
  percentage: number;
};

export type QuestionAnalytics = {
  assessment_id: number;
  total_students_assessed: number;
  scope: { school_id: number | null; class_number: number | null; section: string | null };
  questions: QuestionItem[];
};

export type HistoricalAppearance = {
  assessment_id: number;
  assessment_name: string;
  academic_year: string;
  assessment_type: string;
  question_number: number;
  assessed: number;
  correct: number;
  percentage: number;
};

export type QuestionHistory = {
  question_id: number;
  question_number: number;
  question_text: string | null;
  domain: string;
  fingerprint_valid: boolean;
  fingerprint_match_count: number;
  current: HistoricalAppearance;
  history: HistoricalAppearance[];
};

// ── API Functions ──────────────────────────────────────────────────

export const analyticsApi = {
  overview: (assessmentId: number, params?: { school_id?: number; class_number?: number; section?: string }) =>
    api.get<AssessmentOverview>(`/analytics/assessments/${assessmentId}/overview`, { params }).then((r) => r.data),

  schoolDetail: (assessmentId: number, schoolId: number) =>
    api.get<SchoolDetail>(`/analytics/assessments/${assessmentId}/schools/${schoolId}`).then((r) => r.data),

  studentDetail: (assessmentId: number, studentId: number) =>
    api.get<StudentDetail>(`/analytics/assessments/${assessmentId}/students/${studentId}`).then((r) => r.data),

  questionAnalytics: (assessmentId: number, params?: { school_id?: number; class_number?: number; section?: string }) =>
    api.get<QuestionAnalytics>(`/analytics/assessments/${assessmentId}/questions`, { params }).then((r) => r.data),

  questionHistory: (assessmentId: number, questionId: number, params?: { school_id?: number; class_number?: number; section?: string }) =>
    api.get<QuestionHistory>(`/analytics/assessments/${assessmentId}/questions/${questionId}/history`, { params }).then((r) => r.data),
};
