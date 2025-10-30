import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getRuns = () => {
  // This endpoint is not specified in the PRD, so we will return dummy data.
  return Promise.resolve({
    data: [
      { run_id: 'd9e8f7a6-c5b4-4e3d-8f6a-8e9d0c0b0a0e', status: 'completed' },
      { run_id: 'a1b2c3d4-e5f6-a7b8-c9d0-e1f2a3b4c5d6', status: 'running' },
    ]
  });
};

export const getRunSummary = (runId) => {
  return apiClient.get(`/runs/${runId}/summary`);
};

export const runSmokeTest = (params) => {
  return apiClient.post('/run/smoke', params);
};
