function Bar({ width, height = 12, radius = "var(--radius-chip)", style }) {
  return <span className="skeleton" style={{ display: "inline-block", width, height, borderRadius: radius, ...style }} />;
}

function SkeletonRow() {
  return (
    <div className="sample-row" aria-hidden="true">
      <span className="sample-row-main">
        <Bar width={112} height={13} />
        <Bar width={48} height={16} />
      </span>
      <span className="sample-row-badges">
        <Bar width={56} height={16} />
        <Bar width={42} height={16} />
      </span>
    </div>
  );
}

/**
 * Loading placeholder for ResultsDashboard, shaped like the real layout
 * (summary bar, sample list, detail pane) so the page doesn't jump when
 * real content arrives. Shown while /api/results + /api/dataset are in
 * flight - typically several seconds to over a minute, since it's a live
 * run across the whole dataset the first time.
 */
function DashboardSkeleton() {
  return (
    <div className="dashboard" aria-busy="true" aria-label="Loading results">
      <div className="summary-bar">
        <div className="summary-stats">
          <Bar width={130} height={18} />
          <Bar width={130} height={18} />
        </div>
        <Bar width="100%" height={108} radius="var(--radius-panel)" style={{ flex: "1 1 240px", minWidth: 220 }} />
      </div>

      <div className="sample-explorer">
        <div className="sample-list">
          {Array.from({ length: 12 }).map((_, index) => (
            <SkeletonRow key={index} />
          ))}
        </div>

        <div className="sample-detail">
          <div className="sample-detail-header">
            <Bar width={170} height={17} />
            <Bar width={64} height={16} />
          </div>
          <Bar width="100%" height={46} radius="var(--radius-panel)" />
          <Bar width="100%" height={240} radius="var(--radius-panel)" />
          <div className="findings-columns">
            <Bar width="100%" height={72} radius="var(--radius-panel)" />
            <Bar width="100%" height={72} radius="var(--radius-panel)" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default DashboardSkeleton;
