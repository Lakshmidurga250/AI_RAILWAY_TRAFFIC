const API_BASE = '';

export const api = {
  async getTrains() {
    const res = await fetch(`${API_BASE}/trains`);
    return res.json();
  },
  async getStations() {
    const res = await fetch(`${API_BASE}/stations`);
    return res.json();
  },
  async getNetworkGraph() {
    const res = await fetch(`${API_BASE}/network/graph`);
    return res.json();
  },
  async getSimulationStatus() {
    const res = await fetch(`${API_BASE}/simulation/status`);
    return res.json();
  },
  async controlSimulation(action: string, accelerationFactor = 1.0) {
    const res = await fetch(`${API_BASE}/simulation/control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, acceleration_factor: accelerationFactor })
    });
    return res.json();
  },
  async getConflicts() {
    const res = await fetch(`${API_BASE}/conflicts`);
    return res.json();
  },
  async resolveConflict(conflictId: string) {
    const res = await fetch(`${API_BASE}/optimization/conflicts/${conflictId}/resolve`, {
      method: 'POST'
    });
    return res.json();
  },
  async predictDelay(trainId: string, horizonMinutes = 15) {
    const res = await fetch(`${API_BASE}/ai/delay`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ train_id: trainId, horizon_minutes: horizonMinutes })
    });
    return res.json();
  },
  async optimizeRoute(origin: string, dest: string, algorithm = 'MULTI_OBJECTIVE') {
    const res = await fetch(`${API_BASE}/optimization/route`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        origin_station_id: origin,
        destination_station_id: dest,
        algorithm,
        train_id: 'SERVICE_OPT'
      })
    });
    return res.json();
  },
  async getAnalyticsDashboard() {
    const res = await fetch(`${API_BASE}/analytics/dashboard`);
    return res.json();
  }
};
