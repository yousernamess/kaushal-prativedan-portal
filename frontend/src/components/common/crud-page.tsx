import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../lib/api";
import { Button } from "../ui/button";
import { DataTable } from "./data-table";
import { FormDialog, type FieldConf } from "./form-dialog";
import { DeleteConfirmationDialog } from "./delete-confirmation-dialog";
import { PageHeader } from "./page-header";
import { useToast } from "./toast";
import type { ReactNode } from "react";

export type Row = { id: number; [key: string]: unknown };

export type CrudColumn = {
  label: string;
  render?: (row: Row) => ReactNode;
};

type Props = {
  title: string;
  path: string;
  defaults: Record<string, unknown>;
  columns: (string | CrudColumn)[];
  fieldConfig?: Record<string, FieldConf>;
  /** Custom empty state message. */
  emptyMessage?: string;
  /** Custom empty state hint. */
  emptyHint?: string;
  /** Custom delete confirmation title. */
  deleteTitle?: string;
  /** Custom delete confirmation message. Extracts from row. */
  deleteMessage?: (row: Row) => string;
  /** Completely replace the delete dialog. Receives the row, close callback, and a refresh callback. */
  customDeleteDialog?: (row: Row, onClose: () => void, refresh: () => void) => ReactNode;
};

function buildCreateRow(defaults: Record<string, unknown>, fc?: Record<string, FieldConf>): Record<string, unknown> {
  const row: Record<string, unknown> = {};
  for (const [key, val] of Object.entries(defaults)) {
    const conf = fc?.[key];
    if (conf?.hidden) continue;
    if (conf?.type === "select" && conf.options?.length && (val === "" || val === undefined)) {
      row[key] = conf.options[0].value;
    } else {
      row[key] = val;
    }
  }
  return row;
}

function editableValues(row: Record<string, unknown>, fc?: Record<string, FieldConf>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [key, val] of Object.entries(row)) {
    if (fc?.[key]?.hidden) continue;
    out[key] = val;
  }
  return out;
}

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

export function CrudPage({
  title,
  path,
  defaults,
  columns,
  fieldConfig,
  emptyMessage,
  emptyHint,
  deleteTitle,
  deleteMessage,
  customDeleteDialog,
}: Props) {
  const qc = useQueryClient();
  const toast = useToast();
  const [editing, setEditing] = useState<Row | undefined>();
  const [deleting, setDeleting] = useState<Row | undefined>();
  const [saveError, setSaveError] = useState<string | null>(null);

  const q = useQuery({
    queryKey: [path],
    queryFn: () => api.get<Row[]>(path).then((r) => r.data),
  });

  const save = useMutation({
    mutationFn: (v: Record<string, unknown>) =>
      editing?.id ? api.put(`${path}/${editing.id}`, v) : api.post(path, v),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [path] });
      setEditing(undefined);
      setSaveError(null);
      toast("Saved successfully");
    },
    onError: (err) => setSaveError(extractErrorMessage(err)),
  });

  const del = useMutation({
    mutationFn: () => api.delete(`${path}/${deleting!.id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [path] });
      setDeleting(undefined);
      toast("Deleted successfully");
    },
    onError: (err) => {
      toast(extractErrorMessage(err));
      setDeleting(undefined);
    },
  });

  const normalizedColumns: { label: string; render: (row: Row) => ReactNode }[] = columns.map((col) =>
    typeof col === "string"
      ? { label: col, render: (r: Row) => String(r[col.toLowerCase().replaceAll(" ", "_")] ?? "") }
      : { label: col.label, render: col.render ?? (() => "") }
  );

  return (
    <>
      <PageHeader
        title={title}
        action={
          <Button onClick={() => { setSaveError(null); setEditing({ id: 0, ...buildCreateRow(defaults, fieldConfig) } as Row); }}>
            Create
          </Button>
        }
      />

      {q.isPending && (
        <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600" />
          Loading {title.toLowerCase()}...
        </div>
      )}

      {q.isError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Unable to load {title.toLowerCase()}.{" "}
          <button className="font-medium underline" onClick={() => qc.invalidateQueries({ queryKey: [path] })}>
            Try again
          </button>
        </div>
      )}

      {!q.isPending && !q.isError && q.data?.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-8 text-center">
          <p className="text-sm font-medium text-slate-700">{emptyMessage ?? `No ${title.toLowerCase()} found.`}</p>
          {emptyHint && <p className="mt-1 text-sm text-slate-500">{emptyHint}</p>}
          <Button className="mt-4" onClick={() => { setSaveError(null); setEditing({ id: 0, ...buildCreateRow(defaults, fieldConfig) } as Row); }}>
            Create {title.slice(0, -1)}
          </Button>
        </div>
      )}

      {!q.isPending && !q.isError && q.data && q.data.length > 0 && (
        <DataTable<Row>
          rows={q.data}
          columns={normalizedColumns}
          actions={(r) => (
            <div className="flex gap-1">
              <button
                className="rounded px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100"
                onClick={() => { setSaveError(null); setEditing(r); }}
              >
                Edit
              </button>
              <button
                className="rounded px-3 py-1.5 text-xs text-red-600 hover:bg-red-50"
                onClick={() => setDeleting(r)}
              >
                Delete
              </button>
            </div>
          )}
        />
      )}

      <FormDialog
        open={!!editing}
        title={editing?.id ? `Edit ${title.slice(0, -1)}` : `Add ${title.slice(0, -1)}`}
        values={editing ? editableValues(editing, fieldConfig) : buildCreateRow(defaults, fieldConfig)}
        fieldConfig={fieldConfig}
        loading={save.isPending}
        error={saveError}
        onClose={() => { setEditing(undefined); setSaveError(null); }}
        onSubmit={(v) => { setSaveError(null); save.mutate(v); }}
      />

      {/* Delete — custom or default */}
      {deleting && customDeleteDialog
        ? customDeleteDialog(deleting, () => setDeleting(undefined), () => qc.invalidateQueries({ queryKey: [path] }))
        : (
          <DeleteConfirmationDialog
            open={!!deleting}
            title={deleteTitle ?? `Delete ${title.slice(0, -1)}?`}
            message={deleting ? (deleteMessage?.(deleting) ?? "This action cannot be undone.") : "This action cannot be undone."}
            confirmLabel={`Delete ${title.slice(0, -1)}`}
            loading={del.isPending}
            onClose={() => setDeleting(undefined)}
            onConfirm={() => del.mutate()}
          />
        )
      }
    </>
  );
}
