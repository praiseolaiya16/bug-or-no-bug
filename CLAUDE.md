# Bug or No Bug

Senior seminar research project (Praise Olaiya). Compares traditional static
analysis tools (Bandit, Pylint) against an LLM-based code reviewer (Gemini
API) on their ability to detect seeded bugs in Python code, across three
categories: logic errors, security vulnerabilities, and general
style/coding-convention issues. The research question is whether the two
approaches differ in precision/recall across these categories — the project
produces a scored, side-by-side comparison, not just a working tool.

## Tech stack

- Backend: Python 3.11, Flask (`backend/app.py`), runs on **port 5001** (not
  5000 — macOS AirPlay Receiver squats on 5000 on many machines)
- Static analysis: Bandit + Pylint, wrapped in `backend/analyzers/static_analysis.py`
  (shells out to each CLI with JSON output, per file)
- LLM review: Google Gemini API via the **`google-genai`** SDK (the older
  `google-generativeai` package is fully deprecated — don't reintroduce it),
  wrapped in `backend/analyzers/llm_review.py`
- Scoring: `backend/scoring/metrics.py` (precision/recall/F1, matches a
  finding to the seeded bug when they're on the same file within
  `LINE_TOLERANCE` = 2 lines)
- Frontend: Vite + React (`frontend/src`), dev server on port 5173, proxies
  `/api/*` to the Flask backend (see `vite.config.js`)

Note: early planning docs for this project (Assignments 1 & 2) describe the
backend as FastAPI. The implemented backend is Flask — treat the code as the
source of truth over those docs.

## File structure

```
bug-or-no-bug/
├── backend/
│   ├── app.py                    # Flask entrypoint: /api/health, /api/dataset, /api/analyze, /api/results
│   ├── requirements.txt
│   ├── venv/                     # local virtualenv, Python 3.11 (gitignored)
│   ├── analyzers/
│   │   ├── static_analysis.py    # Bandit + Pylint subprocess wrappers, implemented
│   │   └── llm_review.py         # Gemini (google-genai) client, implemented
│   ├── dataset/
│   │   ├── seeded_bugs/          # 20 hand-written .py samples, one seeded bug each
│   │   └── ground_truth.json     # labels for seeded_bugs/ (see schema below)
│   ├── scoring/
│   │   └── metrics.py            # match_findings / precision_recall_f1 / score_by_bug_type, implemented
│   └── tests/                    # still just the original placeholder test
├── frontend/
│   ├── package.json               # deps: react, recharts, prismjs (syntax highlighting)
│   ├── vite.config.js             # dev-server proxy: /api -> http://127.0.0.1:5001
│   ├── index.html
│   └── src/
│       ├── main.jsx / App.jsx
│       ├── index.css              # CSS vars (light/dark), code-editor-inspired palette, all component styles
│       ├── components/
│       │   ├── ResultsDashboard.jsx   # fetches /api/results + /api/dataset, owns selection state
│       │   ├── SummaryBar.jsx         # compact precision/recall + BugTypeChart, secondary to the browser below
│       │   ├── BugTypeChart.jsx       # recharts grouped bar: recall by category; `compact` prop for SummaryBar
│       │   ├── SampleList.jsx         # master list: 20 rows, filename + category tag + caught/missed badges
│       │   ├── SampleDetail.jsx       # detail pane: bug description, CodeBlock, findings by tool
│       │   └── CodeBlock.jsx          # Prism-highlighted source, bug line banded, gutter dots per tool
│       └── api/
│           └── client.js          # fetchDataset / analyzeSample / fetchResults (unchanged contract)
├── .env.example                   # GEMINI_API_KEY, optional GEMINI_MODEL / PORT
├── .gitignore
└── README.md
```

The frontend is a master-detail code browser, not a table: `SampleList` (left) selects a sample, `SampleDetail` (right) lazily calls `analyzeSample(id)` to show its actual findings (line + message) alongside the syntax-highlighted source with the seeded bug's line banded and per-tool gutter dots. `ComparisonTable.jsx` (the old flat table) was deleted when this replaced it — don't recreate it. Static analysis (`--series-static`, blue) and LLM (`--series-llm`, orange) use one fixed color pair everywhere — chart bars, gutter dots, badges, findings headers — per the dataviz skill's "color follows the entity" rule; category tags (logic/security/style) reuse other slots from the same validated 8-hue palette rather than inventing new hues. All interactive text colors were checked against WCAG 4.5:1 (see `--*-text` CSS variables — the plain series/status colors read fine as fills/marks but not as small text, hence the separate darker text variants).

## `ground_truth.json` schema

Top-level object with `bugs`: an array of entries, one per file in
`dataset/seeded_bugs/`:

```json
{
  "id": "string — unique id, matches the seeded_bugs/ filename stem",
  "file": "string — filename within seeded_bugs/ (not a full path)",
  "is_bug": "boolean — whether the sample actually contains a bug",
  "bug_type": "string — bug category: 'logic' | 'security' | 'style'",
  "line": "integer|null — 1-indexed line number of the bug",
  "description": "string — human-readable explanation of the bug"
}
```

`_comment` and `_schema_example` keys at the top level are documentation
only (not consumed by scoring code).

## API

- `GET /api/health` — liveness check.
- `GET /api/dataset` — every sample's code + ground-truth label.
- `POST /api/analyze {"id": "<sample id>", "refresh": false}` — runs both
  pipelines on one file. Cached by default (see below); `refresh: true`
  forces a live re-run for just this file.
- `GET /api/results` — runs both pipelines across all 20 files and returns
  overall + per-bug-type precision/recall/F1 plus a per-sample caught/missed
  table (this is what the dashboard hydrates from). Cached by default;
  `?refresh=true` forces a full live re-run of all 20 files. A pipeline
  error on a file (missing API key, tool crash, rate limit) is reported
  per-file rather than failing the whole request; if every file's LLM call
  fails, `llm_available: false` and LLM metrics are `null` instead of a
  misleading 0%.

**Caching** (`analyze_bug()` in `app.py`, backed by
`backend/dataset/results_cache.json`, gitignored): static and LLM results
are cached **independently per file**, and only on success — an error is
never persisted as if it were a real finding, so a file that failed (e.g.
hit Gemini's rate limit) is retried live on the next request instead of
replaying a stale failure forever. This exists because the Gemini free
tier caps at **20 requests/day**, and this dataset alone is 20 files — an
uncached `/api/results` would exhaust the entire daily quota on a single
page load. Static analysis is cached too (cheaper reason: no need to
re-shell out to Bandit/Pylint on every load).

## Current status — functional, end-to-end verified, real LLM data in hand

- Dataset complete: 20 seeded samples (10 logic / 5 security / 5 style), each
  with exactly one uncommented bug and a matching `ground_truth.json` entry
  (verified 1:1), all passing `python3 -m py_compile`.
- Both pipelines and scoring are implemented (no longer stubs) and verified
  against a **real** `GEMINI_API_KEY`. Live numbers as of this run: static
  analysis 60% recall / 32% precision overall (30% logic / 100% security /
  80% style); LLM review 55% recall / **100% precision** overall (50% logic /
  60% security / 60% style, zero false positives in every category). The
  pattern: static analysis is noisy-but-thorough, the LLM is precise-but-
  conservative — a real, substantive answer to the research question.
- Frontend is a master-detail code browser (see below), verified rendering
  in a headless browser (Playwright, ad hoc — not part of the repo) in
  light/dark/mobile with zero console errors, including the real per-file
  Gemini findings shown alongside the highlighted bug line.
- The Python 3.9-only limitation noted previously is resolved — Homebrew
  Python 3.11 is now installed and `backend/venv` was rebuilt on it.

### Gemini model: expect frequent retirement, don't hardcode confidence in a name

Model names churn fast on this API — three different models were tried and
retired *within this project's lifetime*: `gemini-2.0-flash` (the original
default) was retired first ("no longer available", pointed to 3.6-flash);
`gemini-3.6-flash` worked but its free tier is only **20 requests/day**,
which this 20-file dataset burns in a single `/api/results` call (this is
why the caching layer above exists — it was built in direct response to
exhausting a day's quota through normal testing); `gemini-2.5-flash` and
`gemini-1.5-flash` are *also* both fully retired ("no longer available to
new users" / "not found"). The current default, **`gemini-3.5-flash-lite`**,
was chosen because Lite-tier models carry a meaningfully higher free-tier
daily quota than full Flash models, and it's what Google's own 404 messages
point to as the current replacement. If this breaks again: run
`client.models.list()` (see `analyzers/llm_review.py`'s `get_client()`) to
see what's actually being served to this API key before picking a
replacement — don't guess from training-data knowledge of model names, they
go stale fast.

## Next steps

- Add real tests in `backend/tests/` for `scoring/metrics.py` at least —
  it's the piece the whole comparison's validity rests on.
- Consider a scheduled or manual "refresh all" flow now that results are
  cached — `?refresh=true` on `/api/results` exists but isn't wired to any
  UI button (only the per-file "↻ re-analyze" in `SampleDetail.jsx` is),
  since a full refresh can burn the whole daily LLM quota in one click.
- Later (per Assignment 2): prompt-strategy comparison (zero-shot/few-shot/
  chain-of-thought), cost/token/time instrumentation per file, and an
  optional hybrid pipeline that feeds static-analysis output into the LLM
  prompt as context.

## Running it locally

```bash
# backend (port 5001)
cd backend && source venv/bin/activate && python app.py

# frontend (port 5173, proxies /api to the backend)
cd frontend && npm run dev
```

Open http://localhost:5173. Without a `GEMINI_API_KEY` in a project-root
`.env`, static analysis results show normally and the LLM columns show
"Unavailable."
