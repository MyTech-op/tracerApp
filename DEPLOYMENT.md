# SEOOps — Where & How to Deploy

SEOOps is a full SEO-plus platform: FastAPI backend (crawl engine, AI fixes, lead tracking,
**reporting**), Celery worker pool, MySQL, Redis, and a Next.js frontend. Reporting is the
product's centerpiece: a Reporting Center (`/reports`) with score trends, issue analytics,
CSV exports, and shareable client portal links.

## What actually needs to run

| Component | Tech | Why |
|---|---|---|
| `frontend` | Next.js 14 (port 3000) | UI, reports pages |
| `backend` | FastAPI / uvicorn (port 8000) | API, crawl orchestration |
| `celery_worker` | Celery | Background crawl jobs |
| `celery_beat` | Celery Beat | Daily automated scans (keeps report trends populated) |
| `redis` | Redis 7 | Celery broker / result backend |
| `mysql` | MySQL 8 | All persistent data (websites, pages, issues, snapshots, leads, jobs) |
| `phpmyadmin` | (optional) | Local DB admin — **remove in production** |

No headless-browser binaries are needed at runtime — the crawler uses `httpx` + BeautifulSoup.
The only external dependency is an AI provider key (`GEMINI_API_KEY`, or `OPENAI_API_KEY` if you
set `AI_PROVIDER=openai`). Without a key, AI fixes, keyword research, and backlink profiles
degrade gracefully; crawling and reporting still work.

---

## Option A — Single VPS with Docker Compose (recommended for most launches)

Best when: you want one bill, full control, cheapest path to production, ~$6–24/month.

Good providers: **Hetzner** (CX22/CX32 — best price/perf), **DigitalOcean** (droplet),
**Vultr**, **Contabo**, or any Ubuntu 22.04/24.04 VPS.

```bash
# 1. Install Docker + Compose plugin on the VPS
curl -fsSL https://get.docker.com | sh

# 2. Clone the project and configure secrets
git clone <your-repo-url> seoops && cd seoops
cp .env.example .env
#   - Generate a strong SECRET_KEY:  openssl rand -hex 32
#   - Set GEMINI_API_KEY to a real key (the committed one is a placeholder)
#   - Point DATABASE_URL/REDIS_URL at the compose services (already default in docker-compose.yml)

# 3. Start everything
docker compose up -d --build
```

Then expose it safely:

- Put **Caddy** (or nginx) in front for automatic HTTPS:
  `seoops.example.com -> backend:8000`, `app.example.com -> frontend:3000`.
- Caddy one-liner reverse proxy:
  ```caddyfile
  seoops-api.example.com { reverse_proxy backend:8000 }
  app.example.com          { reverse_proxy frontend:3000 }
  ```
- **Never** expose phpMyAdmin publicly — comment that service out in production.

### Required code/config changes before going live

1. **Frontend API URL** — `frontend/src/lib/api.ts` now reads `NEXT_PUBLIC_API_URL`
   (falling back to `http://localhost:8000/api/v1`). Set it at build time to your backend,
   e.g. `NEXT_PUBLIC_API_URL=https://seoops-api.example.com/api/v1` (must include `/api/v1`,
   matching the FastAPI route prefix).
2. **CORS**: `app/main.py` currently allows `*`. Once frontend and API are on different
   origins, restrict `allow_origins` to your frontend domain(s).
3. **Secrets**: replace `SECRET_KEY`, `MYSQL_*` passwords, and the default
   `GEMINI_API_KEY` in `.env` / docker-compose.
4. **Backups**: the MySQL volume (`mysql_data`) holds everything. Nightly dump:
   ```bash
   docker exec seoops_mysql mysqldump -u seoops_user -p seoops_db > backup_$(date +%F).sql
   ```
   Restore with `docker exec -i seoops_mysql mysql ... < backup.sql`.

Cost: Hetzner CX22 (~€4/mo) comfortably runs the whole stack for light-to-moderate crawling
(25 pages/scan default). Scale up RAM if you raise `max_pages` or scan many sites in parallel.

---

## Option B — Managed PaaS (Railway / Render / Fly.io)

Best when: you want zero server ops, managed databases, auto-deploys from GitHub.

Because this app needs **MySQL + Redis + a background worker**, it splits into services:

**Railway** (simplest fit — native MySQL and Redis):
1. Provision `MySQL` and `Redis` plugins; copy their connection strings.
2. Deploy `backend/` as a service → start command
   `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
3. Deploy `backend/` again as a second service (same repo) → start command
   `celery -A app.worker.celery worker --loglevel=info`. Set it to not receive public traffic.
4. Add a third `backend/` service → `celery -A app.worker.celery beat --loglevel=info`
   to run the daily automated scans (configurable via `SCHEDULED_SCAN_HOUR`, default 06:00).
5. Deploy `frontend/` → `npm run build && npm run start`.
6. Set env vars on every service: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`,
   `GEMINI_API_KEY` (or `AI_PROVIDER=openai` + `OPENAI_API_KEY`).

**Render**: same split — `web` (backend), a worker service (Celery), a static site or
web service for the frontend. Use Render's **MySQL** (or any external MySQL) and Redis
(Render Redis or a free Redis Cloud tier). Background workers need a paid plan to stay
alive continuously.

**Fly.io**: `fly launch` per service; attach `fly postgres` won't work (app needs MySQL),
so use Upstash/Redis Cloud + PlanetScale or a managed MySQL.

Watch-outs on PaaS:
- **Ephemeral disk**: never rely on local files; DB volume must be managed MySQL.
- **Worker must run 24/7** for scans to be asynchronous (or accept the sync fallback —
  the API already falls back to running crawls inline if Celery is unreachable).
- Costs scale with running hours; a hobby worker + managed DB is roughly
  **$7–25/month** depending on provider.

---

## Option C — Kubernetes / Docker-native clouds (when it grows)

Best when: multiple agencies/teams, per-tenant isolation, autoscaling crawlers.

- **DigitalOcean App Platform / AWS ECS / GCP Cloud Run + Cloud SQL (MySQL) + ElastiCache (Redis)**:
  run backend + celery as separate services, frontend as a static build served from CDN.
- **K8s (k3s on your own VPS, or managed EKS/GKE)**: the provided `Dockerfile`s are already
  container-ready; add `Deployment`/`Service` manifests and a `HorizontalPodAutoscaler`
  on the celery worker when crawl queues grow.
- At this stage: move `page_snapshots.raw_seo_json` to object storage (S3/R2) and keep only
  metadata in MySQL, and add Celery Beat for **scheduled reporting emails** (weekly client
  reports) — see roadmap below.

---

## Option D — Vercel + Neon (all serverless, no VPS)

Best when: you want everything on Vercel with a managed Postgres (Neon) and are willing to
accept serverless trade-offs. **This works** — Vercel now runs FastAPI natively on its
Python runtime, and Neon is Postgres. The app was written for MySQL, so this path swaps the
database dialect and replaces Celery/Beat with a Vercel Cron. The pieces are already in the
repo: Postgres driver, a `CRON_SECRET`-guarded `/api/v1/scan/cron` endpoint that runs crawls
inline, and `backend/vercel.json` + `backend/pyproject.toml` with the function duration and
daily cron preconfigured.

### What changes vs the VPS path

1. **Database → Neon Postgres.** The SQLAlchemy models are dialect-agnostic, so this is a
   config change:
   `DATABASE_URL=postgresql+psycopg2://<neon-user>:<pass>@<host>/<db>?sslmode=require`
   (`psycopg2-binary` is already in `backend/requirements.txt`). Tables are created on first
   boot (`app.main` calls `create_all`); seed the admin with `python app/seed.py`.
2. **Background workers → Vercel Cron.** Celery/Redis/Beat can't run on Vercel. The daily
   cron hits `POST /api/v1/scan/cron`, which runs crawls inline (no broker). It is guarded
   by `CRON_SECRET`: set it in the Vercel project env and Vercel automatically sends it as
   `Authorization: Bearer $CRON_SECRET`. Configured in `backend/vercel.json` (daily 06:00).
3. **Two Vercel projects from the same repo:**
   - **Frontend** → project root `frontend/` (Next.js, auto-detected).
     Env: `NEXT_PUBLIC_API_URL=https://<backend-project>.vercel.app/api/v1`.
   - **Backend** → project root `backend/` (Python/FastAPI; entrypoint pinned to
     `app.main:app` via `backend/pyproject.toml`).

### Vercel limits — read before relying on it

- **Function duration**: `maxDuration` is set to **300s** in `backend/vercel.json`. Hobby
  plans cap functions at **60s**, too short for multi-site crawls — use Pro (or keep
  `max_pages` low; the cron endpoint defaults to 15 pages/site).
- **Sequential crawls**: scans run one site after another inside a single invocation. With
  `max_pages=15` and ~1–2s/page that's fine for a handful of sites; for many clients, split
  cron runs per site via the `website_ids` body param.
- **Manual scans**: the "Scan Website Now" button falls back to running the crawl inline
  (no broker) — on Vercel keep it light, since a big site can exceed the duration cap.
- **Bundle size**: `playwright` in `requirements.txt` is *not* used by the crawler
  (httpx + BeautifulSoup) and bloats the Vercel bundle. For the Vercel project, trim it
  (and `celery`/`redis` if you never use the VPS path) to stay comfortably under limits.
- **CORS**: `allow_origins=["*"]` already permits the Vercel frontend origin.

### Neon specifics

- Use Neon's **pooled** connection string for serverless workloads.
- The only raw SQL in the app (`ALTER TABLE crawl_jobs ADD COLUMN avg_score INTEGER NULL`
  in `app/main.py`) is valid Postgres, so existing installs upgrade cleanly.
- Backups and point-in-time recovery are built in on paid plans.

Cost: Vercel Pro $20/mo (needed for 300s functions) + Neon ~$19/mo — vs Option A's single
~$5–6/mo VPS. Pay the serverless premium only if "no servers" is a hard requirement.

---

## Google Search Console (real search data)

The app shows **real clicks, impressions, and positions** from Google when a website owner
connects Search Console (free — no Semrush/Ahrefs cost):

1. **Google Cloud setup** — create an OAuth client ID (Web application) at
   https://console.cloud.google.com/apis/credentials with scope
   `https://www.googleapis.com/auth/webmasters.readonly`. Add the redirect URI:
   - Local: `http://localhost:8000/api/v1/gsc/callback`
   - Vercel: `https://<backend-project>.vercel.app/api/v1/gsc/callback`
2. **Env vars**: `GSC_CLIENT_ID`, `GSC_CLIENT_SECRET`, `GSC_REDIRECT_URI`, `FRONTEND_URL`.
3. **Connect** from the report page (`/reports/[id]` → "Connect Google Search Console").
   The user verifies the domain with Google; the app auto-picks the matching property
   (`sc-domain:` preferred).
4. **Data**: daily site-level metrics (clicks, impressions, CTR, avg position) for the last
   30 days + a bounded top-25-queries snapshot. Synced on connect, via the "Sync Now"
   button, via the daily `gsc-daily-sync` Celery Beat task, and via Vercel Cron
   (`/api/v1/gsc/cron`, 07:30, guarded by `CRON_SECRET`).

OAuth tokens are encrypted at rest with a key derived from `SECRET_KEY`.

---

## Stripe billing (agency plans: Starter / Growth / Agency)

Paid tiers are enforced on **site count**, **pages per scan**, and **scan frequency**:

| Plan | Price | Sites | Pages/scan | Scan interval |
|---|---|---|---|---|
| Free | $0 | 1 | 10 | 24h |
| Starter | $49/mo | 3 | 25 | 24h |
| Growth | $99/mo | 10 | 50 | 6h |
| Agency | $199/mo | 25 | 100 | 2h |

Setup:

1. Create a Stripe account and get a secret key (https://dashboard.stripe.com/apikeys).
2. **Env vars**: `STRIPE_SECRET_KEY`, `FRONTEND_URL` (already used by GSC), and — optionally
   — `STRIPE_PRICE_STARTER/GROWTH/AGENCY`. If the price IDs are left blank, SEOOps
   auto-creates the monthly prices on the first checkout (products named "SEOOps …").
3. **Webhook**: in the Stripe dashboard add an endpoint for `checkout.session.completed`,
   `customer.subscription.updated`, and `customer.subscription.deleted` pointing at
   `https://<your-backend>/api/v1/billing/webhook`. Copy the signing secret into
   `STRIPE_WEBHOOK_SECRET`. (Without a signing secret, the webhook still works in dev mode
   but **always set it in production**.)
4. **Frontend**: the `/billing` page (linked from the dashboard header) shows plan cards,
   usage meters, an Upgrade button that redirects to Stripe Checkout, and a
   "Manage Billing" button for the Stripe customer portal (cancel / downgrade).

How limits are enforced:

- Site cap → `POST /api/v1/website` returns **402** when the plan's site limit is hit.
- Scan frequency → `POST /api/v1/scan` returns **429** with `next_allowed_at` when the
  interval hasn't elapsed.
- Page cap → every crawl path (manual, cron, Celery Beat, and the crawl task itself)
  clamps `max_pages` to the plan's cap, so no caller can exceed it.
- Plan changes from Stripe events are applied automatically via the webhook; when a
  subscription is canceled the user falls back to the Free plan.

`/billing/status` exposes the current plan, subscription state, and usage so the frontend
can meter against it.

---

## White-label PDF reports

`GET /api/v1/reports/website/{id}/pdf` (auth required) renders a client-ready PDF entirely
server-side with **fpdf2** (pure Python — no system PDF deps, safe on Vercel/Neon):

- Agency name + uploaded logo in the header, site domain, generated date
- KPI cards (health score, delta, open issues, fixes deployed, leads)
- SEO health score trend line chart (from crawl history)
- Google Search Console block: clicks/impressions/CTR/position, a 30-day trend chart, and
  top queries (shown when the site is connected)
- Fixes deployed timeline and open-issue breakdown tables, footer with agency name and
  page numbers on every page

Set the branding under **Agency Settings** (agency name + logo upload, PNG/JPEG up to 2 MB;
the logo is stored in the `users.logo` column as a data URL). The **Download PDF** button on
the report page (`/reports/[id]`) fetches it with the auth token and saves the file.

---

## Production checklist (every option)

- [ ] `NEXT_PUBLIC_API_URL` set to the real backend URL (not localhost)
- [ ] `SECRET_KEY` and DB passwords replaced with strong random values
- [ ] Real `GEMINI_API_KEY` (or OpenAI key) set; `AI_PROVIDER` matches
- [ ] HTTPS enforced (Caddy/nginx or PaaS-managed TLS)
- [ ] CORS restricted to your frontend origin(s)
- [ ] MySQL backups scheduled (nightly dump; test a restore)
- [ ] phpMyAdmin disabled or VPN-only
- [ ] `celery_beat` service running (daily automated scans; trend charts need it or manual scans)
- [ ] Logs shipped somewhere (docker logs / PaaS dashboards) — crawl failures surface in
      `crawl_jobs.error_message`
- [ ] Seed the default admin (`admin@seo.com` / `admin@123`) once, then change the password
      (`backend/app/seed.py` creates it on first run)

---

## Quick roadmap to make reporting fully self-serve

Already shipped in this iteration: Reporting Center, per-site score-trend charts, issue and
lead analytics, CSV export, print-to-PDF, and a shareable public client portal.

Natural next steps:
1. **Scheduled reporting** — Celery Beat task that emails a weekly PDF/CSV summary to each
   client (needs SMTP settings in `Settings`).
2. **Report history durability** — crawl jobs now record `avg_score` per scan and daily
   automated scans (Celery Beat) keep trends populated; a dedicated `report_snapshots` table
   would let history survive even if crawl jobs are pruned.
3. **Keyword-rank tracking** — wire `seo/keywords/generate` results into a persisted
   `keyword_rankings` table so the trend chart includes rankings, not just health scores.
