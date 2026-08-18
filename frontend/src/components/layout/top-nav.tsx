import { Menu } from "lucide-react";
import { Button } from "../ui/button";

export function TopNav({ onMenuClick }: { onMenuClick: () => void }) {
  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          aria-label="Open navigation"
          onClick={onMenuClick}
        >
          <Menu size={20} />
        </Button>
        <div className="min-w-0">
          <h1 className="truncate text-sm font-semibold text-slate-900">Kaushal Prativedan Portal</h1>
          <p className="truncate text-xs text-slate-500">Science Assessment Management</p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
          T
        </div>
      </div>
    </header>
  );
}
