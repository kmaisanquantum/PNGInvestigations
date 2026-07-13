"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Shell from "@/components/Shell";
import StatusBadge from "@/components/StatusBadge";
import { api, CaseItem } from "@/lib/api";

export default function CasesPage() {
  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [caseNumber, setCaseNumber] = useState("");
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function load() {
    setLoading(true);
    api
      .listCases()
      .then(setCases)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createCase({ case_number: caseNumber, title, category: category || undefined, description: description || undefined });
      setCaseNumber("");
      setTitle("");
      setCategory("");
      setDescription("");
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create case");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Shell>
      <div className="px-8 py-8 max-w-5xl">
        <div className="flex items-start justify-between mb-8">
          <div>
            <p className="stamp text-xs text-brass mb-1">Active Docket</p>
            <h1 className="font-display text-2xl font-semibold text-ink">Cases</h1>
          </div>
          <button
            onClick={() => setShowForm((v) => !v)}
            className="focus-ring bg-ink text-paper text-sm px-4 py-2 hover:bg-slate-850 transition-colors"
          >
            {showForm ? "Cancel" : "New case"}
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="card p-6 mb-8 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-ink mb-1.5">Case number</label>
                <input
                  required
                  value={caseNumber}
                  onChange={(e) => setCaseNumber(e.target.value)}
                  placeholder="C-2026-014"
                  className="focus-ring w-full border border-line px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1.5">Category</label>
                <input
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  placeholder="procurement_fraud"
                  className="focus-ring w-full border border-line px-3 py-2 text-sm"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">Title</label>
              <input
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="focus-ring w-full border border-line px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="focus-ring w-full border border-line px-3 py-2 text-sm"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="focus-ring bg-brass text-white text-sm px-4 py-2 hover:opacity-90 transition-opacity disabled:opacity-60"
            >
              {submitting ? "Creating…" : "Create case"}
            </button>
          </form>
        )}

        {error && <p className="text-sm text-alert mb-4">{error}</p>}

        {loading ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : cases.length === 0 ? (
          <div className="card p-10 text-center">
            <p className="text-sm text-ink/60">No cases yet. Create the first one to begin an investigation.</p>
          </div>
        ) : (
          <div className="card divide-y divide-line">
            {cases.map((c) => (
              <Link
                key={c.id}
                href={`/cases/${c.id}`}
                className="flex items-center justify-between px-5 py-4 hover:bg-paper transition-colors"
              >
                <div>
                  <p className="stamp text-[11px] text-ink/40 mb-0.5">{c.case_number}</p>
                  <p className="font-medium text-ink">{c.title}</p>
                  {c.category && <p className="text-xs text-ink/50 mt-0.5">{c.category}</p>}
                </div>
                <StatusBadge status={c.status} />
              </Link>
            ))}
          </div>
        )}
      </div>
    </Shell>
  );
}
