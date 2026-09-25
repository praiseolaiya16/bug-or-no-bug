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
  `LINE_TOLERANCE` = 2 lines; also `score_by_source` and `mcnemar_test`,
  see "Statistical rigor" below)
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
│   │   ├── seeded_bugs/          # 30 .py samples (20 synthetic + 10 real-world), one seeded bug each
│   │   ├── ground_truth.json     # labels for seeded_bugs/ (see schema below)
│   │   └── results_cache.json    # generated, gitignored (see Caching below)
│   ├── scoring/
│   │   └── metrics.py            # match_findings / precision_recall_f1 / score_by_bug_type / score_by_source / mcnemar_test
│   └── tests/
│       └── test_metrics.py       # real coverage: matching, precision/recall, McNemar known-answer checks
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
│       │   ├── SampleList.jsx         # master list: filename + category tag + "real" tag + caught/missed badges
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
  "description": "string — human-readable explanation of the bug",
  "source": "string — 'synthetic' (hand-written for this project) or 'real_world' (adapted from a real CVE/issue/commit)",
  "citation": "string|null — source citation for real_world entries (CVE id, GitHub issue, etc.); null for synthetic"
}
```

Citation sourcing note (for grading/audit purposes): the 10 `real_world`
entries vary in citation strength — 4 security bugs are exact, verifiable
CVEs (CVE-2007-4559, CVE-2017-18342, CVE-2019-9947, CVE-2014-3730), one
style bug (`real_agent_memory`) is adapted from verbatim real code pulled
from a live GitHub issue (agentuniverse-ai/agentUniverse #1184), and the
remaining 5 (3 logic bugs + 2 style bugs) are real, well-documented *bug
classes* (e.g. a specific merged PR, or a widely-recognized anti-pattern
like Bandit's B101/assert-for-security rule) rather than one single
traceable commit. Every entry's `citation` field says explicitly which kind
it is — none are fabricated, but don't overstate the weaker ones as
"exact commits" if this comes up with a professor.

`_comment` and `_schema_example` keys at the top level are documentation
only (not consumed by scoring code).

## API

- `GET /api/health` — liveness check.
- `GET /api/dataset` — every sample's code + ground-truth label.
- `POST /api/analyze {"id": "<sample id>", "refresh": false}` — runs both
  pipelines on one file. Cached by default (see below); `refresh: true`
  forces a live re-run for just this file.
- `GET /api/results` — runs both pipelines across all 30 files and returns:
  - `overall` / `by_bug_type` — precision/recall/F1, overall and per category.
  - `by_source` — same, split `synthetic` vs. `real_world` (see Statistical
    rigor below).
  - `significance` / `significance_by_source` — McNemar's exact test on
    paired caught/missed outcomes, overall and per source.
  - `per_sample` — one row per file (`static_caught`, `llm_caught`,
    `static_fp_count`, `llm_fp_count`, `source`, etc.) — this is what the
    dashboard hydrates from.
  - `llm_available` — see below.

  Cached by default; `?refresh=true` forces a full live re-run of all 30
  files. A pipeline error on a file (missing API key, tool crash, rate
  limit) is reported per-file rather than failing the whole request; if
  every file's LLM call fails, `llm_available: false` and LLM metrics are
  `null` instead of a misleading 0%.

**Caching** (`analyze_bug()` in `app.py`, backed by
`backend/dataset/results_cache.json`, gitignored): static and LLM results
are cached **independently per file**, and only on success — an error is
never persisted as if it were a real finding, so a file that failed (e.g.
hit Gemini's rate limit) is retried live on the next request instead of
replaying a stale failure forever. This exists because the Gemini free
tier caps at **20 requests/day** on some models, and this dataset is now 30
files — an uncached `/api/results` would exhaust a day's quota on well
under one page load. Static analysis is cached too (cheaper reason: no need
to re-shell out to Bandit/Pylint on every load).

## Statistical rigor: significance testing + real-world generalization

Two things were added specifically to stress-test whether the static-vs-LLM
gap is a real finding or an artifact of a small, hand-built dataset:

- **`mcnemar_test()`** (`scoring/metrics.py`) — an exact two-sided binomial
  test on paired per-sample outcomes (not the chi-square approximation,
  which is unreliable at n=20-30). Exposed as `significance` /
  `significance_by_source` in `/api/results`, and shown live in the
  dashboard's summary bar. **Live result: p ≈ 0.27 overall — not
  significant.** Despite the LLM's better raw precision/recall, the
  observed gap (13 discordant samples, 9-4 favoring the LLM) isn't strong
  enough evidence at this sample size to rule out chance. This is a real,
  reportable limitation, not a bug — say so plainly in any write-up rather
  than only reporting the raw percentages.
- **`dataset/seeded_bugs/` real-world extension** — 10 of the 30 samples are
  adapted from real CVEs/GitHub issues rather than hand-written (see the
  `ground_truth.json` schema section above for exactly which ones and how
  strong each citation is). `score_by_source()` reports precision/recall
  split `synthetic` vs. `real_world`. **Live result: they're remarkably
  consistent** — synthetic (static 32%P/60%R, LLM 84%P/80%R) vs. real_world
  (static 37%P/70%R, LLM 80%P/80%R). The core finding holds up outside of
  hand-constructed examples, which is exactly what this check was for.
  (The real_world subset's own McNemar test is underpowered at n=10 — only
  3 discordant samples, p=1.0 — so don't read anything into that p-value
  alone; the point of this check is the consistency of the precision/recall
  numbers, not a second significance claim.)

## Current status — functional, end-to-end verified, real LLM data in hand

- Dataset complete: **30 seeded samples** — 20 synthetic (10 logic / 5
  security / 5 style) + 10 real-world (4 security / 3 logic / 3 style,
  adapted from real CVEs/issues — see schema section above), each with
  exactly one uncommented bug and a matching `ground_truth.json` entry
  (verified 1:1, no orphans either direction), all passing
  `python3 -m py_compile`.
- Both pipelines and scoring are implemented (no longer stubs) and verified
  against a **real** `GEMINI_API_KEY`, across the full 30-sample dataset.
  Current live numbers: static analysis 63% recall / 34% precision overall;
  LLM review 80% recall / 83% precision overall. See "Statistical rigor"
  above for the significance-testing and synthetic-vs-real-world results —
  don't just quote the raw percentages without those caveats.
- `backend/tests/test_metrics.py` covers `match_findings`,
  `precision_recall_f1`, and `mcnemar_test` (including two hand-computed
  known-answer checks on the binomial math) — 10 tests, all passing.
- Frontend is a master-detail code browser (see below), verified rendering
  in a headless browser (Playwright, ad hoc — not part of the repo) in
  light/dark/mobile with zero console errors, including the real per-file
  Gemini findings shown alongside the highlighted bug line. It also shows a
  neutral "real" tag + citation for real_world samples, and the McNemar
  p-value in the summary bar.
- The Python 3.9-only limitation noted previously is resolved — Homebrew
  Python 3.11 is now installed and `backend/venv` was rebuilt on it.

### Gemini model: expect frequent retirement, don't hardcode confidence in a name

Model names churn fast on this API — three different models were tried and
retired *within this project's lifetime*: `gemini-2.0-flash` (the original
default) was retired first ("no longer available", pointed to 3.6-flash);
`gemini-3.6-flash` worked but its free tier is only **20 requests/day**,
which the dataset (20 files at the time) burned in a single `/api/results`
call (this is
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

Done since the last pass: tests for `scoring/metrics.py`, McNemar's
significance test, and the 10-sample real-world dataset extension (all
described above). Remaining:

- Consider a scheduled or manual "refresh all" flow now that results are
  cached — `?refresh=true` on `/api/results` exists but isn't wired to any
  UI button (only the per-file "↻ re-analyze" in `SampleDetail.jsx` is),
  since a full refresh can burn the whole daily LLM quota in one click.
- The real-world dataset could grow past 10, and/or the weaker citations
  (see the schema section's sourcing note) could be upgraded to exact
  commits if a professor pushes on rigor.
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
