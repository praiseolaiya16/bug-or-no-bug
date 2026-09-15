import { useEffect, useState } from "react";
import { analyzeSample, fetchDataset, fetchResults } from "../api/client.js";
import DashboardSkeleton from "./DashboardSkeleton.jsx";
import SampleDetail from "./SampleDetail.jsx";
import SampleList from "./SampleList.jsx";
import SummaryBar from "./SummaryBar.jsx";

function mergeSamples(resultsData, datasetData) {
  const codeById = new Map(datasetData.map((s) => [s.id, s.code]));
  return resultsData.per_sample.map((row) => ({
    ...row,
    code: codeById.get(row.id) ?? "",
  }));
}

/**
 * Top-level dashboard. Fetches /api/results (scored summary across the
 * whole dataset) and /api/dataset (source code per sample) once, then
 * lazily calls /api/analyze for the selected sample's actual findings
 * (line/message detail that /api/results doesn't carry, to keep that
 * endpoint cheap to render a list from).
 */
function ResultsDashboard() {
  const [results, setResults] = useState(null);
  const [samples, setSamples] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [detailsById, setDetailsById] = useState({});
  const [detailLoading, setDetailLoading] = useState(false);
  const [refreshingId, setRefreshingId] = useState(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchResults(), fetchDataset()])
      .then(([resultsData, datasetData]) => {
        if (cancelled) return;
        const merged = mergeSamples(resultsData, datasetData);
        setResults(resultsData);
        setSamples(merged);
        setSelectedId(merged[0]?.id ?? null);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedId || detailsById[selectedId]) return;
    let cancelled = false;
    setDetailLoading(true);
    analyzeSample(selectedId)
      .then((data) => {
        if (!cancelled) setDetailsById((prev) => ({ ...prev, [selectedId]: data }));
      })
      .catch((err) => {
        if (!cancelled) {
          setDetailsById((prev) => ({
            ...prev,
            [selectedId]: { static_findings: [], llm_findings: [], static_error: err.message },
          }));
        }
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId, detailsById]);

  function handleRefresh(id) {
    setRefreshingId(id);
    analyzeSample(id, { refresh: true })
      .then((data) => setDetailsById((prev) => ({ ...prev, [id]: data })))
      .catch((err) => {
        setDetailsById((prev) => ({
          ...prev,
          [id]: { static_findings: [], llm_findings: [], llm_error: err.message },
        }));
      })
      .finally(() => setRefreshingId((current) => (current === id ? null : current)));
  }

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <div className="dashboard">
        <p className="status-message status-message-error">Couldn't load results: {error}</p>
      </div>
    );
  }

  const selectedSample = samples.find((s) => s.id === selectedId) ?? null;
  const selectedDetail = selectedId ? detailsById[selectedId] : null;

  return (
    <div className="dashboard panel-transition">
      <SummaryBar overall={results.overall} byBugType={results.by_bug_type} llmAvailable={results.llm_available} />
      <div className="sample-explorer">
        <SampleList samples={samples} selectedId={selectedId} onSelect={setSelectedId} />
        <SampleDetail
          sample={selectedSample}
          detail={selectedDetail}
          loading={detailLoading}
          onRefresh={handleRefresh}
          refreshing={refreshingId === selectedId}
        />
      </div>
    </div>
  );
}

export default ResultsDashboard;
