import {
  BarChart3,
  ClipboardCheck,
  ChevronsLeft,
  ChevronsRight,
  Database,
  FileBarChart,
  LayoutDashboard,
  ScanLine,
  Users,
  X,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";
import { useAuth } from "../../lib/auth";

// ── Navigation structure ───────────────────────────────────────────

type NavItemData = { to: string; label: string; icon: typeof Database };

function useNavGroups() {
  const { isAdmin } = useAuth();
  const groups: { heading?: string; items: NavItemData[] }[] = [];

  if (isAdmin) {
    groups.push({ items: [{ to: "/", label: "Dashboard", icon: LayoutDashboard }] });
  }

  groups.push({
    heading: "Workflow",
    items: [
      { to: "/assessments", label: "Assessments", icon: ClipboardCheck },
      { to: "/process-omr", label: "Process OMR", icon: ScanLine },
    ],
  });

  groups.push({
    heading: "Insights",
    items: [
      { to: "/analytics", label: "Analytics", icon: BarChart3 },
      { to: "/reports", label: "Reports", icon: FileBarChart },
    ],
  });

  if (isAdmin) {
    groups.push({
      heading: "Setup",
      items: [
        { to: "/master-data", label: "Master Data", icon: Database },
        { to: "/users", label: "Users", icon: Users },
      ],
    });
  } else {
    groups.push({
      heading: "Setup",
      items: [{ to: "/master-data", label: "Master Data", icon: Database }],
    });
  }

  return groups;
}

// ── Nav item component ─────────────────────────────────────────────

function NavItem({
  to,
  label,
  icon: Icon,
  collapsed,
}: NavItemData & { collapsed?: boolean }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      className={({ isActive }) =>
        cn(
          "group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
          isActive
            ? "bg-blue-600/15 text-blue-400"
            : "text-slate-300 hover:bg-white/10 hover:text-white",
          collapsed && "justify-center px-2",
        )
      }
      title={collapsed ? label : undefined}
    >
      {({ isActive }) => (
        <>
          <span
            className={cn(
              "flex h-6 w-6 shrink-0 items-center justify-center rounded transition-colors",
              isActive ? "bg-blue-600 text-white" : "text-slate-400 group-hover:text-white",
            )}
          >
            <Icon size={16} />
          </span>
          {!collapsed && <span>{label}</span>}
        </>
      )}
    </NavLink>
  );
}

// ── Sidebar content (shared between desktop & mobile) ──────────────

function SidebarContent({
  collapsed,
  onCloseMobile,
}: {
  collapsed?: boolean;
  onCloseMobile?: () => void;
}) {
  const navGroups = useNavGroups();

  return (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className={cn("mb-6 flex items-center gap-3", collapsed ? "justify-center px-1" : "px-2")}>
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-blue-600">
          <LayoutDashboard size={20} className="text-white" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-white">Kaushal Prativedan</p>
            <p className="truncate text-xs text-slate-400">Science Assessment</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto">
        {navGroups.map((group, gi) => (
          <div key={gi} className={gi > 0 ? "mt-6" : ""}>
            {group.heading && !collapsed && (
              <p className="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                {group.heading}
              </p>
            )}
            {group.items.map((item) => (
              <NavItem key={item.to} {...item} collapsed={collapsed} />
            ))}
          </div>
        ))}
      </nav>

      {/* Mobile close button at bottom */}
      {onCloseMobile && (
        <div className="mt-auto border-t border-white/10 pt-3">
          <button
            onClick={onCloseMobile}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-slate-300 transition-colors hover:bg-white/10 hover:text-white"
          >
            <X size={18} />
            <span>Close menu</span>
          </button>
        </div>
      )}
    </div>
  );
}

// ── Desktop Sidebar ────────────────────────────────────────────────

export function DesktopSidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  return (
    <aside
      className={cn(
        "hidden flex-col bg-slate-950 p-4 text-white transition-[width] duration-200 lg:flex",
        collapsed ? "w-[68px]" : "w-64",
      )}
    >
      <SidebarContent collapsed={collapsed} />

      {/* Collapse toggle */}
      <button
        onClick={onToggle}
        className="mt-4 flex items-center justify-center rounded-md border border-white/10 p-2 text-slate-400 transition-colors hover:bg-white/10 hover:text-white"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? <ChevronsRight size={16} /> : <ChevronsLeft size={16} />}
      </button>
    </aside>
  );
}

// ── Mobile Sidebar (overlay drawer) ────────────────────────────────

export function MobileSidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 transition-opacity lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-slate-950 p-4 text-white shadow-xl transition-transform duration-200 lg:hidden",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <SidebarContent onCloseMobile={onClose} />
      </aside>
    </>
  );
}
