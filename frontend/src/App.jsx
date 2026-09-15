import ResultsDashboard from "./components/ResultsDashboard.jsx";

/**
 * Root application component for Bug-or-No-Bug: static analysis vs. LLM
 * code review, inspected sample by sample against a seeded bug dataset.
 */
function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>bug-or-no-bug</h1>
        <p>static analysis vs. llm review, scored against 20 seeded bugs</p>
      </header>
      <main>
        <ResultsDashboard />
      </main>
    </div>
  );
}

export default App;
