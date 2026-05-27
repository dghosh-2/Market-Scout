# MarketScout — Agent Reference

> Quick-reference for AI agents and developers working in this codebase.
> Live at: [market-scout-chi.vercel.app](https://market-scout-chi.vercel.app) · API: `https://market-scout-emg1.onrender.com`

---

## What This Project Is

AI-assisted stock research tool for self-directed investors. Users type a natural-language query ("analyze Apple for me"), and the app resolves the ticker, gathers live market data, runs an OpenAI-powered analysis, streams progress updates to the UI, persists the report, and renders a downloadable PDF.

---

## Monorepo Layout

```
Market-Scout/
├── frontend/          # Next.js 14 App Router (deployed to Vercel)
├── backend/           # FastAPI + Python 3.11 (deployed to Render)
├── vercel.json        # Builds frontend/, outputs frontend/.next
├── render.yaml        # Render web service — backend/, Python 3.11
├── railway.json       # Alternate Railway deploy
├── Procfile           # uvicorn main:app --host 0.0.0.0 --port $PORT
├── package.json       # Root scripts: dev (concurrently), setup, build
├── requirements.txt   # Top-level copy of backend deps
└── .cursorrules       # Dev conventions (note: mentions JSON storage — actual store is smoldb)
```

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14, React 18, TypeScript 5.3 (strict), Tailwind CSS 3.4 |
| Backend | FastAPI, Python 3.11, Uvicorn |
| AI | OpenAI `gpt-4o-mini` — query parsing, ticker resolution, report narrative |
| Market data | yfinance — quotes, financials, history, news |
| Persistence | smoldb (HTTP SQL API to a hosted SQLite at `smoldb.fly.dev`) |
| PDF | ReportLab → `backend/output/reports/` (ephemeral on Render disk) |
| Rate limiting | slowapi — 5 req/min on `POST /api/research` |
| HTTP client (FE) | Axios (`lib/api.ts`) + native `fetch` / `EventSource` directly in pages |
| Charts | HTML5 Canvas (research page price chart, landing ParticleWave) |
| Auth | **None** — fully public app |

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Notes |
|----------|----------|-------|
| `OPENAI_API_KEY` | Yes | All OpenAI calls |
| `SMOLDB_KEY` | Yes | `x-api-key` header to smoldb |
| `SMOLDB_URL` | No | Defaults to project-specific URL in `settings.py` |
| `BACKEND_HOST` | No | Default `0.0.0.0` |
| `BACKEND_PORT` | No | Default `8000` |
| `PORT` | Render/Railway | Injected by platform |
| `VERCEL` / `AWS_LAMBDA_FUNCTION_NAME` | No | If set, PDFs go to `/tmp/reports` |

### Frontend (`frontend/.env`)

| Variable | Notes |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | Backend origin without trailing `/api`. E.g. `https://market-scout-emg1.onrender.com`. `getApiBase()` in `lib/env.ts` appends `/api`. In dev, Next rewrites `/api/*` → `localhost:8000/api/*`. |

---

## Backend Architecture (`backend/`)

### Entry Point

`main.py` — creates FastAPI app, configures CORS (Vercel prod + localhost), mounts `StaticFiles` at `/reports`, registers lifespan (`init_schema()`), and includes all routers.

### Routers (`backend/app/routers/`)

| File | Mount | Key endpoints |
|------|-------|---------------|
| `research_router.py` | `/api/research` | `POST /` (rate-limited), `GET /stream/{query}` (SSE), `GET /preview/{query}`, `GET /status/{report_id}` |
| `papers_router.py` | `/api/papers` | `GET /` (all, grouped), `GET /{company}`, `GET /report/{report_id}` |
| `feedback_router.py` | `/api/feedback` | `POST /` — re-runs full research as new version |
| `portfolio_router.py` | `/api/portfolio` | CRUD + `GET /summary` (live prices via yfinance) |

### Research Pipeline

```
User query (string)
  ↓ parse_user_query()          agents/orchestrator.py — AI + fast paths + separator/map heuristics
  ↓ resolve_company_to_ticker() agents/orchestrator.py — hardcoded map → pattern → AI fallback
  ↓ run_master_agent()          agents/master_agent.py — fetch all yfinance data → single GPT call → news reflections
  ↓ get_portfolio_context()     portfolio_router.py — injected as "portfolio_fit" section
  ↓ smoldb persist              db/smoldb.py
  ↓ ReportLab PDF               reports/generator.py → backend/output/reports/<file>.pdf
```

`GET /api/research/stream/{query}` runs the entire pipeline in a background thread and emits SSE `ProgressUpdate` events as steps complete; the final event carries the full `ResearchResponse`.

### Agents (`backend/app/agents/`)

| File | Role |
|------|------|
| `orchestrator.py` | Query parsing, ticker resolution |
| `master_agent.py` | Central analysis — gathers tools, calls GPT once, reflects on news |
| `tools.py` | yfinance wrappers: company info, financials, history, news |
| `prompts.py` | Legacy prompt templates (live path is in `master_agent.py`) |

**Custom sections**: `detect_custom_section_topic()` in `master_agent.py` maps user intent (leadership, ESG, M&A, etc.) into named sections. `omit_sections` / `add_sections` query params on SSE endpoint let clients filter.

### Database (`backend/app/db/smoldb.py`)

HTTP SQL over smoldb. Tables initialized at startup:

| Table | Key columns |
|-------|-------------|
| `queries` | `id` (UUID PK), `request`, `company`, `ticker`, `created_at` |
| `reports` | `id`, `query_id` FK, `company`, `ticker`, `report_path`, `version`, `created_at` |
| `report_data` | `report_id` PK/FK, `company_info`, `financial_data`, `risk_data`, `news_data`, `analysis` (JSON strings) |
| `portfolio` | `ticker` PK, `shares`, `purchase_price`, `company_name`, `holding_id`, `created_at`, `updated_at` |

**Report versioning**: `version` = count of prior reports for that ticker + 1.

### Utilities (`backend/app/utils/`)

- `llm.py` — OpenAI client wrapper
- `parser.py` — JSON extraction from LLM responses
- `validation.py` — Request validation helpers

---

## Frontend Architecture (`frontend/`)

### Pages (`frontend/app/`)

| Route | File | Notes |
|-------|------|-------|
| `/` | `app/page.tsx` | Hero + ParticleWave animation |
| `/research` | `app/research/page.tsx` | Main feature: SSE stream, canvas price chart, analysis display, version picker, feedback, PDF link |
| `/portfolio` | `app/portfolio/page.tsx` | Holdings CRUD, summary stats, "Research all" (sequential POST with 13s delay to respect rate limit) |
| `/papers` | `app/papers/page.tsx` | All reports grouped by company |
| `/papers/[company]` | `app/papers/[company]/page.tsx` | Per-ticker versions + feedback per report |
| `/about` | `app/about/page.tsx` | Product flow, data sources, disclaimer |

### Components (`frontend/components/`)

| Component | Role |
|-----------|------|
| `NavBar.tsx` | Sticky top nav |
| `QueryProvider.tsx` | TanStack React Query client (1 min stale time) — **provider only; no hooks used in pages yet** |
| `ParticleWave.tsx` | Canvas animation on home page |

### Libraries (`frontend/lib/`)

| File | Role |
|------|------|
| `env.ts` | `getApiBase()` / `getBackendOrigin()` — resolves API URL for dev vs prod |
| `api.ts` | Typed Axios helpers: `researchApi`, `papersApi`, `feedbackApi`, `portfolioApi` |
| `helpers.ts` | Date/ticker formatting utilities |

**Important**: Most pages bypass `api.ts` and call `fetch` / `EventSource` directly. `api.ts` and React Query are under-utilized — prefer consolidating to them on future work.

### State Management

- `useState` / `useEffect` / `useCallback` — primary pattern everywhere
- React Query — provider is configured but no `useQuery`/`useMutation` calls exist yet
- No Redux, Zustand, or Context API beyond the Query client wrapper
- URL params: `?ticker=` on research, `?report=` on papers

### Styling

Dark minimal design — black/white palette, Tailwind CSS. Inter font. `layout.tsx` applies dark theme globally.

---

## Scripts

### Root (run from `Market-Scout/`)

```bash
npm run dev       # concurrently starts backend + frontend
npm run setup     # npm install everywhere + venv + pip install
npm run build     # cd frontend && npm run build
```

### Backend (manual)

```bash
cd backend
source venv/bin/activate
python main.py    # dev, port 8000 with reload
```

### Frontend

```bash
cd frontend
npm run dev       # next dev
npm run build     # next build
npm run lint      # next lint
```

---

## Key Caveats for Agents

1. **`.cursorrules` is outdated** — it mentions JSON file storage. Real persistence is smoldb.
2. **`CODEBASE_SUMMARY.md` is partially stale** — references SQLAlchemy, `file_storage.py`, and agent files that no longer exist in their described form.
3. **PDFs are ephemeral** on Render — redeploying clears `backend/output/reports/`. Links in smoldb will 404 after redeploy.
4. **React Query is a stub** — `QueryProvider` wraps the app but no queries are wired up. Adding hooks is straightforward using `lib/api.ts`.
5. **Most pages use raw `fetch`** — not `api.ts` helpers. When editing pages, check for duplicate data-fetching logic.
6. **Rate limit**: `POST /api/research` is hard-limited to 5/min via slowapi. Portfolio "Research all" has a 13s delay between calls to stay under it.
7. **No tests** — zero test files exist in the repo.
8. **No auth** — entirely public; smoldb key is server-side only.
9. **`data/fetch_yfinance.py` and `data/fetch_news.py`** exist but the live orchestration uses `agents/tools.py`. The `data/` files are legacy/alternate helpers.
10. **Recharts** is in `package.json` but never imported. The price chart is plain Canvas.

---

## Analysis Report Sections

Stored as JSON string in `report_data.analysis`. Typical keys:

| Key | Content |
|-----|---------|
| `recommendation` | Buy/Hold/Sell with rationale |
| `company_overview` | Business description and moat |
| `financial_analysis` | Revenue, margins, ratios |
| `risk_assessment` | Key risks |
| `news_analysis` | Recent news summary |
| `user_topics` | Topics parsed from the query |
| `custom_section` | Topic detected from user focus (ESG, M&A, leadership, etc.) |
| `portfolio_fit` | How the stock fits existing holdings |

---

## Deployment

| Service | What it hosts | Config |
|---------|---------------|--------|
| **Vercel** | Next.js frontend | `vercel.json` |
| **Render** | FastAPI backend | `render.yaml` |
| **Railway** | Alternate backend deploy | `railway.json`, `Procfile` |
| **smoldb (fly.dev)** | SQLite persistence | `SMOLDB_URL` + `SMOLDB_KEY` |

Dev API routing: `frontend/next.config.js` rewrites `/api/*` → `http://localhost:8000/api/*` in development only.
