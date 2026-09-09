import React, { useState } from 'react';

export function OptimizationPage() {
  const [activeTab, setActiveTab] = useState<'route' | 'schedule' | 'energy' | 'flow'>('route');
  const [running, setRunning] = useState(false);

  const runOptimization = () => {
    setRunning(true);
    setTimeout(() => setRunning(false), 3000);
  };

  return (
    <div>
      <div className="section-header mb-lg">
        <div className="section-dot" style={{ background: 'var(--color-orange)' }} />
        <h2>Optimization Engine</h2>
        <button
          className={`btn ml-auto ${running ? 'btn-outline' : 'btn-primary'}`}
          onClick={runOptimization}
          disabled={running}
          id="run-optimization-btn"
        >
          {running ? (
            <><span className="animate-spin" style={{ display: 'inline-block' }}>⟳</span> Running...</>
          ) : '⚡ Run Optimization'}
        </button>
      </div>

      {/* Algorithm status */}
      <div className="grid-4 mb-lg">
        {[
          { label: 'Route Optimizer',    status: 'ACTIVE',   algo: 'Dijkstra + A*',    iter: '1,248' },
          { label: 'Schedule Optimizer', status: 'ACTIVE',   algo: 'CSP + Backtrack',  iter: '456' },
          { label: 'Energy Optimizer',   status: 'IDLE',     algo: 'DP + Speed Profile', iter: '89' },
          { label: 'Flow Optimizer',     status: 'ACTIVE',   algo: 'Linear Program',   iter: '33' },
        ].map((m, i) => (
          <div key={i} className="card">
            <div className="card-title mb-sm">{m.label}</div>
            <span className={`badge ${m.status === 'ACTIVE' ? 'badge-emerald' : 'badge-muted'} mb-sm`} style={{ display: 'inline-block', marginBottom: 8 }}>
              {m.status}
            </span>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{m.algo}</div>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', marginTop: 4 }}>
              {m.iter} iterations
            </div>
          </div>
        ))}
      </div>

      <div className="tabs-header">
        {[
          { id: 'route',    label: '🗺 Route Optimization' },
          { id: 'schedule', label: '📅 Schedule' },
          { id: 'energy',   label: '⚡ Energy' },
          { id: 'flow',     label: '🌊 Traffic Flow' },
        ].map(t => (
          <button key={t.id} className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id as any)}>
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'route' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-title mb-md">Dijkstra / A* Route Finder</div>
            <div className="form-group">
              <label className="form-label">Origin</label>
              <select className="form-select">
                <option>NORTH</option><option>HUB</option><option>EAST</option>
                <option>WEST</option><option>SOUTH</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Destination</label>
              <select className="form-select">
                <option>SOUTH</option><option>EAST</option><option>NE</option>
                <option>SE</option><option>WEST</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Objective</label>
              <select className="form-select">
                <option>Minimum Travel Time</option>
                <option>Minimum Delay</option>
                <option>Minimum Energy</option>
                <option>Maximum Reliability</option>
              </select>
            </div>
            <button className="btn btn-primary" onClick={runOptimization}>
              {running ? '⟳ Computing...' : '🧮 Find Optimal Route'}
            </button>
          </div>
          <div className="card">
            <div className="card-title mb-md">Optimal Route Result</div>
            <div style={{ padding: 12, background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', marginBottom: 12 }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-cyan)' }}>
                NORTH → HUB → EAST → NE
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>
                3 intermediate stops · 87.2 km
              </div>
            </div>
            {[
              { label: 'Travel Time',     value: '58 min',    color: 'var(--color-emerald)' },
              { label: 'Predicted Delay', value: '+2.1 min',  color: 'var(--color-amber)' },
              { label: 'Energy Est.',     value: '128 kWh',   color: 'var(--color-cyan)' },
              { label: 'Conflict Risk',   value: 'Low (12%)', color: 'var(--color-emerald)' },
            ].map((r, i) => (
              <div key={i} className="flex justify-between mb-sm" style={{ fontSize: 12 }}>
                <span style={{ color: 'var(--text-secondary)' }}>{r.label}</span>
                <span style={{ fontFamily: 'var(--font-mono)', color: r.color }}>{r.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'energy' && (
        <div className="card">
          <div className="card-title mb-md">Energy-Optimal Speed Profile</div>
          <div className="grid-3 mb-lg" style={{ gap: 8 }}>
            {[
              { label: 'Total Energy Saved', value: '234 kWh', color: 'var(--color-emerald)' },
              { label: 'Eco-Drive Trains',   value: '4 / 6',   color: 'var(--color-cyan)' },
              { label: 'CO₂ Reduction',      value: '127 kg',  color: 'var(--color-emerald)' },
            ].map((s, i) => (
              <div key={i} className="kpi-card" style={{ '--kpi-color': s.color } as React.CSSProperties}>
                <div className="kpi-label">{s.label}</div>
                <div className="kpi-value" style={{ fontSize: 20 }}>{s.value}</div>
              </div>
            ))}
          </div>
          {state => (
            <div style={{ padding: 16, background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>
              <div style={{ color: 'var(--text-muted)', marginBottom: 8 }}>Speed Profile — ICE-1401 (NORTH→SOUTH)</div>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 60 }}>
                {[120, 160, 160, 140, 100, 80, 60, 80, 120, 160, 160, 130, 80, 40].map((v, i) => (
                  <div key={i} style={{
                    flex: 1, height: `${v / 160 * 100}%`,
                    background: 'var(--color-cyan)',
                    opacity: 0.7,
                    borderRadius: '2px 2px 0 0',
                  }} title={`${v} km/h`} />
                ))}
              </div>
              <div style={{ color: 'var(--text-muted)', marginTop: 6 }}>← Distance →</div>
            </div>
          )}
        </div>
      )}

      {(activeTab === 'schedule' || activeTab === 'flow') && (
        <div className="card">
          <div className="card-title mb-md">
            {activeTab === 'schedule' ? 'Schedule Optimization Results' : 'Traffic Flow Optimization'}
          </div>
          <div style={{ color: 'var(--text-secondary)', fontSize: 13, textAlign: 'center', padding: '48px' }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🧬</div>
            Click <strong>Run Optimization</strong> to execute the {activeTab} optimizer.<br/>
            Results will appear here after completion.
          </div>
        </div>
      )}
    </div>
  );
}
