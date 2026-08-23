import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { GraduationCap, Loader2 } from "lucide-react";
import { api } from "../lib/api";

export function AcceptInvitationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [valid, setValid] = useState(false);

  useEffect(() => {
    if (!token) {
      setChecking(false);
      return;
    }
    api
      .get(`/users/invitation-info/${token}`)
      .then((r) => {
        setEmail(r.data.email);
        setValid(true);
      })
      .catch(() => setError("Invalid or expired invitation link."))
      .finally(() => setChecking(false));
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/users/accept-invitation", { token, password, full_name: fullName });
      navigate("/login");
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setError(msg || "Failed to accept invitation.");
    } finally {
      setLoading(false);
    }
  };

  if (checking) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-slate-50">
        <Loader2 size={24} className="animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
            <GraduationCap size={24} className="text-white" />
          </div>
          <div>
            <p className="text-base font-semibold text-slate-900">Kaushal Prativedan</p>
            <p className="text-xs text-slate-500">Science Assessment Portal</p>
          </div>
        </div>

        <div className="rounded-xl border bg-white p-6 shadow-sm">
          <h1 className="mb-2 text-center text-lg font-bold text-slate-900">Create your account</h1>
          {email && <p className="mb-6 text-center text-sm text-slate-500">Invited as {email}</p>}

          {error && (
            <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {!valid && !error ? (
            <p className="text-center text-sm text-slate-500">No invitation token provided.</p>
          ) : valid ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="fullName" className="mb-1 block text-sm font-medium text-slate-700">Full Name</label>
                <input
                  id="fullName"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="h-10 w-full rounded-md border bg-white px-3 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  autoFocus
                />
              </div>
              <div>
                <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">Password</label>
                <input
                  id="password"
                  type="password"
                  required
                  minLength={6}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-10 w-full rounded-md border bg-white px-3 text-sm outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  placeholder="At least 6 characters"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-blue-600 px-4 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
              >
                {loading && <Loader2 size={16} className="animate-spin" />}
                {loading ? "Creating account..." : "Create account"}
              </button>
            </form>
          ) : null}
        </div>
      </div>
    </div>
  );
}
