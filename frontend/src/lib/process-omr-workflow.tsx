import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { processingApi } from "./processing";
import type { ProcessingProgress, ProcessingSession } from "./processing";

// ── Persistence ────────────────────────────────────────────────────

const STORAGE_KEY = "omr-workflow-state";

type PersistedShape = {
  stepIndex: number;
  assessmentId: string;
  schoolId: string;
  sessionId: number | null;
  sessionStatus: string | null;
};

function loadPersisted(): PersistedShape | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function savePersisted(data: PersistedShape) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch { /* quota / private browsing — ignore */ }
}

function clearPersisted() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch { /* ignore */ }
}

// ── Context ────────────────────────────────────────────────────────

type ProcessOmrWorkflowContextValue = {
  stepIndex: number;
  setStepIndex: (value: number) => void;
  assessmentId: string;
  setAssessmentId: (value: string) => void;
  schoolId: string;
  setSchoolId: (value: string) => void;
  files: File[];
  setFiles: (value: File[]) => void;
  session: ProcessingSession | null;
  setSession: (value: ProcessingSession | null) => void;
  progress: ProcessingProgress | null;
  setProgress: (value: ProcessingProgress | null) => void;
  resetWorkflow: () => void;
};

const ProcessOmrWorkflowContext = createContext<ProcessOmrWorkflowContextValue | null>(null);

export function ProcessOmrWorkflowProvider({ children }: { children: ReactNode }) {
  // Lazy initializer: only read localStorage once on mount
  const [stepIndex, setStepIndex] = useState(() => loadPersisted()?.stepIndex ?? 0);
  const [assessmentId, setAssessmentId] = useState(() => loadPersisted()?.assessmentId ?? "");
  const [schoolId, setSchoolId] = useState(() => loadPersisted()?.schoolId ?? "");
  const [files, setFiles] = useState<File[]>([]);
  const [session, setSession] = useState<ProcessingSession | null>(() => {
    const persisted = loadPersisted();
    return persisted?.sessionId ? ({ id: persisted.sessionId } as ProcessingSession) : null;
  });
  const [progress, setProgress] = useState<ProcessingProgress | null>(null);

  // Validate stale session on mount
  const validatedRef = useRef(false);
  useEffect(() => {
    if (validatedRef.current || !session?.id) return;
    validatedRef.current = true;
    processingApi.get(session.id).catch(() => {
      // Session no longer exists on backend — clear stale state
      setSession(null);
      setStepIndex(0);
      setAssessmentId("");
      setSchoolId("");
      clearPersisted();
    });
  }, [session?.id]);

  // Persist serializable state on every change
  useEffect(() => {
    savePersisted({
      stepIndex,
      assessmentId,
      schoolId,
      sessionId: session?.id ?? null,
      sessionStatus: session?.status ?? null,
    });
  }, [stepIndex, assessmentId, schoolId, session?.id, session?.status]);

  const resetWorkflow = useCallback(() => {
    setStepIndex(0);
    setAssessmentId("");
    setSchoolId("");
    setFiles([]);
    setSession(null);
    setProgress(null);
    clearPersisted();
  }, []);

  return (
    <ProcessOmrWorkflowContext.Provider
      value={{
        stepIndex,
        setStepIndex,
        assessmentId,
        setAssessmentId,
        schoolId,
        setSchoolId,
        files,
        setFiles,
        session,
        setSession,
        progress,
        setProgress,
        resetWorkflow,
      }}
    >
      {children}
    </ProcessOmrWorkflowContext.Provider>
  );
}

export function useProcessOmrWorkflow() {
  const context = useContext(ProcessOmrWorkflowContext);
  if (!context) {
    throw new Error("useProcessOmrWorkflow must be used within ProcessOmrWorkflowProvider");
  }
  return context;
}