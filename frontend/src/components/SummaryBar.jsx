import BugTypeChart from "./BugTypeChart.jsx";

function formatPercent(value) {
  return value === null || value === undefined ? "–" : `${Math.round(value * 100)}`;
}

/**
 * Slim, secondary summary strip: overall precision/recall for each tool as
 * compact terminal-style stats, plus the recall-by-category chart shrunk
 * down to a supporting role. This sits above the sample browser (the main
 * event) rather than dominating the page.
 *
 * @param {{ overall: object, byBugType: object, llmAvailable: boolean }} props
 */
function SummaryBar({ overall, byBugType, llmAvailable }) {
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
      </div>
      <BugTypeChart byBugType={byBugType} compact />
    </div>
  );
}

export default SummaryBar;
