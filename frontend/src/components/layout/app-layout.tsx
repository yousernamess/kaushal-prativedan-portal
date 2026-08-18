import { useState, useCallback } from "react";
import { Outlet } from "react-router-dom";
import { DesktopSidebar, MobileSidebar } from "./sidebar";
import { TopNav } from "./top-nav";

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed";

function loadCollapsed(): boolean {
  try {
    return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
  } catch {
    return false;
  }
}

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(loadCollapsed);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(next));
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  return (
    <div className="flex min-h-dvh">
      {/* Mobile drawer */}
      <MobileSidebar open={mobileOpen} onClose={() => setMobileOpen(false)} />

      {/* Desktop sidebar */}
      <DesktopSidebar collapsed={collapsed} onToggle={toggleCollapsed} />

      {/* Main content */}
      <div className="min-w-0 flex-1">
        <TopNav onMenuClick={() => setMobileOpen(true)} />
        <main className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
