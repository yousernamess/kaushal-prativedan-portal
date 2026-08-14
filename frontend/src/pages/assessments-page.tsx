import { useState, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, MoreVertical, Copy, Pencil, Trash2, Eye, X } from "lucide-react";
import { Button } from "../components/ui/button";
import { DataTable } from "../components/common/data-table";
import { PageHeader } from "../components/common/page-header";
import { SearchBar } from "../components/common/search-bar";
import { DeleteConfirmationDialog } from "../components/common/delete-confirmation-dialog";
import { useToast } from "../components/common/toast";
import { assessmentApi, CLASS_OPTIONS, ASSESSMENT_TYPES } from "../lib/assessments";
import type { Assessment } from "../lib/assessments";
import type { AcademicYear } from "../lib/master-data";
import { masterApi } from "../lib/master-data";

// ── Helpers ────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const resp = (err as { response?: { data?: { detail?: unknown } } }).response;
    const detail = resp?.data?.detail;
    if (detail) {
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0];
        if (first && typeof first === "object" && "msg" in first) return String((first as { msg: string }).msg);
      }
      return "Validation error. Please check your input.";
    }
  }
  return "Something went wrong. Please try again.";
}

// ── AssessmentForm ─────────────────────────────────────────────────

type AssessmentFormValues = {
  name: string;
  assessment_type: string;
  academic_year_id: string;
  class_number: string;
};

function AssessmentForm({
  open,
  title,
  values,
  academicYears,
  loading,
  error,
  onClose,
  onSubmit,
}: {
  open: boolean;
  title: string;
  values: AssessmentFormValues;
  academicYears: AcademicYear[];
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (values: AssessmentFormValues) => void;
}) {
  const [form, setForm] = useState(values);
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const prevOpen = useRef(open);

  if (!open) return null;

  const set = (k: string, v: string) => {
    setForm((prev) => ({ ...prev, [k]: v }));
    setTouched((prev) => ({ ...prev, [k]: true }));
  };

  // Reset form only when the dialog transitions from closed to open
  if (open && !prevOpen.current) {
    setForm(values);
    setTouched({});
  }
  prevOpen.current = open;

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
        <h3 className="text-lg font-semibold">{title}</h3>

        {error && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        {/* Assessment Name */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Assessment Name <span className="text-red-500">*</span>
          </span>
          <input
            className={`mt-1 h-10 w-full rounded border px-3 text-sm ${errors.name ? "border-red-400" : "border-slate-300"}`}
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            placeholder="e.g. Science Baseline 2026-27"
          />
          {errors.name && <span className="mt-0.5 block text-xs text-red-600">{errors.name}</span>}
        </label>

        {/* Academic Year */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Academic Year <span className="text-red-500">*</span>
          </span>
          <select
            className={`mt-1 h-10 w-full rounded border bg-white px-3 text-sm ${errors.academic_year_id ? "border-red-400" : "border-slate-300"}`}
            value={form.academic_year_id}
            onChange={(e) => set("academic_year_id", e.target.value)}
          >
            <option value="">Select academic year</option>
            {academicYears.map((y) => (
              <option key={y.id} value={y.id}>{y.name}</option>
            ))}
          </select>
          {errors.academic_year_id && <span className="mt-0.5 block text-xs text-red-600">{errors.academic_year_id}</span>}
        </label>

        {/* Assessment Type */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Assessment Type <span className="text-red-500">*</span>
          </span>
          <select
            className={`mt-1 h-10 w-full rounded border bg-white px-3 text-sm ${errors.assessment_type ? "border-red-400" : "border-slate-300"}`}
            value={form.assessment_type}
            onChange={(e) => set("assessment_type", e.target.value)}
          >
            <option value="">Select type</option>
            {ASSESSMENT_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
          {errors.assessment_type && <span className="mt-0.5 block text-xs text-red-600">{errors.assessment_type}</span>}
        </label>

        {/* Class */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">
            Class <span className="text-red-500">*</span>
          </span>
          <select
            className={`mt-1 h-10 w-full rounded border bg-white px-3 text-sm ${errors.class_number ? "border-red-400" : "border-slate-300"}`}
            value={form.class_number}
            onChange={(e) => set("class_number", e.target.value)}
          >
            <option value="">Select class</option>
            {CLASS_OPTIONS.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
          {errors.class_number && <span className="mt-0.5 block text-xs text-red-600">{errors.class_number}</span>}
        </label>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button type="submit" disabled={loading || !isValid}>
            {loading ? "Saving..." : title.includes("Create") ? "Create Assessment" : "Save Changes"}
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
  const [touched, setTouched] = useState<Record<string, boolean>>({});

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

        {/* New Assessment Name */}
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

        {/* Assessment Type */}
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

        {/* Academic Year */}
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

        {/* Class */}
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

// ── ActionMenu ─────────────────────────────────────────────────────

function ActionMenu({
  assessment,
  onOpen,
  onEdit,
  onDuplicate,
  onDelete,
}: {
  assessment: Assessment;
  onOpen: () => void;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [menuPos, setMenuPos] = useState({ top: 0, right: 0 });

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!open) {
      // Calculate position for fixed dropdown
      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
      setMenuPos({
        top: rect.bottom + 4,
        right: window.innerWidth - rect.right,
      });
    }
    setOpen(!open);
  };

  return (
    <div className="relative inline-block">
      <button
        onClick={handleClick}
        className="rounded p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
      >
        <MoreVertical size={16} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-[998]" onClick={() => setOpen(false)} />
          <div
            className="fixed z-[999] w-40 rounded-lg border bg-white py-1 shadow-lg"
            style={{ top: menuPos.top, right: menuPos.right }}
          >
            <button
              onClick={(e) => { e.stopPropagation(); setOpen(false); onOpen(); }}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              <Eye size={14} /> Open
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setOpen(false); onEdit(); }}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              <Pencil size={14} /> Edit
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setOpen(false); onDuplicate(); }}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            >
              <Copy size={14} /> Duplicate
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setOpen(false); onDelete(); }}
              className="flex w-full items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
            >
              <Trash2 size={14} /> Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// ── AssessmentsPage ────────────────────────────────────────────────

export function AssessmentsPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const qc = useQueryClient();

  // Filters
  const [search, setSearch] = useState("");
  const [academicYearFilter, setAcademicYearFilter] = useState("");
  const [classFilter, setClassFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  // Dialogs
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Assessment | null>(null);
  const [deleting, setDeleting] = useState<Assessment | null>(null);
  const [duplicating, setDuplicating] = useState<Assessment | null>(null);

  // Form errors
  const [createError, setCreateError] = useState<string | null>(null);
  const [editError, setEditError] = useState<string | null>(null);
  const [duplicateError, setDuplicateError] = useState<string | null>(null);

  // Queries
  const academicYears = useQuery({
    queryKey: ["academic-years"],
    queryFn: masterApi.years,
  });

  const assessments = useQuery({
    queryKey: ["assessments", academicYearFilter, classFilter],
    queryFn: () => assessmentApi.list({
      academic_year_id: academicYearFilter ? Number(academicYearFilter) : undefined,
      class_number: classFilter ? Number(classFilter) : undefined,
    }),
  });

  // Client-side search and type filtering
  const filteredAssessments = useMemo(() => {
    if (!assessments.data) return [];
    let result = assessments.data;

    // Client-side search by name
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter((a) => a.name.toLowerCase().includes(q));
    }

    // Type filter (client-side since API doesn't support it)
    if (typeFilter) {
      result = result.filter((a) => a.assessment_type === typeFilter);
    }

    return result;
  }, [assessments.data, search, typeFilter]);

  const hasFilters = search || academicYearFilter || classFilter || typeFilter;

  // Mutations
  const createAssessment = useMutation({
    mutationFn: (v: { name: string; assessment_type: string; academic_year_id: string; class_number: string }) =>
      assessmentApi.create({
        name: v.name.trim(),
        assessment_type: v.assessment_type as "Baseline" | "Endline",
        academic_year_id: Number(v.academic_year_id),
        class_number: Number(v.class_number),
      }),
    onSuccess: (newAssessment) => {
      qc.invalidateQueries({ queryKey: ["assessments"] });
      setCreateOpen(false);
      setCreateError(null);
      toast("Assessment created successfully");
      navigate(`/assessments/${newAssessment.id}`);
    },
    onError: (err) => setCreateError(extractErrorMessage(err)),
  });

  const updateAssessment = useMutation({
    mutationFn: (v: { name: string; assessment_type: string; academic_year_id: string; class_number: string }) =>
      assessmentApi.update(editing!.id, {
        name: v.name.trim(),
        assessment_type: v.assessment_type as "Baseline" | "Endline",
        academic_year_id: Number(v.academic_year_id),
        class_number: Number(v.class_number),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessments"] });
      qc.invalidateQueries({ queryKey: ["assessment", editing!.id] });
      setEditing(null);
      setEditError(null);
      toast("Assessment updated successfully");
    },
    onError: (err) => setEditError(extractErrorMessage(err)),
  });

  const deleteAssessment = useMutation({
    mutationFn: () => assessmentApi.delete(deleting!.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessments"] });
      setDeleting(null);
      toast("Assessment deleted");
    },
    onError: (err) => {
      toast(extractErrorMessage(err));
      setDeleting(null);
    },
  });

  const duplicateAssessment = useMutation({
    mutationFn: (payload: { name: string; assessment_type: string; academic_year_id: number; class_number: number }) =>
      // The backend duplicate endpoint just copies the source assessment.
      // We use the backend duplicate to create the copy, then update it with the new values.
      assessmentApi.duplicate(duplicating!.id).then(async (newAssessment) => {
        // If user changed fields, update the duplicated assessment
        const needsUpdate =
          payload.name !== `${duplicating!.name} (Copy)` ||
          payload.assessment_type !== duplicating!.assessment_type ||
          payload.academic_year_id !== duplicating!.academic_year_id ||
          payload.class_number !== duplicating!.class_number;

        if (needsUpdate) {
          return assessmentApi.update(newAssessment.id, {
            name: payload.name,
            assessment_type: payload.assessment_type as "Baseline" | "Endline",
            academic_year_id: payload.academic_year_id,
            class_number: payload.class_number,
          });
        }
        return newAssessment;
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assessments"] });
      setDuplicating(null);
      setDuplicateError(null);
      toast("Assessment duplicated successfully");
    },
    onError: (err) => setDuplicateError(extractErrorMessage(err)),
  });

  const clearFilters = () => {
    setSearch("");
    setAcademicYearFilter("");
    setClassFilter("");
    setTypeFilter("");
  };

  const getAcademicYearName = (id: number) => {
    const year = academicYears.data?.find((y) => y.id === id);
    return year?.name || `AY ${id}`;
  };

  return (
    <>
      <PageHeader
        title="Assessments"
        action={
          <Button onClick={() => { setCreateError(null); setCreateOpen(true); }}>
            <Plus size={16} className="mr-1" /> Create Assessment
          </Button>
        }
      />

      <p className="mb-4 text-sm text-slate-500">
        Manage assessments used for student evaluation.
      </p>

      {/* Search and Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <SearchBar value={search} onChange={setSearch} />

        <select
          className="h-10 rounded-md border bg-white px-3 text-sm"
          value={academicYearFilter}
          onChange={(e) => setAcademicYearFilter(e.target.value)}
        >
          <option value="">All academic years</option>
          {academicYears.data?.map((y) => (
            <option key={y.id} value={y.id}>{y.name}</option>
          ))}
        </select>

        <select
          className="h-10 rounded-md border bg-white px-3 text-sm"
          value={classFilter}
          onChange={(e) => setClassFilter(e.target.value)}
        >
          <option value="">All classes</option>
          {CLASS_OPTIONS.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>

        <select
          className="h-10 rounded-md border bg-white px-3 text-sm"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All types</option>
          {ASSESSMENT_TYPES.map((t) => (
            <option key={t.value} value={t.value}>{t.label}</option>
          ))}
        </select>

        {hasFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 rounded-md px-3 py-2 text-sm text-slate-500 hover:bg-slate-100"
          >
            <X size={14} /> Clear filters
          </button>
        )}
      </div>

      {/* Result count */}
      {!assessments.isPending && assessments.data && (
        <p className="mb-3 text-sm text-slate-500">
          {filteredAssessments.length} assessment{filteredAssessments.length !== 1 ? "s" : ""}
          {hasFilters ? " found" : ""}
        </p>
      )}

      {/* Loading state */}
      {assessments.isPending && (
        <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
          Loading assessments...
        </div>
      )}

      {/* Error state */}
      {assessments.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Unable to load assessments.{" "}
          <button
            className="font-medium underline"
            onClick={() => qc.invalidateQueries({ queryKey: ["assessments"] })}
          >
            Try again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!assessments.isPending && !assessments.isError && filteredAssessments.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          {hasFilters ? (
            <>
              <p className="text-sm font-medium text-slate-700">No assessments match your filters</p>
              <p className="mt-1 text-sm text-slate-500">Try adjusting your search or filter criteria.</p>
              <Button variant="ghost" className="mt-3" onClick={clearFilters}>
                Clear filters
              </Button>
            </>
          ) : (
            <>
              <p className="text-sm font-medium text-slate-700">No assessments created yet</p>
              <p className="mt-1 text-sm text-slate-500">Create your first assessment to start managing answer keys.</p>
              <Button className="mt-4" onClick={() => { setCreateError(null); setCreateOpen(true); }}>
                <Plus size={16} className="mr-1" /> Create Assessment
              </Button>
            </>
          )}
        </div>
      )}

      {/* Data table */}
      {!assessments.isPending && !assessments.isError && filteredAssessments.length > 0 && (
        <DataTable<Assessment>
          rows={filteredAssessments}
          columns={[
            {
              label: "Assessment",
              render: (r) => (
                <div>
                  <p className="font-medium text-slate-900">{r.name}</p>
                  <p className="text-xs text-slate-500">
                    {r.questions?.length || 0} question{(r.questions?.length || 0) !== 1 ? "s" : ""}
                  </p>
                </div>
              ),
            },
            {
              label: "Type",
              render: (r) => (
                <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                  r.assessment_type === "Baseline"
                    ? "bg-blue-50 text-blue-700"
                    : "bg-purple-50 text-purple-700"
                }`}>
                  {r.assessment_type}
                </span>
              ),
            },
            {
              label: "Academic Year",
              render: (r) => getAcademicYearName(r.academic_year_id),
            },
            {
              label: "Class",
              render: (r) => `Class ${r.class_number}`,
            },
          ]}
          actions={(r) => (
            <ActionMenu
              assessment={r}
              onOpen={() => navigate(`/assessments/${r.id}`)}
              onEdit={() => { setEditError(null); setEditing(r); }}
              onDuplicate={() => { setDuplicateError(null); setDuplicating(r); }}
              onDelete={() => setDeleting(r)}
            />
          )}
        />
      )}

      {/* Create Dialog */}
      <AssessmentForm
        open={createOpen}
        title="Create Assessment"
        values={{ name: "", assessment_type: "", academic_year_id: "", class_number: "" }}
        academicYears={academicYears.data || []}
        loading={createAssessment.isPending}
        error={createError}
        onClose={() => { setCreateOpen(false); setCreateError(null); }}
        onSubmit={(v) => { setCreateError(null); createAssessment.mutate(v); }}
      />

      {/* Edit Dialog */}
      <AssessmentForm
        open={!!editing}
        title="Edit Assessment"
        values={editing ? {
          name: editing.name,
          assessment_type: editing.assessment_type,
          academic_year_id: String(editing.academic_year_id),
          class_number: String(editing.class_number),
        } : { name: "", assessment_type: "", academic_year_id: "", class_number: "" }}
        academicYears={academicYears.data || []}
        loading={updateAssessment.isPending}
        error={editError}
        onClose={() => { setEditing(null); setEditError(null); }}
        onSubmit={(v) => { setEditError(null); updateAssessment.mutate(v); }}
      />

      {/* Delete Dialog */}
      <DeleteConfirmationDialog
        open={!!deleting}
        title="Delete Assessment?"
        message={deleting ? `Are you sure you want to delete "${deleting.name}"? This assessment will no longer appear in the assessment list.` : "This action cannot be undone."}
        confirmLabel="Delete Assessment"
        loading={deleteAssessment.isPending}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleteAssessment.mutate()}
      />

      {/* Duplicate Dialog */}
      <DuplicateAssessmentDialog
        open={!!duplicating}
        assessment={duplicating}
        academicYears={academicYears.data || []}
        loading={duplicateAssessment.isPending}
        error={duplicateError}
        onClose={() => { setDuplicating(null); setDuplicateError(null); }}
        onDuplicate={(payload) => { setDuplicateError(null); duplicateAssessment.mutate(payload); }}
      />
    </>
  );
}
