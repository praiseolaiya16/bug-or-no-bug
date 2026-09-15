import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

// Categorical slots 1 & 2 from the project's validated palette (blue/orange,
// CVD-safe adjacent pair) - fixed order, static analysis always first. Used
// for this chart AND the static/LLM badges elsewhere, so the same entity
// always reads as the same color across the app.
const COLORS = {
  light: { static: "#2a78d6", llm: "#eb6834", grid: "#e2ded0", ink: "#8f8973" },
  dark: { static: "#3987e5", llm: "#d95926", grid: "#2c2820", ink: "#79735f" },
};

function useColorScheme() {
  const getScheme = () =>
    window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  const [scheme, setScheme] = useState(getScheme);

  useEffect(() => {
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (event) => setScheme(event.matches ? "dark" : "light");
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return scheme;
}

function formatPercentTick(value) {
  return `${Math.round(value * 100)}%`;
}

/**
 * Grouped bar chart comparing static analysis vs. LLM review recall,
 * broken down by seeded bug category (logic / security / style).
 *
 * @param {{ byBugType: { static: object, llm: object|null }, compact?: boolean }} props
 */
function BugTypeChart({ byBugType, compact = false }) {
  const colors = COLORS[useColorScheme()];

  if (!byBugType || !byBugType.static) {
    return <p className="status-message">No category data yet.</p>;
  }

  const bugTypes = Object.keys(byBugType.static);
  const data = bugTypes.map((bugType) => ({
    bugType,
    static: byBugType.static[bugType]?.recall ?? 0,
    llm: byBugType.llm ? byBugType.llm[bugType]?.recall ?? 0 : undefined,
  }));

  const height = compact ? 130 : 280;
  const fontSize = compact ? 11 : 13;

  return (
    <div className={`bug-type-chart${compact ? " bug-type-chart-compact" : ""}`}>
      {!compact && <h2>Recall by Bug Category</h2>}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 0 }} barCategoryGap="30%">
          <CartesianGrid vertical={false} stroke={colors.grid} />
          <XAxis
            dataKey="bugType"
            tick={{ fill: colors.ink, fontSize }}
            axisLine={{ stroke: colors.grid }}
            tickLine={false}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={formatPercentTick}
            tick={{ fill: colors.ink, fontSize }}
            axisLine={false}
            tickLine={false}
            width={compact ? 48 : 58}
          />
          <Tooltip
            formatter={(value) => formatPercentTick(value)}
            cursor={{ fill: "var(--ink-primary)", fillOpacity: 0.06 }}
            contentStyle={{
              backgroundColor: "var(--panel-bg)",
              border: "1px solid var(--border)",
              borderRadius: 6,
              fontSize: 12,
              padding: "6px 10px",
            }}
            labelStyle={{
              color: "var(--ink-primary)",
              fontWeight: 700,
              marginBottom: 4,
              textTransform: "uppercase",
              letterSpacing: "0.03em",
              fontSize: 11,
            }}
            itemStyle={{ padding: 0 }}
          />
          <Legend
            wrapperStyle={{ color: "var(--ink-secondary)", fontSize: compact ? 11 : 12 }}
            iconType="circle"
            iconSize={8}
          />
          <Bar dataKey="static" name="Static analysis" fill={colors.static} radius={[2, 2, 0, 0]} maxBarSize={28} />
          {byBugType.llm && (
            <Bar dataKey="llm" name="LLM review" fill={colors.llm} radius={[2, 2, 0, 0]} maxBarSize={28} />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default BugTypeChart;
