# Autonomous AI Investigation Platform — Architecture Design (Phase 1)

**Status:** Design for review. No code generated yet, per your requested workflow.

---

## 1. System Overview

A human-in-the-loop investigation support platform. AI agents ingest, index, and analyze evidence; humans review every finding, approve every risk score, and sign off on every report. The system never issues findings of guilt or automatically escalates cases — it surfaces evidence and recommendations for a qualified investigator to accept, edit, or reject.

**Design principles**
- Every AI output is provenance-tagged (source doc, page, confidence) and immutable once logged.
- Every AI-generated finding has a required human-approval gate before it can move case status forward.
- Evidence is write-once/append-only with hash-chained integrity (chain of custody).
- Agents are advisory tools with bounded autonomy — no agent can close a case, contact a third party, or file anything externally.

---

## 2. Tech Stack

| Layer | Recommendation | Why |
|---|---|---|
| Backend services | Python (FastAPI) for AI/agent services; Go for high-throughput ingestion/indexing services | FastAPI has best AI-ecosystem support; Go for performance-critical evidence pipelines |
| Frontend | React + Next.js, TypeScript, Tailwind, shadcn/ui | SSR for dashboards, strong ecosystem |
| Relational DB | PostgreSQL | ACID, JSONB for flexible metadata, mature RBAC/row-level security |
| Graph DB | Neo4j | Best-in-class for relationship/link analysis and Cypher querying |
| Vector DB | Qdrant or pgvector (Postgres extension) | Qdrant if scale is large; pgvector to reduce infra sprawl for MVP |
| Object storage | S3-compatible (AWS S3 / MinIO for on-prem) | Evidence files, immutable storage with versioning + Object Lock |
| Message queue | Kafka (event backbone) + Redis Streams (lightweight agent task queue) | Kafka for durable audit-relevant event log, Redis for fast task dispatch |
| Workflow / orchestration | Temporal | Durable, resumable long-running investigation workflows with human-approval steps |
| AI orchestration | LangGraph or a custom agent graph on top of Claude via API, with Temporal as the durability layer | Explicit state machines beat "autonomous loops" for auditability |
| Auth | Keycloak (OIDC/SAML) or Auth0 | MFA, SSO, fine-grained RBAC/ABAC |
| Secrets | HashiCorp Vault | Dynamic secrets, encryption-as-a-service |
| Logging/Monitoring | OpenTelemetry → Grafana Loki + Prometheus + Grafana; Sentry for errors | Standard observability stack |
| Containerization | Docker + Kubernetes (EKS/GKE/AKS or on-prem) | Standard for microservices at this scale |
| CI/CD | GitHub Actions → ArgoCD (GitOps) | Auditable deployment trail — important for a forensic-adjacent system |
| Cloud | AWS (GovCloud if public-sector) or Azure Government | GovCloud/Azure Gov matter if this touches government investigations |
| Disaster recovery | Multi-AZ + cross-region async replication; RPO ≤ 15 min, RTO ≤ 1 hr targets | Evidence loss is not an acceptable failure mode |

---

## 3. Microservices Map

```
├── gateway (API gateway, auth, rate limiting)
├── case-service            (case CRUD, status machine)
├── evidence-service         (ingestion, hashing, chain-of-custody, storage)
├── ocr-service               (document → text)
├── document-intel-service   (parsing, classification, entity extraction)
├── financial-analysis-service (transaction/ledger anomaly detection)
├── procurement-service       (bid-rigging / conflict-of-interest detection)
├── link-analysis-service     (Neo4j graph builder + queries)
├── timeline-service          (event sequencing)
├── risk-scoring-service      (composite risk model, always advisory)
├── interview-prep-service    (question generation from case facts)
├── report-service            (drafting, templating, export)
├── compliance-service        (regulatory rule checks)
├── agent-orchestrator        (Temporal workflows, agent dispatch)
├── search-service            (RAG: vector + keyword hybrid search)
├── notification-service
├── audit-service             (immutable audit log, tamper-evidence)
└── admin-service             (users, roles, org config)
```

Each service owns its own schema/tables; cross-service reads go through APIs or an event-driven read model — not shared DB access.

---

## 4. AI Agents

All agents share this contract:

- **Input**: structured request + case context + relevant evidence refs (never raw case dump — retrieval-scoped).
- **Output**: structured JSON with `finding`, `confidence`, `source_citations[]`, `reasoning_summary`.
- **Memory**: short-term = current task context window; long-term = pgvector/Qdrant embeddings of case evidence + Neo4j graph state. No cross-case memory (case isolation is a hard requirement for privilege/confidentiality).
- **Approval gate**: every output lands in a `pending_review` queue; nothing auto-applies to the case record.

| Agent | Core responsibility | Key tools |
|---|---|---|
| Investigation Commander | Plans task sequence, delegates to sub-agents, tracks case progress | Temporal workflow API, case-service |
| Evidence Collection Agent | Normalizes intake (upload, email, scan), triggers hashing | evidence-service, S3, hash/chain-of-custody |
| OCR Agent | Converts scans/images to structured text | Tesseract/AWS Textract/Azure Document Intelligence |
| Document Intelligence Agent | Classifies doc type, extracts entities, dates, amounts | NER models, LLM extraction, schema validators |
| Financial Investigation Agent | Flags anomalous transactions, structuring, shell patterns | Statistical anomaly detection, rules engine, LLM narrative |
| Procurement Fraud Detection Agent | Bid-rigging, conflict-of-interest, vendor overlap detection | Graph queries, statistical bid analysis |
| Compliance Agent | Maps findings to regulatory frameworks (FCPA, UK Bribery Act, etc.) | Rule library, LLM mapping w/ citation |
| Legal Research Agent | Surfaces relevant statutes/precedent for investigator review | Legal DB / search API, RAG |
| Link Analysis Agent | Builds/queries relationship graph, surfaces hidden connections | Neo4j Cypher queries |
| Timeline Agent | Assembles chronology from extracted dates/events | timeline-service, LLM sequencing |
| Interview Preparation Agent | Drafts question sets from case facts and gaps | RAG over case evidence |
| Risk Scoring Agent | Produces advisory composite risk score with rationale | Weighted rules + LLM rationale, always human-reviewed |
| Report Writing Agent | Drafts narrative report sections from approved findings only | Templating, report-service |
| Case Summary Agent | Rolls up case state for dashboards/handoffs | Read-only aggregation |

**Error handling pattern (all agents):** on low-confidence or missing-data, agent emits a `needs_human_input` status rather than guessing; on tool failure, Temporal retries with backoff, then routes to a human queue.

---

## 5. Investigation Workflow (Temporal state machine)

```
Case Created → Evidence Intake → Evidence Indexing (OCR + embeddings + graph)
  → AI Analysis (parallel: financial / procurement / document intel)
  → Relationship Extraction → Timeline Construction → Risk Scoring (draft)
  → HUMAN REVIEW GATE (approve/reject/request more analysis)
  → Report Drafting → HUMAN REVIEW GATE → Final Report → Case Closure
```

Every arrow into a "gate" requires an authenticated, role-checked human action, logged to the audit-service with actor, timestamp, and diff.

---

## 6. Data Model (relational — condensed)

Core tables: `cases`, `evidence`, `evidence_chain_of_custody`, `persons`, `companies`, `government_agencies`, `case_entities` (join table w/ role), `transactions`, `contracts`, `procurement_records`, `witnesses`, `interviews`, `interview_questions`, `events` (timeline), `findings` (status: draft/pending_review/approved/rejected), `reports`, `report_versions`, `users`, `roles`, `permissions`, `role_permissions`, `audit_logs` (append-only, hash-chained).

Key constraints: `findings.status` cannot reach `approved` without a `reviewed_by` user + timestamp; `evidence` rows are immutable after `hash_sealed = true`; all FK relationships preserve full history via `case_entities` rather than overwriting.

---

## 7. Graph Model (Neo4j)

Nodes: `Person`, `Company`, `Agency`, `Transaction`, `Contract`, `Case`, `Document`.
Relationships: `OWNS`, `EMPLOYED_BY`, `SIGNED`, `PAID`, `RELATED_TO`, `BID_ON`, `AWARDED`, `MENTIONED_IN`.

Example hidden-relationship query: find undisclosed common ownership between two bidders on the same contract (paths of length ≤3 between `Company` nodes via shared `Person` owners, filtered to companies that both `BID_ON` the same `Contract`).

---

## 8. AI Capabilities

RAG over case-scoped vector index (hard tenant/case isolation — no cross-case retrieval); hybrid semantic + keyword search; NER/entity extraction; multi-document summarization with citations; contradiction detection (compare extracted statements across documents/interviews, flag conflicts for human review); anomaly detection (statistical + LLM-assisted narrative); recommendation engine (next-best investigative step, advisory only); autonomous task planning bounded by Temporal workflow definitions — agents choose *how* to execute a step, never *whether* a case advances.

---

## 9. Security

Zero Trust (every service-to-service call authenticated via mTLS + short-lived tokens); OIDC/JWT + MFA at the gateway; RBAC + ABAC (case-level access lists — investigators only see assigned cases); encryption at rest (KMS-managed) and in transit (TLS 1.3); evidence integrity via SHA-256 hashing + hash chain, checked on every access; tamper-evident audit log (append-only, periodically anchored/signed); Vault-managed secrets; least-privilege IAM.

---

## 10. Frontend Modules

Case dashboard, evidence explorer (with OCR text overlay), relationship graph (Neo4j-backed force-directed viz), interactive timeline, financial analysis dashboard, investigation assistant chat (RAG-grounded, always shows citations), document viewer, risk dashboard (shows score + full rationale + human override), report generator, admin console (users/roles/audit).

---

## 11. APIs

REST for CRUD-heavy resources (cases, evidence, users). GraphQL is worth it specifically for the relationship-graph and case-summary views, where clients need flexible, nested queries (e.g., "case + entities + findings + timeline" in one round trip) — avoids REST over-fetching for the graph explorer UI.

---

## 12. Milestones

1. **MVP** — case-service, evidence-service (upload + hash), OCR, basic document intel, Postgres schema, auth, simple dashboard. No agents yet, manual review only.
2. **Core AI** — RAG search, entity extraction, timeline agent, risk scoring (draft-only), human review gates, audit-service.
3. **Graph + Financial** — Neo4j integration, link-analysis agent, financial/procurement fraud agents, relationship-graph UI.
4. **Reporting + Compliance** — report-writing agent, compliance agent, interview-prep agent, GraphQL layer.
5. **Enterprise hardening** — Zero Trust rollout, DR/multi-region, SOC2-oriented controls, load testing, admin console, full RBAC/ABAC.

Each milestone would get its own detailed spec (features, DB migrations, tests, deployment plan) when you're ready to scope it.

---

**Next step, per your instructions:** review this design, tell me what to adjust, and pick which module to build first. I'd suggest starting with `evidence-service` (ingestion + hashing + chain-of-custody) since everything else depends on it.
