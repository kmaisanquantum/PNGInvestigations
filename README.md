# Investigation Platform — MVP

Case management + evidence intake with chain-of-custody, built as the first milestone of the
full [Autonomous AI Investigation Platform](./investigation-platform-architecture.md) design.

**What's included in this MVP:**
- FastAPI backend: JWT auth, RBAC (`admin` / `investigator` / `reviewer` / `viewer`), case CRUD,
  evidence upload with SHA-256 hashing + integrity verification on every download, hash-chained
  append-only audit log.
- Next.js frontend: login, case dashboard, case detail with evidence upload.
- PostgreSQL for storage, local (or mounted) volume for evidence files.
- Docker Compose stack — no other infra required to run it.

**Not included yet** (see the architecture doc for the full roadmap): AI agents, OCR, Neo4j graph,
vector search, Temporal workflows. Those are later milestones — this MVP is the foundation they'll
build on (case-service + evidence-service from the design doc).

---

## Run locally

```bash
cp .env.example .env
# edit .env: set JWT_SECRET (openssl rand -hex 32) and a real POSTGRES_PASSWORD
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs

**First-time setup:** there are no users yet. Create the first admin account:

```bash
curl -X POST http://localhost:8000/api/auth/bootstrap-admin \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","full_name":"Admin","password":"change-me-please"}'
```

This endpoint only works once (while the `users` table is empty). After that, log in at
`/login` and use `/api/auth/register` (admin-only) to create investigator/reviewer/viewer accounts.

## Run tests

```bash
cd backend
pip install -r requirements.txt
pip install pytest httpx
pytest -v
```

---

## Deploy via Coolify on a Vultr Ubuntu server

### 1. Provision the server
- Spin up a Vultr Ubuntu 22.04/24.04 instance (2 vCPU / 4GB RAM minimum for this stack).
- Point a DNS A record at the server's IP if you want a real domain (recommended — Coolify can
  provision Let's Encrypt certs automatically once DNS resolves).

### 2. Install Coolify
SSH into the server and run:
```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```
Follow the prompts, then open `http://<server-ip>:8000` to finish the Coolify setup wizard
(create your Coolify admin account).

### 3. Push this repo to GitHub
```bash
cd investigation-platform
git init
git add .
git commit -m "Investigation Platform MVP"
git branch -M main
git remote add origin https://github.com/<your-org>/investigation-platform.git
git push -u origin main
```

### 4. Create the application in Coolify
1. In the Coolify dashboard: **New Resource → Application → Docker Compose**.
2. Connect your GitHub account/repo (Coolify's GitHub App, or a deploy key for a private repo).
3. Point it at this repository, branch `main`, and select `docker-compose.yml` at the repo root
   as the compose file.
4. Under **Environment Variables**, set (do *not* commit these — set them in Coolify's UI):
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
   - `JWT_SECRET` (generate with `openssl rand -hex 32`)
   - `CORS_ORIGINS` — your public frontend URL, e.g. `https://investigations.yourdomain.com`
5. Set the **domain** for the `frontend` service to your DNS record; Coolify will issue a
   Let's Encrypt certificate automatically.
6. (Optional but recommended) Expose the `backend` service only internally — don't map its port
   publicly if you don't need direct API access from outside; let the frontend's rewrite proxy
   handle all `/api/*` traffic.
7. Click **Deploy**. Coolify will build both images from the Dockerfiles and bring up the stack
   in the order defined by the `depends_on`/healthcheck conditions in `docker-compose.yml`.

### 5. Persistent volumes
The compose file defines two named volumes: `postgres_data` and `evidence_data`. Coolify will
create and persist these automatically across redeploys — evidence files and the database survive
container rebuilds. **Back these up regularly** (Coolify supports scheduled backups for attached
volumes/databases, or you can `docker cp`/`pg_dump` on a cron).

### 6. Post-deploy
- Hit `https://your-domain/api/health` — should return `{"status":"ok"}`.
- Bootstrap the first admin account (same `curl` command as above, against your public domain).
- Log in at `https://your-domain/login`.

### Redeploys
Push to `main` and either enable Coolify's auto-deploy webhook (Application → Webhooks) or click
**Redeploy** in the dashboard. Coolify rebuilds the images and does a rolling restart honoring the
healthchecks defined in the Dockerfiles.

---

## Security notes before going to production

- Change every default in `.env` — especially `JWT_SECRET` and `POSTGRES_PASSWORD`.
- This MVP does not yet implement encryption-at-rest for the evidence volume, MFA, or Vault-based
  secrets management — those are called out in the architecture doc's Security section and are
  planned for a later milestone. Don't store real sensitive evidence on this MVP without adding
  disk-level encryption on the Vultr volume in the meantime.
- Evidence integrity is verified via SHA-256 on every download; a mismatch returns `409` and is
  logged to the audit trail rather than silently serving a possibly-tampered file.
- Run Postgres backups (`pg_dump` on a schedule, or Coolify's built-in DB backup feature) — the
  audit log and chain-of-custody records are the whole point of this system, so losing them is not
  an acceptable failure mode.

## Next milestones

See [`investigation-platform-architecture.md`](./investigation-platform-architecture.md) for the
full roadmap: RAG search, entity extraction, Neo4j link analysis, financial/procurement fraud
agents, Temporal-orchestrated workflows with human-approval gates, and report generation.
