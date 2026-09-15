"""
Flask application entrypoint for Bug-or-No-Bug.

Exposes an API that:
  - Serves the seeded bug dataset to the frontend.
  - Runs a single sample or the whole dataset through static analysis
    (analyzers/static_analysis.py) and LLM review (analyzers/llm_review.py).
  - Scores both approaches against dataset/ground_truth.json using
    scoring/metrics.py.
  - Returns a comparison payload for the frontend dashboard to render.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from analyzers.llm_review import review_code
from analyzers.static_analysis import run_static_analysis
from scoring.metrics import precision_recall_f1, score_by_bug_type

load_dotenv()

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset" / "seeded_bugs"
GROUND_TRUTH_PATH = BASE_DIR / "dataset" / "ground_truth.json"
CACHE_PATH = BASE_DIR / "dataset" / "results_cache.json"


def load_ground_truth():
    """Load the seeded-bug labels from dataset/ground_truth.json."""
    with open(GROUND_TRUTH_PATH) as f:
        return json.load(f)["bugs"]


def find_bug(bugs, sample_id):
    """Return the ground-truth entry with the given id, or None."""
    return next((bug for bug in bugs if bug["id"] == sample_id), None)


def load_cache():
    """Load the on-disk analysis cache, keyed by sample id."""
    if not CACHE_PATH.exists():
        return {}
    try:
        with open(CACHE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_cache(cache):
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def analyze_bug(bug, cache, force_refresh=False):
    """Run both pipelines against one seeded_bugs/ file, using the on-disk
    cache so repeat requests don't re-spend Gemini quota (the free tier
    caps at 20 requests/day, and this dataset alone is 20 files).

    Only *successful* results are cached — an error (missing API key, a
    429 from a quota limit, a crashed tool) is never persisted as if it
    were a real finding, so the next request retries it live instead of
    replaying a stale failure forever. Pass force_refresh=True to bypass
    the cache and re-run both pipelines regardless.

    Returns (static_findings, static_error, llm_findings, llm_error).
    """
    entry = cache.get(bug["id"], {})
    file_path = DATASET_DIR / bug["file"]
    changed = False

    if force_refresh or entry.get("static_error") or "static_findings" not in entry:
        try:
            static_findings = run_static_analysis(str(file_path))
            for finding in static_findings:
                finding["file"] = bug["file"]
            entry["static_findings"], entry["static_error"] = static_findings, None
        except Exception as exc:  # noqa: BLE001 - surfaced to the client, not swallowed
            entry["static_findings"], entry["static_error"] = [], str(exc)
        changed = True

    if force_refresh or entry.get("llm_error") or "llm_findings" not in entry:
        try:
            code = file_path.read_text()
            llm_findings = review_code(code, context=bug["file"])
            for finding in llm_findings:
                finding["file"] = bug["file"]
            entry["llm_findings"], entry["llm_error"] = llm_findings, None
        except Exception as exc:  # noqa: BLE001
            entry["llm_findings"], entry["llm_error"] = [], str(exc)
        changed = True

    if changed:
        entry["cached_at"] = datetime.now(timezone.utc).isoformat()
        cache[bug["id"]] = entry
        save_cache(cache)

    return entry["static_findings"], entry["static_error"], entry["llm_findings"], entry["llm_error"]


@app.route("/api/health", methods=["GET"])
def health():
    """Basic liveness check."""
    return jsonify({"status": "ok"})


@app.route("/api/dataset", methods=["GET"])
def get_dataset():
    """Return every seeded sample: its code and its ground-truth label."""
    bugs = load_ground_truth()
    samples = []
    for bug in bugs:
        file_path = DATASET_DIR / bug["file"]
        samples.append(
            {
                "id": bug["id"],
                "file": bug["file"],
                "bug_type": bug["bug_type"],
                "code": file_path.read_text() if file_path.exists() else "",
                "ground_truth": {
                    "is_bug": bug["is_bug"],
                    "line": bug["line"],
                    "description": bug["description"],
                },
            }
        )
    return jsonify(samples)


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Run both pipelines against a single sample, by id.

    Cached by default (see analyze_bug). Pass {"refresh": true} in the
    body to force a live re-run for this one file — cheap (one Bandit +
    Pylint pass, one Gemini call) compared to refreshing the whole dataset.
    """
    payload = request.get_json(silent=True) or {}
    sample_id = payload.get("id")
    if not sample_id:
        return jsonify({"error": "id is required"}), 400

    bug = find_bug(load_ground_truth(), sample_id)
    if bug is None:
        return jsonify({"error": f"unknown sample id: {sample_id}"}), 404

    force_refresh = bool(payload.get("refresh"))
    cache = load_cache()
    static_findings, static_error, llm_findings, llm_error = analyze_bug(
        bug, cache, force_refresh=force_refresh
    )
    return jsonify(
        {
            "id": bug["id"],
            "file": bug["file"],
            "static_findings": static_findings,
            "static_error": static_error,
            "llm_findings": llm_findings,
            "llm_error": llm_error,
        }
    )


@app.route("/api/results", methods=["GET"])
def results():
    """Run both pipelines across the whole dataset and score them.

    This is the endpoint the dashboard hydrates from. Results are cached
    on disk per file (see analyze_bug) — the first call runs everything
    live, later calls reuse cached findings, and only files that
    previously errored (e.g. hit a quota limit) are retried. Pass
    ?refresh=true to force a full live re-run of all 20 files, which
    re-spends the LLM's full quota — use sparingly.
    """
    bugs = load_ground_truth()
    force_refresh = request.args.get("refresh") == "true"
    cache = load_cache()

    all_static_findings = []
    all_llm_findings = []
    per_sample = []
    llm_error_count = 0

    for bug in bugs:
        static_findings, static_error, llm_findings, llm_error = analyze_bug(
            bug, cache, force_refresh=force_refresh
        )
        all_static_findings.extend(static_findings)
        all_llm_findings.extend(llm_findings)
        if llm_error:
            llm_error_count += 1

        per_sample.append(
            {
                "id": bug["id"],
                "file": bug["file"],
                "bug_type": bug["bug_type"],
                "line": bug["line"],
                "description": bug["description"],
                "static_caught": any(
                    f.get("line") is not None and abs(f["line"] - bug["line"]) <= 2
                    for f in static_findings
                ),
                "static_finding_count": len(static_findings),
                "static_error": static_error,
                "llm_caught": any(
                    f.get("line") is not None and abs(f["line"] - bug["line"]) <= 2
                    for f in llm_findings
                ),
                "llm_finding_count": len(llm_findings),
                "llm_error": llm_error,
            }
        )

    # If every single file failed LLM review (e.g. no GEMINI_API_KEY set),
    # report LLM scoring as unavailable rather than as a 0% score.
    llm_available = llm_error_count < len(bugs)

    return jsonify(
        {
            "overall": {
                "static": precision_recall_f1(all_static_findings, bugs),
                "llm": precision_recall_f1(all_llm_findings, bugs) if llm_available else None,
            },
            "by_bug_type": {
                "static": score_by_bug_type(all_static_findings, bugs),
                "llm": score_by_bug_type(all_llm_findings, bugs) if llm_available else None,
            },
            "per_sample": per_sample,
            "llm_available": llm_available,
        }
    )


if __name__ == "__main__":
    # Default 5001, not 5000 - macOS AirPlay Receiver listens on 5000 by default.
    port = int(os.environ.get("PORT", 5001))
    app.run(port=port, debug=True)
