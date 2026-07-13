import { CaseStatus } from "@/lib/api";

const LABELS: Record<CaseStatus, string> = {
  open: "Open",
  evidence_collection: "Evidence Collection",
  under_review: "Under Review",
  closed: "Closed",
};

const STYLES: Record<CaseStatus, string> = {
  open: "bg-brass/10 text-brass border-brass/30",
  evidence_collection: "bg-ink/5 text-ink border-ink/20",
  under_review: "bg-alert/10 text-alert border-alert/30",
  closed: "bg-moss/10 text-moss border-moss/30",
};

export default function StatusBadge({ status }: { status: CaseStatus }) {
  return (
    <span className={`stamp text-[10px] px-2 py-1 border ${STYLES[status]}`}>
      {LABELS[status]}
    </span>
  );
}
