"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Shell from "@/components/Shell";
import StatusBadge from "@/components/StatusBadge";
import { api, CaseItem, CaseStatus, EvidenceItem } from "@/lib/api";

const STATUS_OPTIONS: CaseStatus[] = ["open", "evidence_collection", "under_review", "closed"];

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;

  const [caseData, setCaseData] = useState<CaseItem | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function load() {
    api.getCase(caseId).then(setCaseData).catch((e) => setError(e.message));
    api.listEvidence(caseId).then(setEvidence).catch((e) => setError(e.message));
  }

  useEffect(load, [caseId]);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadEvidence(caseId, file, notes);
      setNotes("");
      if (fileInputRef.current) fileInputRef.current.value = "";
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function handleStatusChange(status: CaseStatus) {
    try {
      const updated = await api.updateCase(caseId, { status });
      setCaseData(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update status");
    }
  }

  if (!caseData) {
    return (
      <Shell>
        <div className="px-8 py-8">{error ? <p className="text-alert text-sm">{error}</p> : <p className="text-sm text-ink/50">Loading…</p>}</div>
      </Shell>
    );
  }

  return (
    <Shell>
      <div className="px-8 py-8 max-w-4xl">
        <p className="stamp text-xs text-brass mb-1">{caseData.case_number}</p>
        <div className="flex items-start justify-between mb-2">
          <h1 className="font-display text-2xl font-semibold text-ink">{caseData.title}</h1>
          <StatusBadge status={caseData.status} />
        </div>
        {caseData.description && <p className="text-sm text-ink/70 mb-4">{caseData.description}</p>}

        <div className="flex items-center gap-2 mb-8">
          <span className="text-xs text-ink/50 mr-1">Update status:</span>
          {STATUS_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => handleStatusChange(s)}
              disabled={s === caseData.status}
              className="focus-ring text-xs border border-line px-2.5 py-1 hover:bg-paper disabled:opacity-40 disabled:cursor-default"
            >
              {s.replace("_", " ")}
            </button>
          ))}
        </div>

        {error && <p className="text-sm text-alert mb-4">{error}</p>}

        <h2 className="font-display text-lg font-semibold text-ink mb-3">Evidence</h2>

        <form onSubmit={handleUpload} className="card p-5 mb-6 space-y-3">
          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">File</label>
            <input ref={fileInputRef} type="file" required className="text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">Notes</label>
            <input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="focus-ring w-full border border-line px-3 py-2 text-sm"
              placeholder="Source, context, collection method…"
            />
          </div>
          <button
            type="submit"
            disabled={uploading}
            className="focus-ring bg-ink text-paper text-sm px-4 py-2 hover:bg-slate-850 transition-colors disabled:opacity-60"
          >
            {uploading ? "Uploading & hashing…" : "Upload evidence"}
          </button>
        </form>

        {evidence.length === 0 ? (
          <div className="card p-8 text-center">
            <p className="text-sm text-ink/60">No evidence uploaded for this case yet.</p>
          </div>
        ) : (
          <div className="card divide-y divide-line">
            {evidence.map((ev) => (
              <div key={ev.id} className="px-5 py-4">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-ink text-sm">{ev.filename}</p>
                  <a
                    href={`/api/cases/${caseId}/evidence/${ev.id}/download`}
                    className="text-xs text-brass hover:underline"
                  >
                    Download
                  </a>
                </div>
                <p className="stamp text-[10px] text-ink/40 mt-1">SHA-256 {ev.sha256_hash}</p>
                {ev.notes && <p className="text-xs text-ink/60 mt-1">{ev.notes}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </Shell>
  );
}
