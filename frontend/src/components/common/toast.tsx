import { createContext, useContext, useState, type ReactNode } from "react";

const ToastContext = createContext<(message: string) => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [message, setMessage] = useState("");
  return (
    <ToastContext.Provider
      value={(m) => {
        setMessage(m);
        setTimeout(() => setMessage(""), 3000);
      }}
    >
      {children}
      {message && (
        <div className="fixed bottom-4 right-4 z-[100] max-w-[calc(100vw-2rem)] rounded bg-slate-900 px-4 py-3 text-sm text-white shadow-lg">
          {message}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
