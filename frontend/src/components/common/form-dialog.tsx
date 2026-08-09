import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Button } from "../ui/button";

export type FieldOption = { value: string | number; label: string };
export type FieldConf = {
  hidden?: boolean;
  type?: "text" | "select";
  label?: string;
  options?: FieldOption[];
  required?: boolean;
  placeholder?: string;
  helperText?: string;
};

type Props = {
  open: boolean;
  title: string;
  values: Record<string, unknown>;
  fieldConfig?: Record<string, FieldConf>;
  loading?: boolean;
  error?: string | null;
  onClose: () => void;
  onSubmit: (values: Record<string, unknown>) => void;
};

export function FormDialog({ open, title, values, fieldConfig, loading, error, onClose, onSubmit }: Props) {
  const { register, handleSubmit, reset, formState: { errors } } = useForm({ defaultValues: values });
  useEffect(() => { if (open) reset(values); }, [values, open, reset]);
  if (!open) return null;

  const entries = Object.entries(values).filter(([key]) => !fieldConfig?.[key]?.hidden);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/40 p-4">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-md space-y-4 rounded-lg bg-white p-6 shadow-xl"
      >
        <h3 className="text-lg font-semibold">{title}</h3>

        {error && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        {entries.map(([key, value]) => {
          const conf = fieldConfig?.[key];
          const label = conf?.label ?? key.replaceAll("_", " ");
          const required = conf?.required !== false;
          const fieldError = errors[key]?.message as string | undefined;

          if (conf?.type === "select" && conf.options) {
            return (
              <label className="block text-sm" key={key}>
                <span className="font-medium text-slate-700">
                  {label}
                  {required && <span className="ml-0.5 text-red-500">*</span>}
                </span>
                <select
                  className={`mt-1 h-10 w-full rounded border bg-white px-3 text-sm ${fieldError ? "border-red-400" : "border-slate-300"}`}
                  {...register(key, { required: required ? `${label} is required` : false })}
                  defaultValue={String(value ?? "")}
                >
                  {conf.options.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                {conf.helperText && !fieldError && (
                  <span className="mt-0.5 block text-xs text-slate-400">{conf.helperText}</span>
                )}
                {fieldError && <span className="mt-0.5 block text-xs text-red-600">{fieldError}</span>}
              </label>
            );
          }

          return (
            <label className="block text-sm" key={key}>
              <span className="font-medium text-slate-700">
                {label}
                {required && <span className="ml-0.5 text-red-500">*</span>}
              </span>
              <input
                className={`mt-1 h-10 w-full rounded border px-3 text-sm ${fieldError ? "border-red-400" : "border-slate-300"}`}
                {...register(key, {
                  required: required ? `${label} is required` : false,
                  minLength: key === "name" ? { value: 1, message: `${label} cannot be empty` } : undefined,
                })}
                defaultValue={String(value ?? "")}
                placeholder={conf?.placeholder}
              />
              {conf?.helperText && !fieldError && (
                <span className="mt-0.5 block text-xs text-slate-400">{conf.helperText}</span>
              )}
              {fieldError && <span className="mt-0.5 block text-xs text-red-600">{fieldError}</span>}
            </label>
          );
        })}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>Cancel</Button>
          <Button type="submit" disabled={loading}>
            {loading ? "Saving..." : "Save"}
          </Button>
        </div>
      </form>
    </div>
  );
}
