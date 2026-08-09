import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { queryClient } from "./lib/query-client";
import { router } from "./app/router";
import "./styles/globals.css";
import { ToastProvider } from "./components/common/toast";

createRoot(document.getElementById("root")!).render(<StrictMode><QueryClientProvider client={queryClient}><ToastProvider><RouterProvider router={router} /></ToastProvider></QueryClientProvider></StrictMode>);
