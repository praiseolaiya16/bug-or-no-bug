/**
 * API client for talking to the Bug-or-No-Bug Flask backend.
 *
 * Requests go to the relative "/api" path; in dev, vite.config.js proxies
 * that to the Flask server (see PORT in backend/app.py, default 5001).
 */
const BASE_URL = "/api";

async function parseJsonOrThrow(response, label) {
  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = body.error ? `: ${body.error}` : "";
    } catch {
      // response body wasn't JSON; ignore
    }
    throw new Error(`${label} failed (${response.status})${detail}`);
  }
  return response.json();
}

/**
 * Fetch the list of seeded bug samples available for analysis.
 * @returns {Promise<Array<object>>}
 */
export async function fetchDataset() {
  const response = await fetch(`${BASE_URL}/dataset`);
  return parseJsonOrThrow(response, "fetchDataset");
}

/**
 * Trigger analysis (static + LLM) for a given sample and fetch results.
 * Cached on the backend by default — pass `refresh: true` to force a live
 * re-run for this one file (e.g. to retry after a transient LLM error).
 * @param {string} sampleId
 * @param {{ refresh?: boolean }} [options]
 * @returns {Promise<object>}
 */
export async function analyzeSample(sampleId, { refresh = false } = {}) {
  const response = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: sampleId, refresh }),
  });
  return parseJsonOrThrow(response, "analyzeSample");
}

/**
 * Fetch aggregated scoring results (precision/recall/F1) for the dashboard.
 * Backend-cached per file after the first run, so repeat loads don't
 * re-spend the LLM's daily quota.
 * @returns {Promise<object>}
 */
export async function fetchResults() {
  const response = await fetch(`${BASE_URL}/results`);
  return parseJsonOrThrow(response, "fetchResults");
}

export { BASE_URL };
