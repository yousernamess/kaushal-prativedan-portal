import { CrudPage } from "../components/common/crud-page";

export function AcademicYearsPage() {
  return (
    <CrudPage
      title="Academic Years"
      path="/academic-years"
      defaults={{ name: "" }}
      columns={["Name"]}
      fieldConfig={{
        name: {
          label: "Academic Year",
          required: true,
          placeholder: "e.g. 2026-27",
          helperText: "Format: YYYY-YY (e.g. 2026-27)",
        },
        id: { hidden: true },
      }}
      emptyMessage="No academic years added yet."
      emptyHint="Add academic years to organize your assessments."
      deleteMessage={(r) => `Are you sure you want to delete academic year "${r.name}"?`}
    />
  );
}
