import type { ReactNode } from "react";
export function PageHeader({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h2 className="text-2xl font-bold min-w-0">{title}</h2>
      {action}
    </div>
  );
}
