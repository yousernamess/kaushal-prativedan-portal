import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../lib/api";
import { CrudPage } from "../components/common/crud-page";
import { Button } from "../components/ui/button";
import { useToast } from "../components/common/toast";
import type { CrudColumn, Row } from "../components/common/crud-page";

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response;
    if (resp?.data?.detail) return resp.data.detail;
  }
  return "Something went wrong.";
}

const columns: CrudColumn[] = [
  { label: "School", render: (r) => String(r.name ?? "") },
  { label: "Students", render: (r) => String(r.student_count ?? 0) },
  { label: "Sections", render: (r) => String(r.section_count ?? 0) },
  {
    label: "Created",
    render: (r) => {
      try { return new Date(String(r.created_at)).toLocaleDateString(); }
      catch { return String(r.created_at ?? ""); }
    },
  },
];

/** Custom delete dialog for schools — offers "Remove students" and "Delete everything" when the school has data. */
function SchoolDeleteDialog({
  row, onClose, refresh,
}: {
  row: Row;
  onClose: () => void;
  refresh: () => void;
}) {
  const toast = useToast();
  const name = String(row.name ?? "this school");
  const students = Number(row.student_count ?? 0);
  const sections = Number(row.section_count ?? 0);
  const hasData = students > 0 || sections > 0;

  const removeStudents = useMutation({
    mutationFn: () => api.delete(`/schools/${row.id}/students`),
    onSuccess: (resp) => {
      const deleted = (resp.data as { deleted?: number }).deleted ?? 0;
      toast(`Removed ${deleted} student${deleted !== 1 ? "s" : ""} from ${name}`);
      refresh();
      onClose();
    },
    onError: (err) => toast(extractErrorMessage(err)),
  });

  const forceDelete = useMutation({
    mutationFn: () => api.delete(`/schools/${row.id}?force=true`),
    onSuccess: () => {
      toast(`${name} deleted`);
      refresh();
      onClose();
    },
    onError: (err) => toast(extractErrorMessage(err)),
  });

  // If no data, simple delete is fine
  if (!hasData) {
    const simpleDelete = useMutation({
      mutationFn: () => api.delete(`/schools/${row.id}`),
      onSuccess: () => { toast(`${name} deleted`); refresh(); onClose(); },
      onError: (err) => toast(extractErrorMessage(err)),
    });
    return (
      <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
        <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
          <h3 className="font-semibold text-slate-900">Delete school?</h3>
          <p className="mt-2 text-sm text-slate-500">Are you sure you want to delete "{name}"? This action cannot be undone.</p>
          <div className="mt-5 flex justify-end gap-2">
            <Button variant="ghost" onClick={onClose}>Cancel</Button>
            <Button onClick={() => simpleDelete.mutate()} disabled={simpleDelete.isPending} className="bg-red-600 text-white hover:bg-red-700">
              {simpleDelete.isPending ? "Deleting..." : "Delete school"}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 className="font-semibold text-slate-900">Delete school?</h3>
        <p className="mt-2 text-sm text-slate-500">
          <strong>{name}</strong> has{" "}
          {students > 0 && <>{students} student{students !== 1 ? "s" : ""}</>}
          {students > 0 && sections > 0 && <> and </>}
          {sections > 0 && <>{sections} section{sections !== 1 ? "s" : ""}</>}.
        </p>

        <div className="mt-5 space-y-3">
          {/* Option 1: Remove students only */}
          <button
            className="w-full rounded-lg border border-amber-200 bg-amber-50 p-3 text-left text-sm transition-colors hover:bg-amber-100"
            onClick={() => removeStudents.mutate()}
            disabled={removeStudents.isPending || forceDelete.isPending}
          >
            <p className="font-medium text-amber-800">Remove all students</p>
            <p className="mt-0.5 text-xs text-amber-600">
              Delete {students} student{students !== 1 ? "s" : ""} but keep the school
            </p>
          </button>

          {/* Option 2: Force delete everything */}
          <button
            className="w-full rounded-lg border border-red-200 bg-red-50 p-3 text-left text-sm transition-colors hover:bg-red-100"
            onClick={() => forceDelete.mutate()}
            disabled={removeStudents.isPending || forceDelete.isPending}
          >
            <p className="font-medium text-red-800">Delete school and all data</p>
            <p className="mt-0.5 text-xs text-red-600">
              Remove {students} student{students !== 1 ? "s" : ""}, {sections} section{sections !== 1 ? "s" : ""}, and "{name}"
            </p>
          </button>
        </div>

        <div className="mt-5 flex justify-end">
          <Button variant="ghost" onClick={onClose} disabled={removeStudents.isPending || forceDelete.isPending}>Cancel</Button>
        </div>
      </div>
    </div>
  );
}

export function SchoolsPage() {
  return (
    <CrudPage
      title="Schools"
      path="/schools"
      defaults={{ name: "" }}
      columns={columns}
      fieldConfig={{
        name: { label: "School Name", required: true, placeholder: "e.g. Sunrise Public School" },
        id: { hidden: true },
        student_count: { hidden: true },
        section_count: { hidden: true },
        created_at: { hidden: true },
        updated_at: { hidden: true },
      }}
      emptyMessage="No schools added yet."
      emptyHint="Add your first school to start managing students and assessments."
      customDeleteDialog={(row, onClose, refresh) => (
        <SchoolDeleteDialog row={row} onClose={onClose} refresh={refresh} />
      )}
    />
  );
}
