import CodeBlock from "./CodeBlock.jsx";

function FindingsGroup({ title, toolClass, findings, error, loading }) {
  return (
    <div className="findings-group">
      <h3 className={`findings-title ${toolClass}`}>{title}</h3>
      <div key={loading ? "loading" : "loaded"} className="panel-transition">
        {loading && <p className="findings-empty">loading…</p>}
        {!loading && error && <p className="findings-empty findings-error">{error}</p>}
        {!loading && !error && findings.length === 0 && <p className="findings-empty">no findings</p>}
        {!loading && !error && findings.length > 0 && (
          <ul className="findings-list">
            {findings.map((finding, index) => (
              <li key={index}>
                <span className="findings-line">L{finding.line ?? "?"}</span>
                {finding.message}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

/**
 * Detail view for the selected sample: the ground-truth bug description,
 * the actual source with the bug line marked, and what each tool found.
 * Findings are backend-cached; the re-analyze button forces a live re-run
 * for just this file (see analyzeSample's `refresh` option).
 *
 * The body (everything below the header) is keyed on the sample id so it
 * remounts - and replays the shared panel-transition fade - every time the
 * selection changes, instead of hard-cutting to new content.
 *
 * @param {{ sample: object|null, detail: object|null, loading: boolean, onRefresh?: (id: string) => void, refreshing?: boolean }} props
 */
function SampleDetail({ sample, detail, loading, onRefresh, refreshing }) {
  if (!sample) {
    return (
      <div className="sample-detail sample-detail-empty">
        <p className="status-message">Select a sample to inspect its code.</p>
      </div>
    );
  }

  const staticFindings = detail?.static_findings ?? [];
  const llmFindings = detail?.llm_findings ?? [];
  const staticLines = new Set(staticFindings.map((f) => f.line).filter((line) => line != null));
  const llmLines = new Set(llmFindings.map((f) => f.line).filter((line) => line != null));
  const busy = loading || refreshing;

  return (
    <div className="sample-detail">
      <div className="sample-detail-header">
        <code className="sample-detail-file">{sample.file}</code>
        <span className={`chip category-tag-${sample.bug_type}`}>{sample.bug_type}</span>
        {onRefresh && (
          <button
            type="button"
            className="refresh-button"
            onClick={() => onRefresh(sample.id)}
            disabled={busy}
            title="Re-run both pipelines for this file, bypassing the cache"
          >
            {refreshing ? "re-analyzing…" : "↻ re-analyze"}
          </button>
        )}
      </div>

      <div key={sample.id} className="sample-detail-content panel-transition">
        <p className="bug-description">
          <span className="bug-description-line">line {sample.line}</span>
          {sample.description}
        </p>

        {sample.source === "real_world" && sample.citation && (
          <p className="citation-note">↳ {sample.citation}</p>
        )}

        <CodeBlock code={sample.code} bugLine={sample.line} staticLines={staticLines} llmLines={llmLines} />

        <div className="findings-columns">
          <FindingsGroup
            title="⚙ static analysis"
            toolClass="findings-title-static"
            findings={staticFindings}
            error={detail?.static_error ?? sample.static_error}
            loading={busy}
          />
          <FindingsGroup
            title="✦ llm review"
            toolClass="findings-title-llm"
            findings={llmFindings}
            error={detail?.llm_error ?? sample.llm_error}
            loading={busy}
          />
        </div>
      </div>
    </div>
  );
}

export default SampleDetail;
