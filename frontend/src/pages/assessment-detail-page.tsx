import { useState, useMemo, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Plus, Pencil, Trash2, Copy, AlertTriangle, Upload, Download } from "lucide-react";
import { Button } from "../components/ui/button";
import { DataTable } from "../components/common/data-table";
import { DeleteConfirmationDialog } from "../components/common/delete-confirmation-dialog";
import { useToast } from "../components/common/toast";
import { assessmentApi, CLASS_OPTIONS, ASSESSMENT_TYPES, ANSWER_OPTIONS, DOMAIN_OPTIONS } from "../lib/assessments";
import type { Assessment, Question } from "../lib/assessments";
import type { AcademicYear } from "../lib/master-data";
import { masterApi } from "../lib/master-data";

// ── Helpers ────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response;
    if (resp?.data?.detail) return resp.data.detail;
  }
  return "Something went wrong. Please try again.";
}

// ── QuestionForm ───────────────────────────────────────────────────

type QuestionFormValues = {
  question_number: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_option: string;
  domain: string;
};

function QuestionForm({
  open,
  title,
  values,
  existingNumbers,
  loading,
  error,
  onClose,
  onSubmit,
}: {
  open: boolean;
  title: string;
  values: QuestionFormValues;
  existingNumbers: number[];
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (values: QuestionFormValues) => void;
}) {
  const [form, setForm] = useState(values);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // Reset form when dialog opens with new values
  useEffect(() => {
    if (open) {
      setForm(values);
      setTouched({});
    }
  }, [open, values.question_number, values.question_text, values.option_a, values.option_b, values.option_c, values.option_d, values.correct_option, values.domain]);

  if (!open) return null;

  const set = (k: string, v: string) => {
    setForm((prev) => ({ ...prev, [k]: v }));
    setTouched((prev) => ({ ...prev, [k]: true }));
  };

  const errors: Record<string, string> = {};
  const qNum = Number(form.question_number);

  if (touched.question_number) {
    if (!form.question_number) {
      errors.question_number = "Question number is required";
    } else if (isNaN(qNum) || qNum < 1 || qNum > 40) {
      errors.question_number = "Must be between 1 and 40";
    } else if (existingNumbers.includes(qNum)) {
      errors.question_number = `Question ${qNum} already exists in this assessment`;
    }
  }
  if (touched.correct_option && !form.correct_option) {
    errors.correct_option = "Correct answer is required";
  }
  if (touched.domain && !form.domain.trim()) {
    errors.domain = "Domain is required";
  }

  const isValid =
    form.question_number &&
    !isNaN(qNum) &&
    qNum >= 1 &&
    qNum <= 40 &&
    !existingNumbers.includes(qNum) &&
    form.correct_option &&
    form.domain.trim();

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (isValid) onSubmit(form);
        }}
        className="w-full max-w-md space-y-4 rounded-lg bg-white p-6 shadow-xl"
      >
        <h3 className="text-lg font-semibold">{title}</h3>

        {error && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        {/* Question Number */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Question Number <span className="text-red-500">*</span>
          </span>
          <input
            className={`mt-1 h-10 w-full rounded border px-3 text-sm ${errors.question_number ? "border-red-400" : "border-slate-300"}`}
            type="number"
            min={1}
            max={40}
            value={form.question_number}
            onChange={(e) => set("question_number", e.target.value)}
            placeholder="e.g. 1"
          />
          {errors.question_number && (
            <span className="mt-0.5 block text-xs text-red-600">{errors.question_number}</span>
          )}
        </label>

        {/* Question Text */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Question Text
          </span>
          <textarea
            className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm"
            rows={3}
            value={form.question_text}
            onChange={(e) => set("question_text", e.target.value)}
            placeholder="Enter the question text (optional)"
          />
        </label>

        {/* Options */}
        <div className="space-y-2">
          <span className="text-sm font-medium text-slate-700">Options (optional)</span>
          <div className="grid grid-cols-2 gap-2">
            <label className="block text-sm">
              <span className="text-slate-600">Option A</span>
              <input
                className="mt-1 h-10 w-full rounded border border-slate-300 px-3 text-sm"
                value={form.option_a}
                onChange={(e) => set("option_a", e.target.value)}
                placeholder="Option A"
              />
            </label>
            <label className="block text-sm">
              <span className="text-slate-600">Option B</span>
              <input
                className="mt-1 h-10 w-full rounded border border-slate-300 px-3 text-sm"
                value={form.option_b}
                onChange={(e) => set("option_b", e.target.value)}
                placeholder="Option B"
              />
            </label>
            <label className="block text-sm">
              <span className="text-slate-600">Option C</span>
              <input
                className="mt-1 h-10 w-full rounded border border-slate-300 px-3 text-sm"
                value={form.option_c}
                onChange={(e) => set("option_c", e.target.value)}
                placeholder="Option C"
              />
            </label>
            <label className="block text-sm">
              <span className="text-slate-600">Option D</span>
              <input
                className="mt-1 h-10 w-full rounded border border-slate-300 px-3 text-sm"
                value={form.option_d}
                onChange={(e) => set("option_d", e.target.value)}
                placeholder="Option D"
              />
            </label>
          </div>
        </div>

        {/* Correct Answer */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Correct Answer <span className="text-red-500">*</span>
          </span>
          <select
            className={`mt-1 h-10 w-full rounded border bg-white px-3 text-sm ${errors.correct_option ? "border-red-400" : "border-slate-300"}`}
            value={form.correct_option}
            onChange={(e) => set("correct_option", e.target.value)}
          >
            <option value="">Select answer</option>
            {ANSWER_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
          {errors.correct_option && (
            <span className="mt-0.5 block text-xs text-red-600">{errors.correct_option}</span>
          )}
        </label>

        {/* Domain */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Domain <span className="text-red-500">*</span>
          </span>
          <select
            className={`mt-1 h-10 w-full rounded border bg-white px-3 text-sm ${errors.domain ? "border-red-400" : "border-slate-300"}`}
            value={form.domain}
            onChange={(e) => set("domain", e.target.value)}
          >
            <option value="">Select domain</option>
            {DOMAIN_OPTIONS.map((d) => (
              <option key={d.value} value={d.value}>{d.label}</option>
            ))}
          </select>
          {errors.domain && (
            <span className="mt-0.5 block text-xs text-red-600">{errors.domain}</span>
          )}
        </label>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button type="submit" disabled={loading || !isValid}>
            {loading ? "Saving..." : title.includes("Add") ? "Add Question" : "Save Changes"}
          </Button>
        </div>
      </form>
    </div>
  );
}

// ── DuplicateAssessmentDialog ──────────────────────────────────────

function DuplicateAssessmentDialog({
  open,
  assessment,
  academicYears,
  loading,
  error,
  onClose,
  onDuplicate,
}: {
  open: boolean;
  assessment: Assessment | null;
  academicYears: AcademicYear[];
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onDuplicate: (payload: { name: string; assessment_type: string; academic_year_id: number; class_number: number }) => void;
}) {
  const [name, setName] = useState("");
  const [assessmentType, setAssessmentType] = useState("");
  const [academicYearId, setAcademicYearId] = useState("");
  const [classNumber, setClassNumber] = useState("");

  if (!open || !assessment) return null;

  const defaultName = `${assessment.name} (Copy)`;
  const displayName = name.trim() || defaultName;
  const displayType = assessmentType || assessment.assessment_type;
  const displayYear = academicYearId ? Number(academicYearId) : assessment.academic_year_id;
  const displayClass = classNumber ? Number(classNumber) : assessment.class_number;

  const isValid = displayName.trim() && displayType && displayYear && displayClass;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (isValid) {
            onDuplicate({
              name: displayName.trim(),
              assessment_type: displayType,
              academic_year_id: displayYear,
              class_number: displayClass,
            });
          }
        }}
        className="w-full max-w-md space-y-4 rounded-lg bg-white p-6 shadow-xl"
      >
        <h3 className="text-lg font-semibold">Duplicate Assessment</h3>

        <div className="rounded-lg bg-slate-50 p-4">
          <p className="text-sm text-slate-600">You are duplicating:</p>
          <p className="mt-1 font-medium text-slate-900">{assessment.name}</p>
          <p className="mt-0.5 text-sm text-slate-500">
            Class {assessment.class_number} · {assessment.assessment_type}
          </p>
        </div>

        {error && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            New Assessment Name <span className="text-red-500">*</span>
          </span>
          <input
            className="mt-1 h-10 w-full rounded border border-slate-300 px-3 text-sm"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={defaultName}
          />
          <span className="mt-0.5 block text-xs text-slate-400">Leave blank to use "{defaultName}"</span>
        </label>

        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Assessment Type <span className="text-red-500">*</span>
          </span>
          <select
            className="mt-1 h-10 w-full rounded border bg-white px-3 text-sm"
            value={assessmentType || assessment.assessment_type}
            onChange={(e) => setAssessmentType(e.target.value)}
          >
            {ASSESSMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Academic Year <span className="text-red-500">*</span>
          </span>
          <select
            className="mt-1 h-10 w-full rounded border bg-white px-3 text-sm"
            value={academicYearId || assessment.academic_year_id}
            onChange={(e) => setAcademicYearId(e.target.value)}
          >
            {academicYears.map((y) => (
              <option key={y.id} value={y.id}>{y.name}</option>
            ))}
          </select>
        </label>

        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Class <span className="text-red-500">*</span>
          </span>
          <select
            className="mt-1 h-10 w-full rounded border bg-white px-3 text-sm"
            value={classNumber || assessment.class_number}
            onChange={(e) => setClassNumber(e.target.value)}
          >
            {CLASS_OPTIONS.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </label>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button type="submit" disabled={loading || !isValid}>
            {loading ? "Duplicating..." : "Duplicate Assessment"}
          </Button>
        </div>
      </form>
    </div>
  );
}

// ── AssessmentDetailPage ───────────────────────────────────────────

export function AssessmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const qc = useQueryClient();
  const assessmentId = Number(id);

  // Dialogs
  const [addQuestionOpen, setAddQuestionOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<Question | null>(null);
  const [deletingQuestion, setDeletingQuestion] = useState<Question | null>(null);
  const [editAssessmentOpen, setEditAssessmentOpen] = useState(false);
  const [deleteAssessmentOpen, setDeleteAssessmentOpen] = useState(false);
  const [duplicating, setDuplicating] = useState(false);
  const [duplicateLoading, setDuplicateLoading] = useState(false);

  // CSV import/export
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [importError, setImportError] = useState<string | null>(null);

  // Errors
  const [addQuestionError, setAddQuestionError] = useState<string | null>(null);
  const [editQuestionError, setEditQuestionError] = useState<string | null>(null);
  const [editAssessmentError, setEditAssessmentError] = useState<string | null>(null);
  const [duplicateError, setDuplicateError] = useState<string | null>(null);

  // Queries
  const academicYears = useQuery({
    queryKey: ["academic-years"],
    queryFn: masterApi.years,
  });

  const assessment = useQuery({
    queryKey: ["assessment", assessmentId],
    queryFn: () => assessmentApi.get(assessmentId),
    enabled: !isNaN(assessmentId),
  });

  // Sorted questions by question number
  const sortedQuestions = useMemo(() => {
    if (!assessment.data?.questions) return [];
    return [...assessment.data.questions].sort((a, b) => a.question_number - b.question_number);
  }, [assessment.data?.questions]);

  // Check for missing question numbers
  const missingNumbers = useMemo(() => {
    if (sortedQuestions.length === 0) return [];
    const numbers = new Set(sortedQuestions.map((q) => q.question_number));
    const missing: number[] = [];
    for (let i = 1; i <= Math.max(...sortedQuestions.map((q) => q.question_number)); i++) {
      if (!numbers.has(i)) missing.push(i);
    }
    return missing;
  }, [sortedQuestions]);

  // Existing question numbers (for validation)
  const existingNumbers = useMemo(() => {
    return sortedQuestions.map((q) => q.question_number);
  }, [sortedQuestions]);

  // Mutations - Assessment
  const updateAssessment = useMutation({
    mutationFn: (v: { name: string; assessment_type: string; academic_year_id: string; class_number: string }) =>
      assessmentApi.update(assessmentId, {
        name: v.name.trim(),
        assessment_type: v.assessment_type as "Baseline" | "Endline",
        academic_year_id: Number(v.academic_year_id),
        class_number: Number(v.class_number),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessment", assessmentId] });
      qc.invalidateQueries({ queryKey: ["assessments"] });
      setEditAssessmentOpen(false);
      setEditAssessmentError(null);
      toast("Assessment updated successfully");
    },
    onError: (err) => setEditAssessmentError(extractErrorMessage(err)),
  });

  const deleteAssessment = useMutation({
    mutationFn: () => assessmentApi.delete(assessmentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessments"] });
      setDeleteAssessmentOpen(false);
      toast("Assessment deleted");
      navigate("/assessments");
    },
    onError: (err) => {
      toast(extractErrorMessage(err));
      setDeleteAssessmentOpen(false);
    },
  });

  // Mutations - CSV import/export
  const exportCsv = useMutation({
    mutationFn: () => assessmentApi.exportCsv(assessmentId, assessment.data?.name || "assessment"),
    onSuccess: () => toast("Questions exported to CSV"),
    onError: (err) => toast(extractErrorMessage(err)),
  });

  const importCsv = useMutation({
    mutationFn: (file: File) => assessmentApi.importCsv(assessmentId, file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessment", assessmentId] });
      qc.invalidateQueries({ queryKey: ["assessments"] });
      setImportError(null);
      toast("Questions imported successfully");
    },
    onError: (err) => setImportError(extractErrorMessage(err)),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setImportError("Please select a .csv file");
      return;
    }
    setImportError(null);
    if (window.confirm("Importing a CSV will replace all current questions in this assessment. Continue?")) {
      importCsv.mutate(file);
    }
  };

  // Mutations - Questions
  const addQuestion = useMutation({
    mutationFn: (v: QuestionFormValues) =>
      assessmentApi.addQuestion(assessmentId, {
        question_number: Number(v.question_number),
        question_text: v.question_text || null,
        option_a: v.option_a || null,
        option_b: v.option_b || null,
        option_c: v.option_c || null,
        option_d: v.option_d || null,
        correct_option: v.correct_option as "A" | "B" | "C" | "D",
        domain: v.domain,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessment", assessmentId] });
      setAddQuestionOpen(false);
      setAddQuestionError(null);
      toast("Question added");
    },
    onError: (err) => setAddQuestionError(extractErrorMessage(err)),
  });

  const updateQuestion = useMutation({
    mutationFn: (v: QuestionFormValues) =>
      assessmentApi.updateQuestion(editingQuestion!.id, {
        question_number: Number(v.question_number),
        question_text: v.question_text || null,
        option_a: v.option_a || null,
        option_b: v.option_b || null,
        option_c: v.option_c || null,
        option_d: v.option_d || null,
        correct_option: v.correct_option as "A" | "B" | "C" | "D",
        domain: v.domain,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessment", assessmentId] });
      setEditingQuestion(null);
      setEditQuestionError(null);
      toast("Question updated");
    },
    onError: (err) => setEditQuestionError(extractErrorMessage(err)),
  });

  const deleteQuestion = useMutation({
    mutationFn: () => assessmentApi.deleteQuestion(deletingQuestion!.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessment", assessmentId] });
      setDeletingQuestion(null);
      toast("Question deleted");
    },
    onError: (err) => {
      toast(extractErrorMessage(err));
      setDeletingQuestion(null);
    },
  });

  // Helper
  const getAcademicYearName = (yearId: number) => {
    const year = academicYears.data?.find((y) => y.id === yearId);
    return year?.name || `AY ${yearId}`;
  };

  // Invalid ID
  if (isNaN(assessmentId)) {
    return (
      <div className="py-12 text-center">
        <p className="text-sm text-slate-500">Invalid assessment ID.</p>
        <Button variant="ghost" className="mt-3" onClick={() => navigate("/assessments")}>
          <ArrowLeft size={16} className="mr-1" /> Back to Assessments
        </Button>
      </div>
    );
  }

  // Loading
  if (assessment.isPending) {
    return (
      <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
        Loading assessment...
      </div>
    );
  }

  // Error
  if (assessment.isError) {
    return (
      <div className="py-12 text-center">
        <div className="mx-auto max-w-md rounded-lg border border-red-200 bg-red-50 p-6 text-sm text-red-700">
          <p className="font-medium">Unable to load assessment</p>
          <p className="mt-1">The assessment may not exist or there was a connection error.</p>
          <div className="mt-4 flex justify-center gap-2">
            <Button variant="ghost" onClick={() => navigate("/assessments")}>
              <ArrowLeft size={16} className="mr-1" /> Back to Assessments
            </Button>
            <Button onClick={() => qc.invalidateQueries({ queryKey: ["assessment", assessmentId] })}>
              Try again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const a = assessment.data;

  return (
    <>
      {/* Back navigation */}
      <button
        onClick={() => navigate("/assessments")}
        className="mb-4 flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
      >
        <ArrowLeft size={16} /> Back to Assessments
      </button>

      {/* Assessment header */}
      <div className="mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">{a.name}</h2>
            <div className="mt-1 flex items-center gap-2 text-sm text-slate-500">
              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                a.assessment_type === "Baseline"
                  ? "bg-blue-50 text-blue-700"
                  : "bg-purple-50 text-purple-700"
              }`}>
                {a.assessment_type}
              </span>
              <span>·</span>
              <span>Class {a.class_number}</span>
              <span>·</span>
              <span>{getAcademicYearName(a.academic_year_id)}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" onClick={() => { setEditAssessmentError(null); setEditAssessmentOpen(true); }}>
              <Pencil size={14} className="mr-1" /> Edit
            </Button>
            <Button variant="ghost" onClick={() => { setDuplicateError(null); setDuplicating(true); }}>
              <Copy size={14} className="mr-1" /> Duplicate
            </Button>
            <Button variant="ghost" onClick={() => setDeleteAssessmentOpen(true)} className="text-red-600 hover:bg-red-50 hover:text-red-700">
              <Trash2 size={14} className="mr-1" /> Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Missing questions warning */}
      {missingNumbers.length > 0 && (
        <div className="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" />
          <div>
            <p className="font-medium">Missing question numbers</p>
            <p className="mt-0.5">
              Question{missingNumbers.length !== 1 ? "s" : ""} {missingNumbers.join(", ")} {missingNumbers.length !== 1 ? "are" : "is"} not defined.
            </p>
          </div>
        </div>
      )}

      {/* Questions section */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-slate-900">
          Questions
          <span className="ml-2 text-sm font-normal text-slate-500">
            ({sortedQuestions.length} question{sortedQuestions.length !== 1 ? "s" : ""})
          </span>
        </h3>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            disabled={exportCsv.isPending || sortedQuestions.length === 0}
            onClick={() => exportCsv.mutate()}
          >
            <Download size={16} className="mr-1" />
            {exportCsv.isPending ? "Exporting..." : "Export CSV"}
          </Button>
          <Button
            variant="ghost"
            disabled={importCsv.isPending}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={16} className="mr-1" />
            {importCsv.isPending ? "Importing..." : "Import CSV"}
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={handleFileChange}
          />
          <Button onClick={() => { setAddQuestionError(null); setAddQuestionOpen(true); }}>
            <Plus size={16} className="mr-1" /> Add Question
          </Button>
        </div>
      </div>

      {importError && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          Import failed: {importError}
        </div>
      )}

      {/* Questions loading */}
      {assessment.isPending && (
        <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
          Loading questions...
        </div>
      )}

      {/* Questions empty state */}
      {!assessment.isPending && sortedQuestions.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <p className="text-sm font-medium text-slate-700">No questions added yet</p>
          <p className="mt-1 text-sm text-slate-500">
            Add questions to define the answer key for this assessment.
          </p>
          <Button className="mt-4" onClick={() => { setAddQuestionError(null); setAddQuestionOpen(true); }}>
            <Plus size={16} className="mr-1" /> Add Question
          </Button>
        </div>
      )}

      {/* Questions table */}
      {!assessment.isPending && sortedQuestions.length > 0 && (
        <DataTable<Question>
          rows={sortedQuestions}
          columns={[
            {
              label: "Question",
              render: (r) => (
                <div>
                  <span className="font-medium text-slate-900">Q{r.question_number}</span>
                  {r.question_text && (
                    <p className="mt-0.5 text-xs text-slate-600 line-clamp-2">{r.question_text}</p>
                  )}
                </div>
              ),
            },
            {
              label: "Options",
              render: (r) => (
                <div className="text-xs text-slate-600">
                  {r.option_a && <p>A: {r.option_a}</p>}
                  {r.option_b && <p>B: {r.option_b}</p>}
                  {r.option_c && <p>C: {r.option_c}</p>}
                  {r.option_d && <p>D: {r.option_d}</p>}
                  {!r.option_a && !r.option_b && !r.option_c && !r.option_d && (
                    <span className="text-slate-400">—</span>
                  )}
                </div>
              ),
            },
            {
              label: "Answer",
              render: (r) => (
                <span className="inline-flex h-7 w-7 items-center justify-center rounded-md bg-green-50 text-sm font-semibold text-green-700">
                  {r.correct_option}
                </span>
              ),
            },
            {
              label: "Domain",
              render: (r) => (
                <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
                  {r.domain}
                </span>
              ),
            },
          ]}
          actions={(r) => (
            <div className="flex gap-1">
              <button
                className="rounded px-2 py-1 text-xs text-slate-600 hover:bg-slate-100"
                onClick={() => { setEditQuestionError(null); setEditingQuestion(r); }}
              >
                Edit
              </button>
              <button
                className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                onClick={() => setDeletingQuestion(r)}
              >
                Delete
              </button>
            </div>
          )}
        />
      )}

      {/* Add Question Dialog */}
      <QuestionForm
        open={addQuestionOpen}
        title="Add Question"
        values={{ question_number: "", question_text: "", option_a: "", option_b: "", option_c: "", option_d: "", correct_option: "", domain: "" }}
        existingNumbers={existingNumbers}
        loading={addQuestion.isPending}
        error={addQuestionError}
        onClose={() => { setAddQuestionOpen(false); setAddQuestionError(null); }}
        onSubmit={(v) => { setAddQuestionError(null); addQuestion.mutate(v); }}
      />

      {/* Edit Question Dialog */}
      <QuestionForm
        open={!!editingQuestion}
        title="Edit Question"
        values={editingQuestion ? {
          question_number: String(editingQuestion.question_number),
          question_text: editingQuestion.question_text || "",
          option_a: editingQuestion.option_a || "",
          option_b: editingQuestion.option_b || "",
          option_c: editingQuestion.option_c || "",
          option_d: editingQuestion.option_d || "",
          correct_option: editingQuestion.correct_option,
          domain: editingQuestion.domain,
        } : { question_number: "", question_text: "", option_a: "", option_b: "", option_c: "", option_d: "", correct_option: "", domain: "" }}
        existingNumbers={editingQuestion ? existingNumbers.filter((n) => n !== editingQuestion.question_number) : existingNumbers}
        loading={updateQuestion.isPending}
        error={editQuestionError}
        onClose={() => { setEditingQuestion(null); setEditQuestionError(null); }}
        onSubmit={(v) => { setEditQuestionError(null); updateQuestion.mutate(v); }}
      />

      {/* Delete Question Dialog */}
      <DeleteConfirmationDialog
        open={!!deletingQuestion}
        title={deletingQuestion ? `Delete Question ${deletingQuestion.question_number}?` : "Delete Question?"}
        message={deletingQuestion ? `This will remove Question ${deletingQuestion.question_number} from this assessment's answer key.` : "This action cannot be undone."}
        confirmLabel="Delete Question"
        loading={deleteQuestion.isPending}
        onClose={() => setDeletingQuestion(null)}
        onConfirm={() => deleteQuestion.mutate()}
      />

      {/* Edit Assessment Dialog */}
      {editAssessmentOpen && (
        <EditAssessmentDialog
          open={editAssessmentOpen}
          assessment={a}
          academicYears={academicYears.data || []}
          loading={updateAssessment.isPending}
          error={editAssessmentError}
          onClose={() => { setEditAssessmentOpen(false); setEditAssessmentError(null); }}
          onSubmit={(v) => { setEditAssessmentError(null); updateAssessment.mutate(v); }}
        />
      )}

      {/* Delete Assessment Dialog */}
      <DeleteConfirmationDialog
        open={deleteAssessmentOpen}
        title="Delete Assessment?"
        message={`Are you sure you want to delete "${a.name}"? This assessment will no longer appear in the assessment list.`}
        confirmLabel="Delete Assessment"
        loading={deleteAssessment.isPending}
        onClose={() => setDeleteAssessmentOpen(false)}
        onConfirm={() => deleteAssessment.mutate()}
      />

      {/* Duplicate Dialog */}
      {duplicating && (
        <DuplicateAssessmentDialog
          open={duplicating}
          assessment={a}
          academicYears={academicYears.data || []}
          loading={duplicateLoading}
          error={duplicateError}
          onClose={() => { setDuplicating(false); setDuplicateError(null); }}
          onDuplicate={(payload) => {
            setDuplicateError(null);
            setDuplicateLoading(true);
            // Duplicate then update with custom values
            assessmentApi.duplicate(assessmentId).then(async (newAssessment) => {
              const needsUpdate =
                payload.name !== `${a.name} (Copy)` ||
                payload.assessment_type !== a.assessment_type ||
                payload.academic_year_id !== a.academic_year_id ||
                payload.class_number !== a.class_number;
              if (needsUpdate) {
                return assessmentApi.update(newAssessment.id, {
                  name: payload.name,
                  assessment_type: payload.assessment_type as "Baseline" | "Endline",
                  academic_year_id: payload.academic_year_id,
                  class_number: payload.class_number,
                });
              }
              return newAssessment;
            }).then(() => {
              qc.invalidateQueries({ queryKey: ["assessments"] });
              setDuplicating(false);
              setDuplicateLoading(false);
              toast("Assessment duplicated successfully");
              navigate("/assessments");
            }).catch((err) => {
              setDuplicateError(extractErrorMessage(err));
              setDuplicateLoading(false);
            });
          }}
        />
      )}
    </>
  );
}

// ── EditAssessmentDialog ───────────────────────────────────────────

function EditAssessmentDialog({
  open,
  assessment,
  academicYears,
  loading,
  error,
  onClose,
  onSubmit,
}: {
  open: boolean;
  assessment: Assessment;
  academicYears: AcademicYear[];
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (values: { name: string; assessment_type: string; academic_year_id: string; class_number: string }) => void;
}) {
  const [form, setForm] = useState({
    name: assessment.name,
    assessment_type: assessment.assessment_type,
    academic_year_id: String(assessment.academic_year_id),
    class_number: String(assessment.class_number),
  });
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  if (!open) return null;

  const set = (k: string, v: string) => {
    setForm((prev) => ({ ...prev, [k]: v }));
    setTouched((prev) => ({ ...prev, [k]: true }));
  };

  const errors: Record<string, string> = {};
  if (touched.name && !form.name.trim()) errors.name = "Assessment name is required";
  if (touched.assessment_type && !form.assessment_type) errors.assessment_type = "Assessment type is required";
  if (touched.academic_year_id && !form.academic_year_id) errors.academic_year_id = "Academic year is required";
  if (touched.class_number && !form.class_number) errors.class_number = "Class is required";

  const isValid = form.name.trim() && form.assessment_type && form.academic_year_id && form.class_number;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (isValid) onSubmit(form);
        }}
        className="w-full max-w-md space-y-4 rounded-lg bg-white p-6 shadow-xl"
      >
        <h3 className="text-lg font-semibold">Edit Assessment</h3>

        {error && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Assessment Name <span className="text-red-500">*</span>
          </span>
          <input
            className={`mt-1 h-10 w-full rounded border px-3 text-sm ${errors.name ? "border-red-400" : "border-slate-300"}`}
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
          />
          {errors.name && <span className="mt-0.5 block text-xs text-red-600">{errors.name}</span>}
        </label>

        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Academic Year <span className="text-red-500">*</span>
          </span>
          <select
            className={`mt-1 h-10 w-full rounded border bg-white px-3 text-sm ${errors.academic_year_id ? "border-red-400" : "border-slate-300"}`}
            value={form.academic_year_id}
            onChange={(e) => set("academic_year_id", e.target.value)}
          >
            {academicYears.map((y) => (
              <option key={y.id} value={y.id}>{y.name}</option>
            ))}
          </select>
          {errors.academic_year_id && <span className="mt-0.5 block text-xs text-red-600">{errors.academic_year_id}</span>}
        </label>

        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Assessment Type <span className="text-red-500">*</span>
          </span>
          <select
            className={`mt-1 h-10 w-full rounded border bg-white px-3 text-sm ${errors.assessment_type ? "border-red-400" : "border-slate-300"}`}
            value={form.assessment_type}
            onChange={(e) => set("assessment_type", e.target.value)}
          >
            {ASSESSMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          {errors.assessment_type && <span className="mt-0.5 block text-xs text-red-600">{errors.assessment_type}</span>}
        </label>

        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Class <span className="text-red-500">*</span>
          </span>
          <select
            className={`mt-1 h-10 w-full rounded border bg-white px-3 text-sm ${errors.class_number ? "border-red-400" : "border-slate-300"}`}
            value={form.class_number}
            onChange={(e) => set("class_number", e.target.value)}
          >
            {CLASS_OPTIONS.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          {errors.class_number && <span className="mt-0.5 block text-xs text-red-600">{errors.class_number}</span>}
        </label>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button type="submit" disabled={loading || !isValid}>
            {loading ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </form>
    </div>
  );
}