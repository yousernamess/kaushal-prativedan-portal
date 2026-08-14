import { useCallback, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Play, Loader2 } from "lucide-react";
import { Button } from "../components/ui/button";
import { useToast } from "../components/common/toast";
import { processingApi } from "../lib/processing";
import type { ProcessingSession, ProcessingProgress } from "../lib/processing";
import { StepAssessmentSchool } from "../components/process-omr/step-assessment-school";
import { StepUpload } from "../components/process-omr/step-upload";
import { StepReview } from "../components/process-omr/step-review";
import { StepProcessing } from "../components/process-omr/step-processing";
import { StepResults } from "../components/process-omr/step-results";
import { useProcessOmrWorkflow } from "../lib/process-omr-workflow";

// ── Wizard Steps ───────────────────────────────────────────────────

const STEPS = [
  { key: "select", title: "Assessment & School" },
  { key: "upload", title: "Upload OMR Sheets" },
  { key: "review", title: "Review & Validate" },
  { key: "process", title: "Processing" },
  { key: "results", title: "Results" },
];

// ── Helpers ────────────────────────────────────────────────────────

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const resp = (err as { response?: { data?: { detail?: unknown } } }).response;
    const detail = resp?.data?.detail;
    if (detail) {
      if (typeof detail === "string") return detail;
      if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0];
        if (first && typeof first === "object" && "msg" in first) return String((first as { msg: string }).msg);
      }
      return "Validation error. Please check your input.";
    }
  }
  return "Something went wrong. Please try again.";
}

// ── Main Page ──────────────────────────────────────────────────────

export function ProcessOmrPage() {
  const toast = useToast();
  const qc = useQueryClient();
  const {
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
  } = useProcessOmrWorkflow();

  const restoredSession = useQuery({
    queryKey: ["processing-session", session?.id],
    queryFn: () => processingApi.get(session!.id),
    enabled: !!session?.id,
    refetchOnMount: "always",
  });

  useEffect(() => {
    if (restoredSession.data) {
      setSession(restoredSession.data);
    }
  }, [restoredSession.data, setSession]);

  // ── Mutations ──

  const createSession = useMutation({
    mutationFn: () => processingApi.create(Number(assessmentId), Number(schoolId), files),
    onSuccess: (data) => {
      setSession(data);
      toast(`Session created with ${data.total_files} file${data.total_files !== 1 ? "s" : ""}`);
      // Auto-validate so Review shows real VALID/INVALID counts
      validateSession.mutate(data.id);
    },
    onError: (err) => toast(extractErrorMessage(err)),
  });

  const validateSession = useMutation({
    mutationFn: (id: number) => processingApi.validate(id),
    onSuccess: (data) => {
      setSession(data);
      setStepIndex(2); // navigate to review after validation
      if (data.valid_files > 0) {
        toast(`Validation complete: ${data.valid_files} valid, ${data.invalid_files} invalid`);
      } else {
        toast("No valid files found. Please re-upload corrected files.");
      }
    },
    onError: (err) => toast(extractErrorMessage(err)),
  });

  const processSession = useMutation({
    mutationFn: (id: number) => processingApi.process(id),
    onSuccess: () => {
      toast("Processing started");
      setStepIndex(3); // jump to processing progress
    },
    onError: (err) => toast(extractErrorMessage(err)),
  });

  // ── Handlers ──

  const handleUpload = useCallback(async () => {
    if (!session) {
      // Create new session
      createSession.mutate();
    }
  }, [session, createSession]);

  const handleValidate = useCallback(() => {
    if (session) {
      validateSession.mutate(session.id);
    }
  }, [session, validateSession]);

  const handleProcess = useCallback(() => {
    if (session) {
      processSession.mutate(session.id);
    }
  }, [session, processSession]);

  const handleNewSession = useCallback(() => {
    resetWorkflow();
    qc.removeQueries({ queryKey: ["processing-sessions"] });
  }, [qc, resetWorkflow]);

  const handleProgress = useCallback((p: ProcessingProgress) => {
    setProgress(p);
    if (p.status !== "PROCESSING") {
      // Processing finished — fetch full session for results
      processingApi.get(p.session_id).then((data) => {
        setSession(data);
        setStepIndex(4); // jump to results
      });
    }
  }, []);

  // ── Step Navigation ──

  const canGoNext = (): boolean => {
    switch (stepIndex) {
      case 0: return assessmentId !== "" && schoolId !== "";
      case 1: return files.length > 0;
      case 2: return session !== null && session.valid_files > 0;
      default: return false;
    }
  };

  const goNext = () => {
    if (stepIndex === 0) {
      setStepIndex(1);
    } else if (stepIndex === 1) {
      if (session) {
        setStepIndex(2);
      } else {
        handleUpload();
      }
    } else if (stepIndex === 2) {
      if (session?.status === "READY") {
        handleProcess();
      } else {
        handleValidate();
      }
    }
  };

  const goBack = () => {
    if (stepIndex > 0) {
      if (stepIndex === 2) {
        // Going back from Review: clear session so re-uploading creates a fresh one
        setSession(null);
      }
      setStepIndex(stepIndex - 1);
    }
  };

  // ── Button Labels ──

  const getNextLabel = (): string => {
    switch (stepIndex) {
      case 0: return "Next: Upload";
      case 1: return session ? "Next: Review" : "Upload & Create Session";
      case 2:
        if (session?.status === "READY") return "Start Processing";
        return "Validate Files";
      default: return "Next";
    }
  };

  const getBackLabel = (): string => {
    switch (stepIndex) {
      case 1: return "Back: Assessment & School";
      case 2: return session ? "Back: Upload" : "Back: Upload";
      default: return "Back";
    }
  };

  const isLoading = createSession.isPending || validateSession.isPending || processSession.isPending;

  // ── Render ──

  return (
    <div className="mx-auto max-w-4xl">
      <h2 className="mb-2 text-2xl font-bold text-slate-900">Process OMR</h2>
      <p className="mb-6 text-sm text-slate-500">
        Upload and process OMR assessment sheets for a school batch.
      </p>

      {/* Step Indicator */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {STEPS.map((step, i) => (
            <div key={step.key} className="flex items-center">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                  i < stepIndex
                    ? "bg-green-100 text-green-700"
                    : i === stepIndex
                    ? "bg-blue-600 text-white"
                    : "bg-slate-200 text-slate-500"
                }`}
              >
                {i < stepIndex ? "✓" : i + 1}
              </div>
              <span
                className={`ml-2 hidden text-sm sm:inline ${
                  i === stepIndex ? "font-medium text-slate-900" : "text-slate-500"
                }`}
              >
                {step.title}
              </span>
              {i < STEPS.length - 1 && (
                <div className="mx-2 hidden h-px w-8 bg-slate-300 sm:block" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        {stepIndex === 0 && (
          <StepAssessmentSchool
            assessmentId={assessmentId}
            schoolId={schoolId}
            onSelectAssessment={setAssessmentId}
            onSelectSchool={setSchoolId}
          />
        )}

        {stepIndex === 1 && (
          <StepUpload files={files} onFilesChange={setFiles} />
        )}

        {stepIndex === 2 && session && (
          <StepReview session={session} />
        )}

        {stepIndex === 3 && (
          <StepProcessing sessionId={session!.id} onProgress={handleProgress} />
        )}

        {stepIndex === 4 && session && (
          <StepResults session={session} onNewSession={handleNewSession} />
        )}
      </div>

      {/* Navigation Buttons */}
      {stepIndex < 4 && (
        <div className="mt-6 flex items-center justify-between">
          <div>
            {stepIndex > 0 && (
              <Button variant="ghost" onClick={goBack} disabled={isLoading}>
                <ArrowLeft className="mr-2 h-4 w-4" />
                {getBackLabel()}
              </Button>
            )}
          </div>
          <div>
            <Button
              onClick={goNext}
              disabled={!canGoNext() || isLoading}
            >
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : stepIndex === 2 && session?.status === "READY" ? (
                <Play className="mr-2 h-4 w-4" />
              ) : (
                <ArrowRight className="mr-2 h-4 w-4" />
              )}
              {getNextLabel()}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
