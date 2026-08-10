import { BarChart3, ClipboardCheck, Database, FileBarChart, GraduationCap, LayoutDashboard, ScanLine } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";

const mainItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/assessments", label: "Assessments", icon: ClipboardCheck },
  { to: "/process-omr", label: "Process OMR", icon: ScanLine },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/reports", label: "Reports", icon: FileBarChart },
];

const masterItem = { to: "/master-data", label: "Master Data", icon: Database };

function NavItem({ to, label, icon: Icon }: { to: string; label: string; icon: typeof Database }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-white/10 hover:text-white",
          isActive && "bg-white/15 text-white"
        )
      }
    >
      <Icon size={18} />
      {label}
    </NavLink>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col bg-slate-950 p-4 text-white lg:flex">
      <div className="mb-8 flex items-center gap-3 px-2">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-blue-600">
          <GraduationCap size={21} />
        </div>
        <div>
          <p className="text-sm font-semibold">Kaushal Prativedan</p>
          <p className="text-xs text-slate-400">Science Assessment</p>
        </div>
      </div>
      <nav className="space-y-1">
        {/* Dashboard */}
        <NavItem {...mainItems[0]} />
        {/* Master Data */}
        <p className="mt-6 px-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Master Data</p>
        <NavItem {...masterItem} />
        {/* Main workflow */}
        <div className="pt-4">
          {mainItems.slice(1).map((item) => (
            <NavItem key={item.to} {...item} />
          ))}
        </div>
      </nav>
    </aside>
  );
}
