import React, { useState, useEffect } from 'react';
import { api } from './services/api';
import { Train, Conflict, KPIData } from './types';

export function App() {
  const [trains, setTrains] = useState<Train[]>([]);
  const [conflicts, setConflicts] = useState<Conflict[]>([]);
  const [kpis, setKpis] = useState<Partial<KPIData>>({
    punctuality_rate: 96.8,
    average_delay_minutes: 1.4,
    active_trains: 6,
    total_conflicts_active: 0,
    network_throughput_tph: 24.5
  });

  useEffect(() => {
    async function loadData() {
      try {
        const [trainData, conflictData, analyticsData] = await Promise.all([
          api.getTrains(),
          api.getConflicts(),
          api.getAnalyticsDashboard()
        ]);
        setTrains(trainData);
        setConflicts(conflictData);
        if (analyticsData && analyticsData.kpis) {
          setKpis(analyticsData.kpis);
        }
      } catch (err) {
        console.error("Dashboard initial load failed", err);
      }
    }
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      <header className="flex justify-between items-center pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center">
            <span className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse mr-3"></span>
            AI Railway Traffic Control Center
          </h1>
          <p className="text-xs text-cyan-400 font-mono mt-1">Autonomous Simulation, ML Prediction & Schedule Optimization</p>
        </div>
        <div className="flex space-x-3">
          <button onClick={() => api.controlSimulation('start')} className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded text-xs font-semibold">Start</button>
          <button onClick={() => api.controlSimulation('pause')} className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 rounded text-xs font-semibold">Pause</button>
          <button onClick={() => api.controlSimulation('step')} className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 rounded text-xs font-semibold">Step (10s)</button>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 my-6">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Punctuality</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{kpis.punctuality_rate}%</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Avg Delay</div>
          <div className="text-2xl font-bold text-white mt-1">{kpis.average_delay_minutes} min</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Active Fleet</div>
          <div className="text-2xl font-bold text-cyan-400 mt-1">{kpis.active_trains} Trains</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Conflicts</div>
          <div className="text-2xl font-bold text-rose-400 mt-1">{conflicts.length} Active</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div className="text-[11px] font-mono text-slate-400 uppercase">Throughput</div>
          <div className="text-2xl font-bold text-purple-400 mt-1">{kpis.network_throughput_tph} TPH</div>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-lg font-bold text-white mb-4">Fleet Telemetry Status</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-slate-400 font-mono uppercase border-b border-slate-800">
              <tr>
                <th className="p-3">Train</th>
                <th className="p-3">Type</th>
                <th className="p-3">Speed</th>
                <th className="p-3">Delay</th>
                <th className="p-3">Priority</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {trains.map(t => (
                <tr key={t.id} className="hover:bg-slate-800/50">
                  <td className="p-3 font-mono font-bold text-cyan-400">{t.train_number}</td>
                  <td className="p-3">{t.train_type}</td>
                  <td className="p-3 font-mono text-white">{t.current_speed_kmh} km/h</td>
                  <td className="p-3 font-mono text-emerald-400">{t.current_delay_minutes} min</td>
                  <td className="p-3 font-mono">{t.priority}</td>
                  <td className="p-3"><span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 text-[10px] font-mono">{t.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
