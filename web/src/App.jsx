import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);

  useEffect(() => {
    // For now, we will use dummy data, as the API to list runs is not specified.
    const dummyRuns = [
      { run_id: 'd9e8f7a6-c5b4-4e3d-8f6a-8e9d0c0b0a0e', status: 'completed' },
      { run_id: 'a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6', status: 'running' },
    ];
    setRuns(dummyRuns);
  }, []);

  const handleRunClick = (runId) => {
    // In a real app, you would fetch the run details from the API
    // GET /api/runs/:id/summary
    axios.get(`/api/runs/${runId}/summary`)
      .then(response => {
        setSelectedRun(response.data);
      })
      .catch(error => {
        console.error('Error fetching run details:', error);
        // For now, show dummy details
        setSelectedRun({
          run_id: runId,
          match: true,
          meta: { scenario_id: 'smoke_test' },
          kpi: { avg_travel_time: 120 }
        });
      });
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>CARLA Runs</h1>
      </header>
      <div className="container">
        <div className="run-list">
          <h2>Runs</h2>
          <ul>
            {runs.map(run => (
              <li key={run.run_id} onClick={() => handleRunClick(run.run_id)}>
                {run.run_id} - {run.status}
              </li>
            ))}
          </ul>
        </div>
        <div className="run-detail">
          <h2>Run Details</h2>
          {selectedRun ? (
            <pre>{JSON.stringify(selectedRun, null, 2)}</pre>
          ) : (
            <p>Select a run to see details.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;