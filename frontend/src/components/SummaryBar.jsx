import BugTypeChart from "./BugTypeChart.jsx";

function formatPercent(value) {
  return value === null || value === undefined ? "–" : `${Math.round(value * 100)}`;
}

/**
 * McNemar's exact test result on the paired per-sample outcomes: whether
 * the static-vs-LLM gap is likely real or could be noise at n=20.
 *
 * @param {{ significance: object|null }} props
 */
function SignificanceNote({ significance }) {
  if (!significance) return null;

  const { p_value: pValue, n_discordant: nDiscordant } = significance;
  const isSignificant = significance["significant_at_0.05"];

  return (
    <span
      className={`significance-note ${isSignificant ? "significance-note-significant" : "significance-note-not"}`}
      title={`McNemar's exact test on ${nDiscordant} discordant samples (where the two tools disagreed)`}
    >
      McNemar p={pValue.toFixed(3)} · {isSignificant ? "significant" : "not significant at n=20"}
    </span>
  );
}

/**
 * Slim, secondary summary strip: overall precision/recall for each tool as
 * compact terminal-style stats, plus the recall-by-category chart shrunk
 * down to a supporting role. This sits above the sample browser (the main
 * event) rather than dominating the page.
 *
 * @param {{ overall: object, byBugType: object, llmAvailable: boolean, significance: object|null }} props
 */
function SummaryBar({ overall, byBugType, llmAvailable, significance }) {
  return (
    <div className="summary-bar">
      <div className="summary-stats">
        <div className="summary-stat-group">
          <span className="summary-stat-label">static</span>
          <span className="summary-stat-value">
            {formatPercent(overall.static.precision)}
            <span className="summary-stat-unit">P</span>
          </span>
          <span className="summary-stat-value">
            {formatPercent(overall.static.recall)}
            <span className="summary-stat-unit">R</span>
          </span>
        </div>
        <div className="summary-stat-group">
          <span className="summary-stat-label">llm</span>
          {llmAvailable ? (
            <>
              <span className="summary-stat-value">
                {formatPercent(overall.llm?.precision)}
                <span className="summary-stat-unit">P</span>
              </span>
              <span className="summary-stat-value">
                {formatPercent(overall.llm?.recall)}
                <span className="summary-stat-unit">R</span>
              </span>
            </>
          ) : (
            <span className="summary-stat-unavailable">unavailable — set GEMINI_API_KEY</span>
          )}
        </div>
        <SignificanceNote significance={significance} />
      </div>
      <BugTypeChart byBugType={byBugType} compact />
    </div>
  );
}

export default SummaryBar;
