import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import { useToast } from "../components/common/toast";
import { PageHeader } from "../components/common/page-header";
import { Loader2, Mail, UserCheck, UserX } from "lucide-react";

type UserRecord = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
};

type InvitationRecord = {
  id: number;
  email: string;
  role: string;
  is_used: boolean;
  expires_at: string;
  created_at: string;
};

export function UsersPage() {
  const toast = useToast();
  const qc = useQueryClient();
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("user");
  const [showInvite, setShowInvite] = useState(false);

  const usersQ = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<UserRecord[]>("/users").then((r) => r.data),
  });

  const invitationsQ = useQuery({
    queryKey: ["invitations"],
    queryFn: () => api.get<InvitationRecord[]>("/users/invitations").then((r) => r.data),
  });

  const toggleActive = useMutation({
    mutationFn: (u: UserRecord) => api.put(`/users/${u.id}`, { is_active: !u.is_active }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      toast("User updated");
    },
    onError: (err: unknown) => {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail : undefined;
      toast(msg || "Failed to update user");
    },
  });

  const inviteMutation = useMutation({
    mutationFn: () => api.post("/users/invite", { email: inviteEmail, role: inviteRole }),
    onSuccess: (res) => {
      qc.invalidateQueries({ queryKey: ["invitations"] });
      const token = res.data.token;
      const link = `${window.location.origin}/accept-invitation?token=${token}`;
      navigator.clipboard.writeText(link).then(() => {
        toast("Invitation link copied to clipboard");
      }).catch(() => {
        toast(`Invitation link: ${link}`);
      });
      setInviteEmail("");
      setInviteRole("user");
      setShowInvite(false);
    },
    onError: (err: unknown) => {
      const msg = err && typeof err === "object" && "response" in err
        ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail : undefined;
      toast(msg || "Failed to send invitation");
    },
  });

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <PageHeader
        title="Users"
        action={
          <button
            onClick={() => setShowInvite(!showInvite)}
            className="flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            <Mail size={16} />
            Invite User
          </button>
        }
      />

      {/* Invite form */}
      {showInvite && (
        <div className="rounded-lg border bg-white p-4 shadow-sm">
          <h3 className="mb-3 text-sm font-semibold text-slate-700">Invite a new user</h3>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex-1">
              <label className="mb-1 block text-xs font-medium text-slate-500">Email</label>
              <input
                type="email"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="h-10 w-full rounded-md border bg-white px-3 text-sm"
                placeholder="user@example.com"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-500">Role</label>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="h-10 rounded-md border bg-white px-3 text-sm"
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <button
              onClick={() => inviteMutation.mutate()}
              disabled={!inviteEmail || inviteMutation.isPending}
              className="flex h-10 items-center gap-2 rounded-md bg-blue-600 px-4 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {inviteMutation.isPending && <Loader2 size={14} className="animate-spin" />}
              Send Invitation
            </button>
          </div>
        </div>
      )}

      {/* Users table */}
      <div className="rounded-lg border bg-white shadow-sm">
        <div className="border-b px-4 py-3">
          <h3 className="text-sm font-semibold text-slate-700">Active Users</h3>
        </div>
        {usersQ.isLoading ? (
          <div className="flex justify-center p-8"><Loader2 size={20} className="animate-spin text-slate-400" /></div>
        ) : usersQ.data && usersQ.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {usersQ.data.map((u) => (
                  <tr key={u.id} className="border-t">
                    <td className="px-4 py-3 font-medium text-slate-900">{u.full_name}</td>
                    <td className="px-4 py-3 text-slate-600">{u.email}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                        u.role === "admin" ? "bg-blue-100 text-blue-700" : "bg-slate-100 text-slate-700"
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 text-xs font-medium ${
                        u.is_active ? "text-green-700" : "text-red-600"
                      }`}>
                        {u.is_active ? <UserCheck size={12} /> : <UserX size={12} />}
                        {u.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleActive.mutate(u)}
                        className={`rounded px-3 py-1.5 text-xs font-medium ${
                          u.is_active
                            ? "text-red-600 hover:bg-red-50"
                            : "text-green-600 hover:bg-green-50"
                        }`}
                      >
                        {u.is_active ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="p-8 text-center text-sm text-slate-500">No users found.</p>
        )}
      </div>

      {/* Invitations */}
      {invitationsQ.data && invitationsQ.data.length > 0 && (
        <div className="rounded-lg border bg-white shadow-sm">
          <div className="border-b px-4 py-3">
            <h3 className="text-sm font-semibold text-slate-700">Invitations</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Sent</th>
                  <th className="px-4 py-3 font-medium">Expires</th>
                </tr>
              </thead>
              <tbody>
                {invitationsQ.data.map((inv) => (
                  <tr key={inv.id} className="border-t">
                    <td className="px-4 py-3 text-slate-700">{inv.email}</td>
                    <td className="px-4 py-3 text-slate-700">{inv.role}</td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-medium ${inv.is_used ? "text-green-700" : "text-amber-600"}`}>
                        {inv.is_used ? "Accepted" : "Pending"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {new Date(inv.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {new Date(inv.expires_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
