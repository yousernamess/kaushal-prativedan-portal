import { useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileUp, FileDown } from "lucide-react";
import { Button } from "../components/ui/button";
import { DataTable } from "../components/common/data-table";
import { PageHeader } from "../components/common/page-header";
import { SearchBar } from "../components/common/search-bar";
import { useToast } from "../components/common/toast";
import { api } from "../lib/api";
import type { School, Section, Student } from "../lib/master-data";

const download = (blob: Blob, filename: string) => { const url = URL.createObjectURL(blob); const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url); };

export function StudentsPage() {
  const toast = useToast(); const client = useQueryClient(); const input = useRef<HTMLInputElement>(null);
  const [search, setSearch] = useState(""); const [schoolId, setSchoolId] = useState(""); const [classNumber, setClassNumber] = useState(""); const [section, setSection] = useState("");
  const schools = useQuery({ queryKey: ["schools"], queryFn: () => api.get<School[]>("/schools").then(r => r.data) });
  const sections = useQuery({ queryKey: ["sections", schoolId, classNumber], queryFn: () => api.get<Section[]>("/sections", { params: { school_id: schoolId || undefined, class_number: classNumber || undefined } }).then(r => r.data) });
  const students = useQuery({ queryKey: ["students", search, schoolId, classNumber, section], queryFn: () => api.get<Student[]>("/students", { params: { search: search || undefined, school_id: schoolId || undefined, class_number: classNumber || undefined, section: section || undefined } }).then(r => r.data) });
  const importCsv = async (file: File) => { const data = new FormData(); data.append("file", file); try { const response = await api.post<{ created: number; skipped: number }>("/students/import", data, { headers: { "Content-Type": "multipart/form-data" } }); toast(`Imported ${response.data.created} student(s); skipped ${response.data.skipped}.`); client.invalidateQueries({ queryKey: ["students"] }); } catch { toast("CSV import failed. Check the file format and school names."); } finally { if (input.current) input.current.value = ""; } };
  const exportCsv = async () => { try { const response = await api.get("/students/export/csv", { params: { school_id: schoolId || undefined, class_number: classNumber || undefined, section: section || undefined }, responseType: "blob" }); download(response.data, "students.csv"); toast("CSV exported."); } catch { toast("CSV export failed."); } };
  const template = () => download(new Blob(["Roll Number,Student Name,School,Class,Section\r\n"], { type: "text/csv" }), "students-template.csv");
  return <><PageHeader title="Students" action={<div className="flex flex-wrap gap-2"><input ref={input} className="hidden" type="file" accept=".csv,text/csv" onChange={e => e.target.files?.[0] && importCsv(e.target.files[0])}/><Button variant="ghost" onClick={template}><Download size={16}/> Download Template</Button><Button variant="ghost" onClick={exportCsv}><FileDown size={16}/> Export CSV</Button><Button onClick={() => input.current?.click()}><FileUp size={16}/> Import CSV</Button></div>}/><div className="mb-5 grid gap-3 md:grid-cols-4"><SearchBar value={search} onChange={setSearch}/><select className="h-10 rounded border bg-white px-3" value={schoolId} onChange={e => { setSchoolId(e.target.value); setSection(""); }}><option value="">All schools</option>{schools.data?.map(s => <option value={s.id} key={s.id}>{s.name}</option>)}</select><select className="h-10 rounded border bg-white px-3" value={classNumber} onChange={e => { setClassNumber(e.target.value); setSection(""); }}><option value="">All classes</option>{[6,7,8].map(n => <option key={n}>{n}</option>)}</select><select className="h-10 rounded border bg-white px-3" value={section} onChange={e => setSection(e.target.value)}><option value="">All sections</option>{sections.data?.map(s => <option key={s.id}>{s.section_name}</option>)}</select></div>{students.isPending ? <p>Loading students...</p> : students.isError ? <p>Unable to load students.</p> : !students.data?.length ? <p>No students found.</p> : <DataTable rows={students.data} columns={[{label:"Roll Number",render:r=>r.roll_number},{label:"Student Name",render:r=>r.student_name},{label:"School",render:r=>r.school_name},{label:"Class",render:r=>r.current_class},{label:"Section",render:r=>r.current_section}]}/>}</>;
}
