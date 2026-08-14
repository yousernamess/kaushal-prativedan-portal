import { useQuery } from "@tanstack/react-query";
import { masterApi } from "../../lib/master-data";
import { assessmentApi } from "../../lib/assessments";
import type { School, Section } from "../../lib/master-data";
import type { Assessment } from "../../lib/assessments";

type Props = {
  assessmentId: string;
  schoolId: string;
  classNumber: string;
  section: string;
  onChangeAssessment: (v: string) => void;
  onChangeSchool: (v: string) => void;
  onChangeClass: (v: string) => void;
  onChangeSection: (v: string) => void;
};

export function FilterBar({
  assessmentId, schoolId, classNumber, section,
  onChangeAssessment, onChangeSchool, onChangeClass, onChangeSection,
}: Props) {
  const assessmentsQ = useQuery({ queryKey: ["assessments"], queryFn: () => assessmentApi.list() });
  const schoolsQ = useQuery({ queryKey: ["schools"], queryFn: masterApi.schools });
  const sectionsQ = useQuery({ queryKey: ["sections"], queryFn: masterApi.sections });

  const assessments = (assessmentsQ.data ?? []).filter((a: Assessment) => !a.is_deleted);
  const schools: School[] = schoolsQ.data ?? [];
  const allSections: Section[] = sectionsQ.data ?? [];

  // Filter sections by selected school and class
  const filteredSections = allSections.filter((s) => {
    if (schoolId && s.school_id !== Number(schoolId)) return false;
    if (classNumber && s.class_number !== Number(classNumber)) return false;
    return true;
  });

  // Unique class numbers from sections
  const classNumbers = [...new Set(allSections.map((s) => s.class_number))].sort();

  // Scope description
  const selectedSchool = schools.find((s) => s.id === Number(schoolId));
  const scopeParts: string[] = [];
  if (selectedSchool) scopeParts.push(selectedSchool.name);
  if (classNumber) scopeParts.push(`Class ${classNumber}`);
  if (section) scopeParts.push(`Section ${section}`);
  const scopeLabel = scopeParts.length > 0 ? scopeParts.join(" · ") : "All Schools";

  return (
    <div className="space-y-4">
      {/* Filter row */}
      <div className="flex flex-wrap gap-3">
        {/* Assessment — required */}
        <select
          value={assessmentId}
          onChange={(e) => onChangeAssessment(e.target.value)}
          className="h-10 rounded-md border bg-white px-3 text-sm min-w-[200px]"
        >
          <option value="">Select Assessment...</option>
          {assessments.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name} ({a.assessment_type}) — Class {a.class_number}
            </option>
          ))}
        </select>

        {/* School — optional */}
        <select
          value={schoolId}
          onChange={(e) => { onChangeSchool(e.target.value); onChangeSection(""); }}
          className="h-10 rounded-md border bg-white px-3 text-sm min-w-[160px]"
        >
          <option value="">All Schools</option>
          {schools.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>

        {/* Class — optional */}
        <select
          value={classNumber}
          onChange={(e) => { onChangeClass(e.target.value); onChangeSection(""); }}
          className="h-10 rounded-md border bg-white px-3 text-sm min-w-[130px]"
        >
          <option value="">All Classes</option>
          {classNumbers.map((c) => (
            <option key={c} value={c}>Class {c}</option>
          ))}
        </select>

        {/* Section — optional */}
        <select
          value={section}
          onChange={(e) => onChangeSection(e.target.value)}
          className="h-10 rounded-md border bg-white px-3 text-sm min-w-[140px]"
        >
          <option value="">All Sections</option>
          {filteredSections.map((s) => (
            <option key={s.id} value={s.section_name}>Section {s.section_name}</option>
          ))}
        </select>
      </div>

      {/* Scope summary */}
      {assessmentId && (
        <p className="text-sm text-slate-500">
          Scope: <span className="font-medium text-slate-700">{scopeLabel}</span>
        </p>
      )}
    </div>
  );
}
