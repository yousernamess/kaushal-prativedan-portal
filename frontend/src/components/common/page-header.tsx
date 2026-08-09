import type { ReactNode } from "react";
export function PageHeader({ title, action }: { title: string; action?: ReactNode }) { return <div className="mb-6 flex items-center justify-between"><h2 className="text-2xl font-bold">{title}</h2>{action}</div>; }
