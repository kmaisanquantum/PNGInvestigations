"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.login(email, password);
      router.push("/cases");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-paper px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <p className="stamp text-xs text-brass mb-2">Case Management System</p>
          <h1 className="font-display text-3xl font-semibold text-ink">Investigation Platform</h1>
        </div>

        <form onSubmit={handleSubmit} className="card p-8 space-y-5">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-ink mb-1.5">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="focus-ring w-full border border-line px-3 py-2 text-sm bg-white"
              placeholder="you@agency.gov"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-ink mb-1.5">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="focus-ring w-full border border-line px-3 py-2 text-sm bg-white"
            />
          </div>

          {error && (
            <p className="text-sm text-alert border border-alert/30 bg-alert/5 px-3 py-2">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="focus-ring w-full bg-ink text-paper py-2.5 text-sm font-medium hover:bg-slate-850 transition-colors disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-xs text-center text-ink/50 mt-6">
          First time setup? Bootstrap the admin account via{" "}
          <code className="stamp">POST /api/auth/bootstrap-admin</code>
        </p>
      </div>
    </main>
  );
}
