# Budgy 2.0

A personal finance dashboard for tracking spending, managing budgets, and understanding where your money goes.

---

## Purpose

Most personal finance tools are either too simple (spreadsheets) or too invasive (connecting directly to bank accounts). Budgy 2.0 sits in the middle: you import your own CSV exports from your bank, and the app gives you a full picture — spending by category, budget tracking, month-over-month trends, and an AI-generated monthly summary.

The goal is a tool that respects your data while giving you the analytical depth of a commercial product.

---

## Demo

You can explore the app without uploading any data. Use the **Demo Mode** toggle in the bottom-left sidebar to load a full set of sample transactions, categories, and budgets across all pages. Toggle it off at any time to return to real data.

---

## AI Features

> This is an active area of development.

**Currently implemented:**

- **Automatic transaction categorization** — classify imported transactions using a fine-tuned or few-shot model, reducing manual review. End-to-end AI integration tests on the backend for the CSV upload pipeline. Runs real Claude API calls against 8 fixture CSVs and scores each stage to refine prompting / tooling.
- **AI monthly summary** — the dashboard generates a natural-language summary of your month's spending, income, and notable patterns via an LLM call

**Planned:**

- **Anomaly detection** — flag unusual transactions or spending spikes relative to your history
- **Natural language budget queries** — ask questions like "how much did I spend on food last quarter?" and get direct answers

The data model and API architecture are designed to support these features. Summaries, analytics series, and category hierarchies are all pre-computed and exposed as structured endpoints that feed directly into AI context windows.

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Backend | Python · FastAPI · SQLAlchemy · Pandas · Pydantic |
| Frontend | React · TypeScript · Vite |
| State | Zustand · TanStack React Query |
| UI | shadcn/ui · Tailwind CSS · Recharts |
| Data | SQLite (local) · CSV import pipeline |

### python-toolkit

- This porject utilizes 2 custom python packages pleasant_loggers and pleasant_database.
- Both are created and maintained by myself and released publicly on pypi.org.
- Both can be found at [https://github.com/EliasRodkey/python-toolkit](https://github.com/EliasRodkey/python-toolkit)

---

## Architecture

```
budgy_2.0/
├── backend/           # FastAPI application
│   ├── api/           # Route handlers (transactions, categories, summaries, analytics, budgets)
│   ├── database_modules/  # SQLAlchemy models and query managers
│   └── csv_modules/   # CSV ingestion and normalization pipeline
│
└── frontend/          # React + Vite SPA
    └── src/
        ├── api/       # Typed fetch wrappers (one file per backend domain)
        ├── components/ # UI components (dashboard, transactions, categories, layout)
        ├── hooks/     # React Query hooks
        ├── pages/     # Route-level page components
        └── store/     # Zustand stores (sidebar, date range, demo mode)
```

The frontend talks to the backend through a thin proxy at `/api`, keeping CORS simple. React Query manages all server state — cache invalidation happens on any mutation, so the UI stays consistent without manual refresh.

---

## Challenges

### CSV ingestion and normalization

Bank CSV exports are not standardized. Budgy's import pipeline handles varying column names, date formats, and encodings. Tags can arrive as comma-delimited strings or Python-style lists, so the normalizer unwraps both forms consistently. Deduplication is handled at the database layer using a composite key on date, amount, and description.

### Category and budget data model

The category hierarchy has two levels (primary → detailed) with 16 primary categories spanning both spending and non-spending types (income, transfers, investments). Budgets are versioned: a `budget_assignment` table maps time periods to budget definitions, so the system can reconstruct what limits were active in any historical month — which matters for analytics and AI context.

### Full-stack integration

Wiring a FastAPI backend to a React frontend across live data mutations required careful React Query cache design. Every mutation — editing a transaction, uploading a CSV, bulk-categorizing — invalidates exactly the right queries without over-fetching. The summary recompute pipeline runs server-side and the frontend polls for completion before re-rendering.

### Designing for AI

Adding an AI summary card meant building an endpoint that assembles structured financial context into a prompt — not just a number, but a narrative-ready data payload. Deciding what information to include, how to constrain token usage, and how to surface the result in the UI without blocking the rest of the dashboard were real design problems. This groundwork shapes how future AI features will be integrated.

---

## Getting Started

**Prerequisites:** Python 3.11+, Node 18+

### Environment setup

Budgy's AI features (CSV analysis, monthly summary) require an Anthropic API key.

1. Copy `.env.example` to `.env` at the repo root:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and set your key:

   ```dotenv
   ANTHROPIC_API_KEY=sk-ant-...
   ```

   Get a key at [console.anthropic.com](https://console.anthropic.com). The `.env` file is gitignored and will never be committed.

> The app runs without a key — demo mode and all non-AI features work fine — but CSV import and AI summaries will show an error until the key is set.

### Backend

```bash
# From the repo root
pip install -e .

uvicorn backend.main:app --reload
# API available at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

The frontend proxies `/api` requests to `localhost:8000` via Vite's dev server config.

---

## AI-Assisted Development

This project was built with significant help from [Claude Code](https://claude.ai/code), Anthropic's AI coding assistant.

**Division of labor:**

- **Backend** (FastAPI routes, SQLAlchemy models, CSV pipeline, query logic) — written primarily by myself
- **Frontend** (React components, hooks, state management, UI layout) — built primarily by Claude Code under my direction and review

This reflects a deliberate experiment in AI-assisted engineering: using an AI system as a capable frontend collaborator while retaining ownership of the data model, business logic, and architectural decisions. The result is a full-stack application produced faster than either party could alone, with the human focusing on what is hardest to delegate — domain knowledge, system design, and correctness at the data layer.

---

## License

All Rights Reserved — Elias Rodkey
