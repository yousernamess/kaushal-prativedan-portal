import { useRef, useState, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileUp, FileDown, Plus, Upload, X } from "lucide-react";
import { Button } from "../components/ui/button";
import { DataTable } from "../components/common/data-table";
import { PageHeader } from "../components/common/page-header";
import { SearchBar } from "../components/common/search-bar";
import { DeleteConfirmationDialog } from "../components/common/delete-confirmation-dialog";
import { useToast } from "../components/common/toast";
import { api } from "../lib/api";
import type { School, Section, Student } from "../lib/master-data";

/* ── helpers ─────────────────────────────────────────────────────── */

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
  return "Something went wrong.";
}

const download = (blob: Blob, filename: string) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
};

const classOptions = [
  { value: "", label: "All classes" },
  { value: "6", label: "Class 6" },
  { value: "7", label: "Class 7" },
  { value: "8", label: "Class 8" },
];

const classFormOptions = [
  { value: 6, label: "Class 6" },
  { value: 7, label: "Class 7" },
  { value: 8, label: "Class 8" },
];

type ImportResult = { created: number; skipped: number; errors: { row: number; errors: string[] }[] } | null;

/* ── StudentForm ─────────────────────────────────────────────────── */

function StudentForm({
  open, title, values, schools, sectionsData, loading, error,
  onClose, onSubmit,
}: {
  open: boolean;
  title: string;
  values: { roll_number: string; student_name: string; school_id: string; current_class: string; current_section: string };
  schools: School[];
  sectionsData: Section[];
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onSubmit: (v: typeof values) => void;
}) {
  const [form, setForm] = useState(values);
  useEffect(() => { if (open) setForm(values); }, [values, open]);

  if (!open) return null;

  const set = (k: string, v: string) => setForm((prev) => {
    const next = { ...prev, [k]: v };
    // Cascade: if school or class changes, reset section
    if (k === "school_id" || k === "current_class") next.current_section = "";
    return next;
  });

  const filteredSections = sectionsData.filter(
    (s) => String(s.school_id) === form.school_id && String(s.class_number) === form.current_class
  );

  const isValid = form.roll_number && form.student_name && form.school_id && form.current_class && form.current_section;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
      <form
        onSubmit={(e) => { e.preventDefault(); if (isValid) onSubmit(form); }}
        className="w-full max-w-md space-y-4 rounded-lg bg-white p-6 shadow-xl"
      >
        <h3 className="text-lg font-semibold">{title}</h3>

        {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

        {/* Roll Number */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">Roll Number <span className="text-red-500">*</span></span>
          <input
            className="mt-1 h-10 w-full rounded border border-slate-300 px-3 text-sm"
            type="number"
            value={form.roll_number}
            onChange={(e) => set("roll_number", e.target.value)}
            placeholder="e.g. 14"
          />
        </label>

        {/* Student Name */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">Student Name <span className="text-red-500">*</span></span>
          <input
            className="mt-1 h-10 w-full rounded border border-slate-300 px-3 text-sm"
            value={form.student_name}
            onChange={(e) => set("student_name", e.target.value)}
            placeholder="e.g. Rahul Patel"
          />
        </label>

        {/* School */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">School <span className="text-red-500">*</span></span>
          <select className="mt-1 h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm" value={form.school_id} onChange={(e) => set("school_id", e.target.value)}>
            <option value="" disabled>Select a school</option>
            {schools.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </label>

        {/* Class */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">Class <span className="text-red-500">*</span></span>
          <select className="mt-1 h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm" value={form.current_class} onChange={(e) => set("current_class", e.target.value)}>
            <option value="" disabled>Select a class</option>
            {classFormOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </label>

        {/* Section — cascading */}
        <label className="block text-sm">
          <span className="font-medium text-slate-700">Section <span className="text-red-500">*</span></span>
          {!form.school_id ? (
            <select className="mt-1 h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm" disabled>
              <option>Select a school first</option>
            </select>
          ) : !form.current_class ? (
            <select className="mt-1 h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm" disabled>
              <option>Select a class first</option>
            </select>
          ) : (
            <select className="mt-1 h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm" value={form.current_section} onChange={(e) => set("current_section", e.target.value)}>
              <option value="" disabled>Select a section</option>
              {filteredSections.map((s) => <option key={s.id} value={s.section_name}>{s.section_name}</option>)}
            </select>
          )}
          {form.school_id && form.current_class && filteredSections.length === 0 && (
            <span className="mt-0.5 block text-xs text-amber-600">No sections exist for this school/class. Create sections first.</span>
          )}
        </label>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button type="submit" disabled={loading || !isValid}>
            {loading ? "Saving..." : "Save Student"}
          </Button>
        </div>
      </form>
    </div>
  );
}

/* ── ImportDialog ────────────────────────────────────────────────── */

function ImportDialog({
  open, onClose, onImported,
}: {
  open: boolean;
  onClose: () => void;
  onImported: () => void;
}) {
  const toast = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!open) return null;

  const handleFile = (f: File) => {
    setFile(f);
    setResult(null);
    setError(null);
  };

  const doImport = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = new FormData();
      data.append("file", file);
      const resp = await api.post<ImportResult>("/students/import", data, { headers: { "Content-Type": "multipart/form-data" } });
      setResult(resp.data);
      onImported();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const downloadErrors = () => {
    if (!result?.errors?.length) return;
    const lines = ["Row,Problem"];
    result.errors.forEach((e) => e.errors.forEach((msg) => lines.push(`${e.row},"${msg}"`)));
    download(new Blob([lines.join("\r\n")], { type: "text/csv" }), "import-errors.csv");
  };

  const close = () => { setFile(null); setResult(null); setError(null); onClose(); };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
      <div className="w-full max-w-lg space-y-4 rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Import Students</h3>
          <button onClick={close} className="rounded p-1 text-slate-400 hover:text-slate-600"><X size={18} /></button>
        </div>

        {!result && (
          <>
            <p className="text-sm text-slate-600">Upload a CSV containing your student roster.</p>
            <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-500">
              <p className="font-medium text-slate-600">Expected columns:</p>
              <p>Roll Number, Student Name, School, Class, Section</p>
              <p className="mt-1 text-slate-400">Tip: Use the "Template" button above to download a ready-to-fill CSV.</p>
            </div>
          </>
        )}

        {/* File picker or result */}
        {!result ? (
          <>
            <div
              className="cursor-pointer rounded-lg border-2 border-dashed border-slate-300 p-6 text-center hover:border-blue-400 hover:bg-blue-50/50"
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); }}
            >
              <Upload className="mx-auto mb-2 text-slate-400" size={24} />
              <p className="text-sm text-slate-600">Drag and drop your CSV here</p>
              <p className="text-xs text-slate-400">or click to choose a file</p>
            </div>
            <input ref={inputRef} type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])} />

            {file && (
              <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-sm text-green-700">
                <span>✓</span> {file.name} selected
              </div>
            )}

            {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={close} disabled={loading}>Cancel</Button>
              <Button onClick={doImport} disabled={loading || !file}>
                <Upload size={16} className="mr-1" />
                {loading ? "Importing..." : "Import"}
              </Button>
            </div>
          </>
        ) : (
          <>
            {/* Result */}
            <div className="space-y-2">
              {result.created > 0 && (
                <div className="flex items-center gap-2 rounded-md bg-green-50 p-3 text-sm text-green-700">
                  <span>✓</span> {result.created} student{result.created !== 1 ? "s" : ""} added
                </div>
              )}
              {result.errors.length > 0 && (
                <div className="rounded-md bg-amber-50 p-3 text-sm text-amber-700">
                  <p className="font-medium">⚠ {result.errors.length} row{result.errors.length !== 1 ? "s" : ""} need attention</p>
                </div>
              )}
            </div>

            {result.errors.length > 0 && (
              <div className="max-h-48 overflow-y-auto rounded-lg border border-slate-200">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      <th className="px-3 py-2 font-medium">Row</th>
                      <th className="px-3 py-2 font-medium">Problem</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.errors.map((e) =>
                      e.errors.map((msg, i) => (
                        <tr key={`${e.row}-${i}`} className="border-t">
                          <td className="px-3 py-2 text-slate-500">{e.row}</td>
                          <td className="px-3 py-2 text-slate-700">{msg}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2">
              {result.errors.length > 0 && (
                <Button variant="ghost" onClick={downloadErrors}>
                  <Download size={16} className="mr-1" /> Download Error Report
                </Button>
              )}
              <Button onClick={close}>Done</Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ── StudentsPage ────────────────────────────────────────────────── */

export function StudentsPage() {
  const toast = useToast();
  const qc = useQueryClient();

  // Filters
  const [search, setSearch] = useState("");
  const [schoolId, setSchoolId] = useState("");
  const [classNumber, setClassNumber] = useState("");
  const [section, setSection] = useState("");

  // Dialogs
  const [addOpen, setAddOpen] = useState(false);
  const [editing, setEditing] = useState<Student | undefined>();
  const [deleting, setDeleting] = useState<Student | undefined>();
  const [importOpen, setImportOpen] = useState(false);

  // Form state for add
  const [addForm, setAddForm] = useState({ roll_number: "", student_name: "", school_id: "", current_class: "", current_section: "" });

  // Queries
  const schools = useQuery({ queryKey: ["schools"], queryFn: () => api.get<School[]>("/schools").then((r) => r.data) });
  const sections = useQuery({
    queryKey: ["sections"],
    queryFn: () => api.get<Section[]>("/sections").then((r) => r.data),
  });
  const students = useQuery({
    queryKey: ["students", search, schoolId, classNumber, section],
    queryFn: () => api.get<Student[]>("/students", {
      params: { search: search || undefined, school_id: schoolId || undefined, class_number: classNumber || undefined, section: section || undefined },
    }).then((r) => r.data),
  });

  const hasFilters = search || schoolId || classNumber || section;

  // Mutations
  const createStudent = useMutation({
    mutationFn: (v: Record<string, unknown>) => api.post("/students", {
      school_id: Number(v.school_id),
      roll_number: Number(v.roll_number),
      student_name: v.student_name,
      current_class: Number(v.current_class),
      current_section: v.current_section,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
      setAddOpen(false);
      toast("Student added");
    },
    onError: (err) => toast(extractErrorMessage(err)),
  });

  const updateStudent = useMutation({
    mutationFn: (v: Record<string, unknown>) => api.put(`/students/${editing!.id}`, {
      school_id: Number(v.school_id),
      roll_number: Number(v.roll_number),
      student_name: v.student_name,
      current_class: Number(v.current_class),
      current_section: v.current_section,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
      setEditing(undefined);
      toast("Student updated");
    },
    onError: (err) => toast(extractErrorMessage(err)),
  });

  const deleteStudent = useMutation({
    mutationFn: () => api.delete(`/students/${deleting!.id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["students"] });
      setDeleting(undefined);
      toast("Student deleted");
    },
    onError: (err) => {
      toast(extractErrorMessage(err));
      setDeleting(undefined);
    },
  });

  // CSV export
  const exportCsv = async () => {
    try {
      const resp = await api.get("/students/export/csv", {
        params: { school_id: schoolId || undefined, class_number: classNumber || undefined, section: section || undefined },
        responseType: "blob",
      });
      download(resp.data, "students.csv");
      toast("CSV exported");
    } catch { toast("CSV export failed"); }
  };

  // Template download
  const downloadTemplate = () => {
    download(new Blob(["Roll Number,Student Name,School,Class,Section\r\n"], { type: "text/csv" }), "students-template.csv");
  };

  // Open add dialog
  const openAdd = () => {
    setAddForm({ roll_number: "", student_name: "", school_id: String(schools.data?.[0]?.id ?? ""), current_class: "6", current_section: "" });
    setAddOpen(true);
  };

  // Open edit dialog
  const openEdit = (s: Student) => {
    setEditing(s);
  };

  const openEditForm = editing ? {
    roll_number: String(editing.roll_number),
    student_name: editing.student_name,
    school_id: String(editing.school_id),
    current_class: String(editing.current_class),
    current_section: editing.current_section,
  } : null;

  return (
    <>
      <PageHeader
        title="Students"
        action={
          <div className="flex flex-wrap gap-2">
            <Button onClick={openAdd}>
              <Plus size={16} className="mr-1" /> Add Student
            </Button>
            <Button variant="ghost" onClick={() => setImportOpen(true)}>
              <FileUp size={16} className="mr-1" /> Import CSV
            </Button>
            <Button variant="ghost" onClick={exportCsv}>
              <FileDown size={16} className="mr-1" /> Export CSV
            </Button>
            <Button variant="ghost" onClick={downloadTemplate}>
              <Download size={16} className="mr-1" /> Template
            </Button>
          </div>
        }
      />

      <p className="mb-4 text-sm text-slate-500">Manage student rosters across schools, classes, and sections.</p>

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <SearchBar value={search} onChange={setSearch} />
        <select className="h-9 rounded border border-slate-300 bg-white px-3 text-sm" value={schoolId} onChange={(e) => { setSchoolId(e.target.value); setSection(""); }}>
          <option value="">All schools</option>
          {schools.data?.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select className="h-9 rounded border border-slate-300 bg-white px-3 text-sm" value={classNumber} onChange={(e) => { setClassNumber(e.target.value); setSection(""); }}>
          {classOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <select className="h-9 rounded border border-slate-300 bg-white px-3 text-sm" value={section} onChange={(e) => setSection(e.target.value)}>
          <option value="">All sections</option>
          {sections.data?.filter((s) => (!schoolId || String(s.school_id) === schoolId) && (!classNumber || String(s.class_number) === classNumber)).map((s) => (
            <option key={s.id} value={s.section_name}>{s.section_name}</option>
          ))}
        </select>
        {hasFilters && (
          <button className="text-sm text-slate-500 hover:text-slate-700" onClick={() => { setSearch(""); setSchoolId(""); setClassNumber(""); setSection(""); }}>
            Clear filters
          </button>
        )}
        {students.data && (
          <span className="text-sm text-slate-500">
            {students.data.length} student{students.data.length !== 1 ? "s" : ""}
            {hasFilters ? " matching" : ""}
          </span>
        )}
      </div>

      {/* Loading */}
      {students.isPending && (
        <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
          Loading students...
        </div>
      )}

      {/* Error */}
      {students.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Unable to load students.{" "}
          <button className="font-medium underline" onClick={() => qc.invalidateQueries({ queryKey: ["students"] })}>Try again</button>
        </div>
      )}

      {/* Empty state */}
      {!students.isPending && !students.isError && students.data?.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <p className="text-sm font-medium text-slate-700">
            {hasFilters ? "No students match your filters." : "No students added yet."}
          </p>
          {!hasFilters && (
            <p className="mt-1 text-sm text-slate-500">Add students manually or import them from a CSV file.</p>
          )}
          <div className="mt-4 flex justify-center gap-2">
            {!hasFilters && <Button onClick={openAdd}><Plus size={16} className="mr-1" /> Add Student</Button>}
            {!hasFilters && <Button variant="ghost" onClick={() => setImportOpen(true)}><Upload size={16} className="mr-1" /> Import CSV</Button>}
          </div>
        </div>
      )}

      {/* Table */}
      {!students.isPending && !students.isError && students.data && students.data.length > 0 && (
        <DataTable
          rows={students.data}
          columns={[
            { label: "Roll No.", render: (r) => String(r.roll_number) },
            { label: "Student Name", render: (r) => r.student_name },
            { label: "School", render: (r) => r.school_name },
            { label: "Class", render: (r) => `Class ${r.current_class}` },
            { label: "Section", render: (r) => r.current_section },
          ]}
          actions={(r) => (
            <div className="flex gap-1">
              <button className="rounded px-2 py-1 text-xs text-slate-600 hover:bg-slate-100" onClick={() => openEdit(r)}>Edit</button>
              <button className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50" onClick={() => setDeleting(r)}>Delete</button>
            </div>
          )}
        />
      )}

      {/* Add Dialog */}
      <StudentForm
        open={addOpen}
        title="Add Student"
        values={addForm}
        schools={schools.data ?? []}
        sectionsData={sections.data ?? []}
        loading={createStudent.isPending}
        error={null}
        onClose={() => setAddOpen(false)}
        onSubmit={(v) => createStudent.mutate(v)}
      />

      {/* Edit Dialog */}
      {editing && openEditForm && (
        <StudentForm
          open={true}
          title="Edit Student"
          values={openEditForm}
          schools={schools.data ?? []}
          sectionsData={sections.data ?? []}
          loading={updateStudent.isPending}
          error={null}
          onClose={() => setEditing(undefined)}
          onSubmit={(v) => updateStudent.mutate(v)}
        />
      )}

      {/* Delete Dialog */}
      <DeleteConfirmationDialog
        open={!!deleting}
        title="Delete student?"
        message={deleting ? `Are you sure you want to remove ${deleting.student_name} from the student roster? This action cannot be undone.` : ""}
        confirmLabel="Delete student"
        loading={deleteStudent.isPending}
        onClose={() => setDeleting(undefined)}
        onConfirm={() => deleteStudent.mutate()}
      />

      {/* Import Dialog */}
      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        onImported={() => qc.invalidateQueries({ queryKey: ["students"] })}
      />
    </>
  );
}
