const ICON = { caught: "✓", missed: "✗", unavailable: "–" };

function badgeState(sample, tool) {
  const error = tool === "static" ? sample.static_error : sample.llm_error;
  if (error) return "unavailable";
  const caught = tool === "static" ? sample.static_caught : sample.llm_caught;
  return caught ? "caught" : "missed";
}

function Badge({ tool, state }) {
  return (
    <span className={`chip badge badge-${state}`} title={`${tool}: ${state}`}>
      <span className="badge-icon" aria-hidden="true">
        {ICON[state]}
      </span>
      {tool}
    </span>
  );
}

/**
 * The 20-sample browser: filename, category, and two compact pass/fail
 * badges per row. Clicking a row selects it for SampleDetail.
 *
 * @param {{ samples: Array<object>, selectedId: string|null, onSelect: (id: string) => void }} props
 */
function SampleList({ samples, selectedId, onSelect }) {
  return (
    <nav className="sample-list" aria-label="Seeded bug samples">
      {samples.map((sample) => (
        <button
          key={sample.id}
          type="button"
          className={`sample-row${sample.id === selectedId ? " sample-row-selected" : ""}`}
          onClick={() => onSelect(sample.id)}
          aria-current={sample.id === selectedId}
        >
          <span className="sample-row-main">
            <code className="sample-file" title={sample.file}>
              {sample.file}
            </code>
            <span className={`chip category-tag-${sample.bug_type}`}>{sample.bug_type}</span>
          </span>
          <span className="sample-row-badges">
            <Badge tool="static" state={badgeState(sample, "static")} />
            <Badge tool="llm" state={badgeState(sample, "llm")} />
          </span>
        </button>
      ))}
    </nav>
  );
}

export default SampleList;
