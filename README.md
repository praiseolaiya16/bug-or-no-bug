# Bug or No Bug

A benchmark comparing traditional static analysis (Bandit + Pylint) against
LLM-based code review (Gemini) at detecting seeded bugs in Python code, with
a dashboard for visualizing precision/recall/F1 results.

**Status: skeleton only.** No analysis, scoring, or API logic is implemented
yet — see the `TODO`s in each file.

## Structure

```
bug-or-no-bug/
├── backend/            # Flask API
│   ├── app.py          # App entrypoint / routes
│   ├── analyzers/      # static_analysis.py (Bandit/Pylint), llm_review.py (Gemini)
│   ├── dataset/        # seeded_bugs/ samples + ground_truth.json labels
│   ├── scoring/        # metrics.py (precision/recall/F1)
│   └── tests/
├── frontend/           # Vite + React dashboard
│   └── src/
│       ├── components/ # ResultsDashboard, BugTypeChart, ComparisonTable
│       └── api/        # client.js — backend API calls
├── .env.example
└── .gitignore
```

## Setup

### Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env  # then fill in GEMINI_API_KEY
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## TODO

- Implement `analyzers/static_analysis.py` (Bandit + Pylint wrappers).
- Implement `analyzers/llm_review.py` (Gemini API client + prompt design).
- Populate `dataset/seeded_bugs/` with sample code and `dataset/ground_truth.json` labels.
- Implement `scoring/metrics.py` (precision/recall/F1, per bug-type breakdown).
- Wire up `app.py` routes (`/api/analyze`, `/api/dataset`, `/api/results`).
- Implement `frontend/src/api/client.js` calls and connect dashboard components to real data.
