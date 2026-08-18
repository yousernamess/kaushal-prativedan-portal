import { useState } from "react";
import { cn } from "../lib/utils";
import { SchoolsPage } from "./schools-page";
import { AcademicYearsPage } from "./academic-years-page";
import { SectionsPage } from "./sections-page";
import { StudentsPage } from "./students-page";

const tabs = [
  { key: "schools", label: "Schools" },
  { key: "academic-years", label: "Academic Years" },
  { key: "sections", label: "Sections" },
  { key: "students", label: "Students" },
] as const;

type TabKey = (typeof tabs)[number]["key"];

export function MasterDataPage() {
  const [active, setActive] = useState<TabKey>("schools");

  return (
    <div>
      <div className="mb-6 border-b border-slate-200">
        <nav className="flex gap-0 -mb-px overflow-x-auto" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActive(tab.key)}
              className={cn(
                "whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors",
                active === tab.key
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700"
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
      <div>
        {active === "schools" && <SchoolsPage />}
        {active === "academic-years" && <AcademicYearsPage />}
        {active === "sections" && <SectionsPage />}
        {active === "students" && <StudentsPage />}
      </div>
    </div>
  );
}
