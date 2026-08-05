import { Outlet } from "react-router-dom";
import { Sidebar } from "./sidebar";
import { TopNav } from "./top-nav";
export function AppLayout() { return <div className="flex min-h-screen"><Sidebar /><div className="min-w-0 flex-1"><TopNav /><main className="p-5 sm:p-8"><Outlet /></main></div></div>; }
