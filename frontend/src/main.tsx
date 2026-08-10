import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { queryClient } from "./lib/query-client";
import { router } from "./app/router";
import "./styles/globals.css";
import { ToastProvider } from "./components/common/toast";
import { ProcessOmrWorkflowProvider } from "./lib/process-omr-workflow";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<QueryClientProvider client={queryClient}>
			<ToastProvider>
				<ProcessOmrWorkflowProvider>
					<RouterProvider router={router} />
				</ProcessOmrWorkflowProvider>
			</ToastProvider>
		</QueryClientProvider>
	</StrictMode>,
);
