import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { api } from "../lib/api";
import { Button } from "../components/ui/button";
import { DataTable } from "../components/common/data-table";
import { FormDialog } from "../components/common/form-dialog";
import { DeleteConfirmationDialog } from "../components/common/delete-confirmation-dialog";
import { PageHeader } from "../components/common/page-header";
import { useToast } from "../components/common/toast";
import type { School } from "../lib/master-data";

type Section = { id: number; school_id: number; class_number: number; section_name: string };

const classOptions = [
  { value: 6, label: "Class 6" },
  { value: 7, label: "Class 7" },
  { value: 8, label: "Class 8" },
];

const classFilterOptions = [
  { value: "", label: "All classes" },
  { value: "6", label: "Class 6" },
  { value: "7", label: "Class 7" },
  { value: "8", label: "Class 8" },
];

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const resp = (err as { response?: { data?: { detail?: string } } }).response;
    if (resp?.data?.detail) return resp.data.detail;
  }
  return "Something went wrong.";
}

export function SectionsPage() {
  const toast = useToast();
  const qc = useQueryClient();

  // Filters
  const [filterSchool, setFilterSchool] = useState("");
  const [filterClass, setFilterClass] = useState("");

  // Bulk create dialog
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulkSchool, setBulkSchool] = useState<number | "">("");
  const [bulkClass, setBulkClass] = useState<number>(6);
  const [bulkNames, setBulkNames] = useState("");

  // Edit dialog
  const [editing, setEditing] = useState<Section | undefined>();
  const [editSchool, setEditSchool] = useState<number | "">("");
  const [editClass, setEditClass] = useState<number>(6);
  const [editName, setEditName] = useState("");

  // Delete dialog
  const [deleting, setDeleting] = useState<Section | undefined>();

  // Queries
  const schools = useQuery({ queryKey: ["schools"], queryFn: () => api.get<School[]>("/schools").then((r) => r.data) });
  const sections = useQuery({
    queryKey: ["sections", filterSchool, filterClass],
    queryFn: () => api.get<Section[]>("/sections", {
      params: { school_id: filterSchool || undefined, class_number: filterClass || undefined },
    }).then((r) => r.data),
  });

  // Build school name lookup
  const schoolMap = new Map(schools.data?.map((s) => [s.id, s.name]) ?? []);

  // Mutations
  const bulkCreate = useMutation({
    mutationFn: () => api.post("/sections/bulk", {
      school_id: bulkSchool,
      class_number: bulkClass,
      section_names: bulkNames,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sections"] });
      setBulkOpen(false);
      setBulkNames("");
      toast("Sections created successfully");
    },
    onError: (err) => toast(extractErrorMessage(err)),
  });

  const updateSection = useMutation({
    mutationFn: () => api.put(`/sections/${editing!.id}`, {
      school_id: editSchool,
      class_number: editClass,
      section_name: editName,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sections"] });
      setEditing(undefined);
      toast("Section updated");
    },
    onError: (err) => toast(extractErrorMessage(err)),
  });

  const deleteSection = useMutation({
    mutationFn: () => api.delete(`/sections/${deleting!.id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sections"] });
      setDeleting(undefined);
      toast("Section deleted");
    },
    onError: (err) => {
      toast(extractErrorMessage(err));
      setDeleting(undefined);
    },
  });

  // Parse bulk names for preview
  const parsedBulkNames = bulkNames
    .split(",")
    .map((n) => n.trim())
    .filter((n) => n.length > 0);
  const uniqueBulkNames = [...new Set(parsedBulkNames.map((n) => n.toUpperCase()))];

  const openBulk = () => {
    setBulkSchool(schools.data?.[0]?.id ?? "");
    setBulkClass(6);
    setBulkNames("");
    setBulkOpen(true);
  };

  const openEdit = (s: Section) => {
    setEditing(s);
    setEditSchool(s.school_id);
    setEditClass(s.class_number);
    setEditName(s.section_name);
  };

  const hasFilters = filterSchool || filterClass;
  const schoolName = (id: number) => schoolMap.get(id) ?? `School #${id}`;

  return (
    <>
      <PageHeader
        title="Sections"
        action={
          <Button onClick={openBulk}>
            <Plus size={16} className="mr-1" />
            Add Sections
          </Button>
        }
      />

      {/* Filters */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select
          className="h-9 rounded border border-slate-300 bg-white px-3 text-sm"
          value={filterSchool}
          onChange={(e) => setFilterSchool(e.target.value)}
        >
          <option value="">All schools</option>
          {schools.data?.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <select
          className="h-9 rounded border border-slate-300 bg-white px-3 text-sm"
          value={filterClass}
          onChange={(e) => setFilterClass(e.target.value)}
        >
          {classFilterOptions.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        {hasFilters && (
          <button
            className="text-sm text-slate-500 hover:text-slate-700"
            onClick={() => { setFilterSchool(""); setFilterClass(""); }}
          >
            Clear filters
          </button>
        )}
        {sections.data && (
          <span className="text-sm text-slate-500">{sections.data.length} section{sections.data.length !== 1 ? "s" : ""}</span>
        )}
      </div>

      {/* Loading */}
      {sections.isPending && (
        <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
          Loading sections...
        </div>
      )}

      {/* Error */}
      {sections.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Unable to load sections.{" "}
          <button className="font-medium underline" onClick={() => qc.invalidateQueries({ queryKey: ["sections"] })}>
            Try again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!sections.isPending && !sections.isError && sections.data?.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <p className="text-sm font-medium text-slate-700">No sections added yet.</p>
          <p className="mt-1 text-sm text-slate-500">Create sections for each school and class before adding students.</p>
          <Button className="mt-4" onClick={openBulk}>
            <Plus size={16} className="mr-1" />
            Add Sections
          </Button>
        </div>
      )}

      {/* Table */}
      {!sections.isPending && !sections.isError && sections.data && sections.data.length > 0 && (
        <DataTable
          rows={sections.data}
          columns={[
            { label: "School", render: (r) => schoolName(r.school_id) },
            { label: "Class", render: (r) => `Class ${r.class_number}` },
            { label: "Section", render: (r) => r.section_name },
          ]}
          actions={(r) => (
            <div className="flex gap-1">
              <button className="rounded px-2 py-1 text-xs text-slate-600 hover:bg-slate-100" onClick={() => openEdit(r)}>Edit</button>
              <button className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50" onClick={() => setDeleting(r)}>Delete</button>
            </div>
          )}
        />
      )}

      {/* Bulk Create Dialog */}
      {bulkOpen && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
          <div className="w-full max-w-lg space-y-4 rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold">Add Sections</h3>

            {/* School */}
            <label className="block text-sm">
              <span className="font-medium text-slate-700">School <span className="text-red-500">*</span></span>
              <select
                className="mt-1 h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm"
                value={bulkSchool}
                onChange={(e) => setBulkSchool(Number(e.target.value))}
              >
                <option value="" disabled>Select a school</option>
                {schools.data?.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </label>

            {/* Class */}
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Class <span className="text-red-500">*</span></span>
              <select
                className="mt-1 h-10 w-full rounded border border-slate-300 bg-white px-3 text-sm"
                value={bulkClass}
                onChange={(e) => setBulkClass(Number(e.target.value))}
              >
                {classOptions.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>

            {/* Section names */}
            <label className="block text-sm">
              <span className="font-medium text-slate-700">Sections <span className="text-red-500">*</span></span>
              <input
                className="mt-1 h-10 w-full rounded border border-slate-300 px-3 text-sm"
                value={bulkNames}
                onChange={(e) => setBulkNames(e.target.value)}
                placeholder="e.g. A, B, C"
              />
              <span className="mt-0.5 block text-xs text-slate-400">Enter section names separated by commas</span>
            </label>

            {/* Preview */}
            {uniqueBulkNames.length > 0 && bulkSchool && (
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs font-medium text-slate-600">This will create:</p>
                <p className="text-sm font-medium text-slate-800">
                  {schoolMap.get(bulkSchool as number) ?? "School"} — {classOptions.find((c) => c.value === bulkClass)?.label}
                </p>
                <ul className="mt-1 space-y-0.5">
                  {uniqueBulkNames.map((name) => (
                    <li key={name} className="text-sm text-slate-600">• Section {name}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={() => setBulkOpen(false)} disabled={bulkCreate.isPending}>Cancel</Button>
              <Button
                onClick={() => bulkCreate.mutate()}
                disabled={bulkCreate.isPending || !bulkSchool || uniqueBulkNames.length === 0}
              >
                {bulkCreate.isPending ? "Creating..." : `Create ${uniqueBulkNames.length} Section${uniqueBulkNames.length !== 1 ? "s" : ""}`}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Dialog */}
      <FormDialog
        open={!!editing}
        title="Edit Section"
        values={{ school_id: editSchool, class_number: editClass, section_name: editName }}
        fieldConfig={{
          school_id: { type: "select", label: "School", required: true, options: schools.data?.map((s) => ({ value: s.id, label: s.name })) ?? [] },
          class_number: { type: "select", label: "Class", required: true, options: classOptions },
          section_name: { label: "Section Name", required: true },
        }}
        loading={updateSection.isPending}
        onClose={() => setEditing(undefined)}
        onSubmit={(v) => {
          setEditSchool(v.school_id as number);
          setEditClass(v.class_number as number);
          setEditName(v.section_name as string);
          updateSection.mutate();
        }}
      />

      {/* Delete Dialog */}
      <DeleteConfirmationDialog
        open={!!deleting}
        title="Delete section?"
        message={deleting ? `Are you sure you want to delete section "${deleting.section_name}" from ${schoolName(deleting.school_id)} — Class ${deleting.class_number}? This action cannot be undone.` : ""}
        confirmLabel="Delete section"
        loading={deleteSection.isPending}
        onClose={() => setDeleting(undefined)}
        onConfirm={() => deleteSection.mutate()}
      />
    </>
  );
}
