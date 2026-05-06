# Market Scout — Codebase Summary

## What It Is

**Market Scout** is an AI-assisted stock research web application for self-directed investors. Given a plain-English company query (e.g. `"Apple - growth prospects"`), it:

1. Resolves the company to a ticker via a lookup map, ticker pattern detection, or an OpenAI fallback
2. Fetches financial data (via `yfinance`), recent news, and optionally SEC filings
3. Runs an LLM pipeline (OpenAI GPT) to produce a structured multi-section research report
4. Renders the report as a downloadable **PDF** (via ReportLab) and serves it over HTTP
5. Persists reports to a **JSON file store** for browsing history ("Papers")
6. Supports **portfolio tracking** with per-holding valuation, weight, and sector breakdown
7. Injects **portfolio context** into reports when holdings exist so the report includes a "portfolio fit" section
8. Allows **feedback-driven regeneration**: submitting feedback on an existing report triggers a new version

**Live deployment:**
- Frontend → [Vercel](https://market-scout-chi.vercel.app)
- Backend API → `https://market-scout-emg1.onrender.com` (Render)

---

## Repository Layout

```
marketscout/
└── Market-Scout/
    ├── README.md
    ├── package.json          # root: concurrently runs frontend + backend in dev
    ├── requirements.txt      # top-level Python deps (mirrors backend/)
    ├── vercel.json           # Vercel: builds frontend/, outputs frontend/.next
    ├── render.yaml           # Render: Python 3.11, uvicorn main:app
    ├── .cursorrules          # architecture conventions for AI assistants
    ├── .gitignore
    ├── frontend/
    │   ├── package.json
    │   ├── next.config.js
    │   ├── tailwind.config.ts
    │   ├── tsconfig.json
    │   ├── app/
    │   │   ├── layout.tsx              # root layout, navbar, global providers
    │   │   ├── page.tsx                # landing/home
    │   │   ├── globals.css
    │   │   ├── about/page.tsx          # product description + disclaimer
    │   │   ├── research/page.tsx       # main research UI (query input, charts, report)
    │   │   ├── portfolio/page.tsx      # portfolio management UI
    │   │   ├── papers/page.tsx         # report history list
    │   │   └── papers/[company]/page.tsx  # per-company report archive
    │   ├── components/
    │   │   ├── NavBar.tsx              # site navigation
    │   │   ├── QueryProvider.tsx       # TanStack Query wrapper
    │   │   ├── ResearchForm.tsx        # (orphan — not imported anywhere)
    │   │   ├── ReportCard.tsx          # (orphan — references non-existent API routes)
    │   │   └── FeedbackForm.tsx        # (orphan — mismatched IDs vs backend)
    │   └── lib/
    │       ├── api.ts                  # axios client (several routes are stale/wrong)
    │       └── helpers.ts
    └── backend/
        ├── main.py                     # FastAPI app factory, router registration
        ├── Procfile                    # Railway/Heroku: uvicorn main:app
        ├── railway.json                # Railway hosting config
        ├── requirements.txt
        ├── output/reports/             # generated PDFs (served as StaticFiles)
        └── app/
            ├── config/settings.py      # pydantic-settings, loads .env
            ├── schemas/
            │   └── request_schemas.py  # Pydantic request/response models
            ├── utils/
            │   ├── validation.py       # query parsing, ticker resolution
            │   ├── parser.py           # text/LLM response parsing helpers
            │   └── llm.py              # thin OpenAI wrapper (call_openai)
            ├── data/
            │   ├── fetch_yfinance.py   # price history, financials, company info
            │   ├── fetch_news.py       # Yahoo Finance news scraping
            │   ├── fetch_filings.py    # SEC EDGAR (partial / unused in live path)
            │   └── scrape_tools.py     # BeautifulSoup helpers (unused in live path)
            ├── db/
            │   ├── file_storage.py     # JSON file persistence (active)
            │   ├── models.py           # SQLAlchemy ORM models (incomplete/dead)
            │   ├── database.py         # SQLAlchemy engine setup (dead — missing setting)
            │   └── crud.py             # SQLAlchemy CRUD ops (dead)
            ├── reports/
            │   └── generator.py        # ReportLab PDF builder
            ├── agents/
            │   ├── orchestrator.py     # entry point: parse → resolve → master agent
            │   ├── master_agent.py     # tool dispatch, GPT analysis, section assembly
            │   ├── tools.py            # tool execution: company, financials, risk, news
            │   ├── prompts.py          # system/user prompt templates
            │   ├── company_agent.py    # (legacy — not used in live path)
            │   ├── financial_agent.py  # (legacy — not used in live path)
            │   ├── news_agent.py       # (legacy — not used in live path)
            │   └── risk_agent.py       # (legacy — not used in live path)
            └── routers/
                ├── research_router.py
                ├── papers_router.py
                ├── feedback_router.py
                └── portfolio_router.py
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend framework** | Next.js 14 (App Router) |
| **Frontend language** | TypeScript |
| **Styling** | Tailwind CSS |
| **Data fetching (FE)** | TanStack Query + Axios |
| **Charts (FE)** | Canvas API (research page); Recharts declared but not the main chart |
| **Backend framework** | FastAPI |
| **Backend language** | Python 3.11 |
| **ASGI server** | Uvicorn |
| **AI** | OpenAI API (GPT-4 class models) |
| **Financial data** | `yfinance` |
| **News** | Yahoo Finance scraping (BeautifulSoup4) |
| **PDF generation** | ReportLab |
| **Persistence (active)** | JSON flat files (`file_storage.py`) |
| **Persistence (incomplete)** | SQLAlchemy ORM + SQLite/Postgres |
| **Validation** | Pydantic / pydantic-settings |

---

## Configuration

### Environment Variables

The backend loads from `.env` via `pydantic-settings`:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | All LLM calls |
| `DATABASE_URL` | Referenced in `database.py` but **not defined** in `Settings` — dead code |

### Key Config Files

| File | Purpose |
|---|---|
| `vercel.json` | Builds `frontend/`, outputs `frontend/.next` |
| `render.yaml` | Python 3.11, `pip install -r requirements.txt`, `uvicorn main:app --host 0.0.0.0 --port 10000`, health check at `/health` |
| `frontend/next.config.js` | Dev-only rewrite: `/api/*` → `http://localhost:8000/api/*`. Production has **no rewrite** — pages hardcode the Render URL directly |
| `.cursorrules` | Architecture conventions: JSON-first storage, port 8000/3000, UI styling direction |

---

## Backend: Data Flow

### Research Pipeline (`POST /api/research`)

```
User query string
    │
    ▼
parse_user_query()          ← extracts company + optional focus/omissions/sections
    │
    ▼
resolve_company_to_ticker() ← map lookup → ticker pattern → OpenAI fallback
    │
    ▼
orchestrate_research()
    │
    ├─ run_master_agent()
    │       ├─ tools.execute_tool("company_info")   → yfinance
    │       ├─ tools.execute_tool("financials")     → yfinance
    │       ├─ tools.execute_tool("risk")           → yfinance + heuristics
    │       ├─ tools.execute_tool("news")           → Yahoo Finance scrape
    │       ├─ tools.execute_tool("other")          ← optional custom section
    │       ├─ get_portfolio_context()              ← reads portfolio.json
    │       ├─ generate_analysis()                  ← single large GPT call
    │       └─ generate_news_reflections()          ← GPT: top headline takes
    │
    ├─ persist to file_storage (query, report metadata, report_data)
    └─ generate_report() via ReportLab → PDF written to output/reports/
         └─ returns /reports/<filename>.pdf (served as StaticFiles)
```

### Feedback Pipeline (`POST /api/feedback`)

Loads prior `report_data` from `file_storage`, re-runs `run_master_agent` with the same data plus user feedback as an additional prompt context, generates a new PDF, and saves as a new version.

### Portfolio (`/api/portfolio/*`)

CRUD over `portfolio.json`. The `/summary` endpoint enriches each holding with a live `yfinance` price fetch to compute current value, weight, and sector.

---

## Backend: API Reference

### Global

| Method | Path | Description |
|---|---|---|
| GET | `/` | Heartbeat |
| GET | `/health` | Render health check |
| — | `/reports/*` | Static PDF file serving |

### Research (`/api/research`)

| Method | Path | Description |
|---|---|---|
| POST | `/api/research` | Full pipeline → PDF + persisted report |
| GET | `/api/research/stream/{query}` | SSE progress stream (parse, resolve, partial data steps) |
| GET | `/api/research/preview/{query}` | Company info + 1y price history, no full report |
| GET | `/api/research/status/{report_id}` | Report status — **type mismatch**: param typed `int`, IDs are UUID strings |

### Papers (`/api/papers`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/papers` | All reports grouped by company |
| GET | `/api/papers/{company}` | Reports for a company (substring match) |
| GET | `/api/papers/report/{report_id}` | Single report + embedded data |

### Feedback (`/api/feedback`)

| Method | Path | Description |
|---|---|---|
| POST | `/api/feedback` | Regenerate report from existing `report_id` + feedback text |

### Portfolio (`/api/portfolio`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/portfolio` | List all holdings |
| POST | `/api/portfolio` | Add holding (`ticker`, `shares`, `purchase_price`) |
| PUT | `/api/portfolio/{ticker}` | Update shares for a ticker |
| DELETE | `/api/portfolio/{ticker}` | Remove a ticker |
| GET | `/api/portfolio/summary` | Holdings enriched with live prices, values, weights |

---

## Database / Persistence

### Active: JSON File Storage (`file_storage.py`)

All runtime data lives in JSON files under `backend/data/` (or `/tmp/data` when `VERCEL`/Lambda env detected):

| File | Contents |
|---|---|
| `queries.json` | `{ id (UUID), request, company, created_at }` |
| `reports.json` | `{ id (UUID), query_id, company, report_path, version, created_at }` |
| `report_data.json` | Raw agent payloads keyed by report ID |
| `portfolio.json` | Holding records `{ ticker, shares, purchase_price, added_at }` |

### Inactive: SQLAlchemy ORM (`models.py`, `database.py`, `crud.py`)

Full ORM layer exists but is **never imported or initialized** in `main.py`. `database.py` references `settings.database_url` which is not defined in `Settings`. The ORM models mirror the JSON schema:

- `Query` (1-to-many) → `Report` (1-to-1) → `ReportData`

---

## Frontend: Pages

### `research/page.tsx` — Core UI
- Text input for query
- Sends `POST /api/research`, polls result
- Renders a **canvas-drawn price chart** for 1-year history
- Displays report sections inline + links to PDF download
- Feedback input triggers `POST /api/feedback`

### `portfolio/page.tsx`
- Table of holdings (ticker, shares, purchase price, current value, weight, sector)
- Add/edit/delete holdings via portfolio API
- Calls `/api/portfolio/summary` for enriched data

### `papers/page.tsx`
- Lists all past reports grouped by company
- Links to per-company page

### `papers/[company]/page.tsx`
- Shows version history of reports for a company
- Links to view/download each version

### `about/page.tsx`
- Static product description + risk disclaimer

---

## Frontend: Key Observations

### `lib/api.ts`
- Axios client pointing at the Render URL
- Defines endpoints like `/papers/companies` and `/papers/download/:id` that **do not exist** on the backend
- `report_id` typed as `number`; backend uses UUID strings

### Orphan Components
These components exist in `components/` but are **not imported anywhere** in the pages:

| Component | Issue |
|---|---|
| `ResearchForm.tsx` | Not used; duplicate of logic in `research/page.tsx` |
| `ReportCard.tsx` | References `/api/papers/download/*` which doesn't exist |
| `FeedbackForm.tsx` | Mismatched field IDs vs backend `FeedbackRequest` schema |

---

## Agents & LLM Layer

### `orchestrator.py`
Entry point for research. Calls `parse_user_query` → `resolve_company_to_ticker` → `run_master_agent`. Wraps errors into `ResearchResponse`.

### `master_agent.py`
Core logic controller:
1. Dispatches tool calls (company info, financials, risk, news, optional custom)
2. Loads portfolio context from `portfolio.json`
3. Calls `generate_analysis()` — a single large GPT prompt that produces all narrative sections
4. Calls `generate_news_reflections()` — GPT produces short takes on top headlines
5. Detects custom section topics via `detect_custom_section_topic()` — has a bug where an unmatched long string returns a `list` instead of a `str`

### `tools.py`
Executes the four standard data-gathering tools by calling the `data/` fetchers, formats their output for the LLM prompt.

### `prompts.py`
Prompt templates for the master analysis call and news reflection call.

### Legacy Agents (not in live path)
`company_agent.py`, `financial_agent.py`, `news_agent.py`, `risk_agent.py` — individual analyzers that predate the `master_agent` consolidation. Not called by any router. Retained dead code.

---

## PDF Generation (`reports/generator.py`)

Uses **ReportLab** to produce a styled PDF with:
- Cover page (company name, ticker, date, logo placeholder)
- Table of contents
- Per-section narrative text
- Financial summary table (P/E, market cap, revenue, etc.)
- News headlines section
- Risk summary
- Portfolio fit section (if portfolio context exists)
- Disclaimer footer

Files are written to `backend/output/reports/` and served as static files at `/reports/<filename>`.

---

## Known Bugs and Inconsistencies

| # | Location | Issue |
|---|---|---|
| 1 | `research_router.py` | `get_research_status` path param typed as `int`; all IDs are UUID strings |
| 2 | `master_agent.py` | `detect_custom_section_topic`: long unmatched text returns `list` not `str` |
| 3 | `lib/api.ts` | Routes `/papers/companies`, `/papers/download/:id` do not exist on backend |
| 4 | `lib/api.ts` | `report_id` typed `number`; backend uses UUID `str` |
| 5 | `database.py` | References `settings.database_url`; not in `Settings` class |
| 6 | `main.py` | SQLAlchemy `init_db()` never called; ORM layer entirely dead |
| 7 | `FeedbackForm.tsx` | Field names don't match `FeedbackRequest` schema |
| 8 | `ReportCard.tsx` | Calls `/api/papers/download/{id}` — endpoint doesn't exist |
| 9 | `main.py` | `allow_origins=["*"]` + `allow_credentials=True` — browsers reject credentialed wildcard CORS |
| 10 | `backend/backend/data/` | Nested duplicate data directory; runtime path is `backend/data/` |
| 11 | `research_router.py` | `omit_sections` / `add_sections` parsed in validation but **not passed** through `orchestrate_research` to the master agent |
| 12 | `papers_router.py` | Company lookup uses substring match; frontend passes just a ticker, backend stores `"Name (TICKER)"` strings — match is fragile |

---

## Infrastructure

| Concern | Detail |
|---|---|
| **Frontend hosting** | Vercel (auto-deployed from `frontend/` via `vercel.json`) |
| **Backend hosting** | Render (primary), Railway config also present |
| **PDF storage** | Local disk on Render (`output/reports/`) — ephemeral, lost on redeploy |
| **Data storage** | Local JSON files on Render — same ephemeral problem |
| **API secrets** | `OPENAI_API_KEY` in Render environment |
| **Dev workflow** | `npm run dev` at repo root runs `concurrently` for both Next.js and uvicorn |
