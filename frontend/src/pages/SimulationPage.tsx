import React, { useState } from 'react';
import type { AppState } from '../App';

interface SimulationPageProps {
  state: AppState;
  onSimControl: (action: 'start' | 'pause' | 'stop' | 'step') => void;
  onSpeedChange: (speed: number) => void;
}

export function SimulationPage({ state, onSimControl, onSpeedChange }: SimulationPageProps) {
  const [scenario, setScenario] = useState('normal');
  const [activeTab, setActiveTab] = useState<'control' | 'events' | 'physics'>('control');

  const simTimeStr = new Date(state.simTime * 1000).toISOString().substring(11, 19);

  return (
    <div>
      <div className="section-header mb-lg">
        <div className="section-dot" style={{ background: 'var(--color-amber)' }} />
        <h2>Simulation Engine</h2>
        <div style={{ marginLeft: 'auto' }}>
          <span className={`badge ${state.simRunning ? 'badge-emerald' : 'badge-amber'}`}>
            {state.simRunning ? '● RUNNING' : '⏸ PAUSED'}
          </span>
        </div>
      </div>

      {/* Main control panel */}
      <div className="grid-3 mb-lg">
        {/* Time display */}
        <div className="card" style={{ gridColumn: '1' }}>
          <div className="card-title mb-md">Simulation Clock</div>
          <div style={{
            fontFamily: 'var(--font-brand)',
            fontSize: 40,
            color: 'var(--color-cyan)',
            letterSpacing: 4,
            textAlign: 'center',
            padding: '16px 0',
            textShadow: 'var(--glow-cyan)',
          }}>
            {simTimeStr}
          </div>
          <div style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
            Speed: {state.simSpeed}× real-time
          </div>
        </div>

        {/* Controls */}
        <div className="card">
          <div className="card-title mb-md">Simulation Controls</div>
          <div className="flex gap-sm mb-md flex-wrap">
            <button id="sim-page-start" className="btn btn-success" onClick={() => onSimControl('start')}>▶ Start</button>
            <button id="sim-page-pause" className="btn btn-warning" onClick={() => onSimControl('pause')}>⏸ Pause</button>
            <button id="sim-page-step"  className="btn btn-outline" onClick={() => onSimControl('step')}>⏭ Step</button>
            <button id="sim-page-stop"  className="btn btn-danger"  onClick={() => onSimControl('stop')}>⏹ Stop</button>
          </div>
          <div className="card-title mb-sm">Playback Speed</div>
          <div className="speed-selector flex gap-xs">
            {[1, 5, 10, 30, 60, 120].map(spd => (
              <button
                key={spd}
                className={`speed-btn ${state.simSpeed === spd ? 'active' : ''}`}
                onClick={() => onSpeedChange(spd)}
              >
                {spd}×
              </button>
            ))}
          </div>
        </div>

        {/* Scenario selector */}
        <div className="card">
          <div className="card-title mb-md">Scenario</div>
          <div className="form-group">
            <label className="form-label">Active Scenario</label>
            <select className="form-select" value={scenario} onChange={e => setScenario(e.target.value)}>
              <option value="normal">Normal Operations</option>
              <option value="peak">Peak Hour Traffic</option>
              <option value="disruption">Major Disruption</option>
              <option value="maintenance">Planned Maintenance</option>
              <option value="emergency">Emergency Response</option>
              <option value="weather">Adverse Weather</option>
            </select>
          </div>
          <button className="btn btn-primary btn-sm w-full">Load Scenario</button>
        </div>
      </div>

      <div className="tabs-header">
        {[
          { id: 'control', label: '⚙️ Engine Parameters' },
          { id: 'events',  label: '📋 Event Log' },
          { id: 'physics', label: '⚗️ Physics State' },
        ].map(t => (
          <button key={t.id} className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id as any)}>
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'control' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-title mb-md">Engine Parameters</div>
            {[
              { label: 'Time Step (seconds)', value: '10', type: 'number' },
              { label: 'Max Trains',          value: '50', type: 'number' },
              { label: 'Headway Min (min)',    value: '3',  type: 'number' },
              { label: 'Random Seed',         value: '42', type: 'number' },
            ].map((p, i) => (
              <div key={i} className="form-group">
                <label className="form-label">{p.label}</label>
                <input className="form-input" type={p.type} defaultValue={p.value} />
              </div>
            ))}
          </div>
          <div className="card">
            <div className="card-title mb-md">Simulation Statistics</div>
            <div className="grid-2" style={{ gap: 8 }}>
              {[
                { label: 'Ticks Elapsed',    value: Math.floor(state.simTime / 10).toLocaleString(), color: 'var(--color-cyan)' },
                { label: 'Events Processed', value: (Math.floor(state.simTime / 10) * 3).toLocaleString(), color: 'var(--color-blue)' },
                { label: 'Decisions Made',   value: (Math.floor(state.simTime / 10) * 7).toLocaleString(), color: 'var(--color-purple)' },
                { label: 'Conflicts Found',  value: String(state.conflicts.length), color: 'var(--color-rose)' },
              ].map((s, i) => (
                <div key={i} style={{
                  background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)', padding: '10px 12px',
                }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{s.label}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: s.color }}>{s.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'events' && (
        <div className="card">
          <div className="card-title mb-md">Live Event Stream</div>
          <div className="live-log dark-scroll" style={{ height: 320 }}>
            {Array.from({ length: 30 }).map((_, i) => {
              const levels = ['INFO', 'INFO', 'INFO', 'WARN', 'ERROR', 'DEBUG'];
              const level = levels[Math.floor(Math.random() * levels.length)];
              const msgs = [
                'Train ICE-1401 departed platform 1A',
                'Route R-12 locked successfully',
                'CBI: Signal SIG-04 cleared to GREEN',
                'Delay prediction updated for RE-2205',
                'Headway violation detected: trains T3, T5',
                'Point P-07 moved to REVERSE',
                'Platform 2B: dwell time expired',
                'RL agent dispatched train IC-3301',
                'Overlap OVL-3 released by timer',
                'Petri-Net verification: PASS',
              ];
              const msg = msgs[Math.floor(Math.random() * msgs.length)];
              const sec = i * 2;
              const t = new Date(Date.now() - sec * 1000);
              return (
                <div key={i} className="log-entry">
                  <span className="log-timestamp">{t.toLocaleTimeString()}</span>
                  <span className={`log-level ${level}`}>{level}</span>
                  <span className="log-message">{msg}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === 'physics' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-title mb-md">Adhesion & Braking</div>
            {state.trains.slice(0, 4).map((t, i) => (
              <div key={i} style={{ marginBottom: 16, padding: '10px 12px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-cyan)', marginBottom: 6 }}>{t.train_number}</div>
                <div className="grid-2" style={{ gap: 4, fontSize: 10, fontFamily: 'var(--font-mono)' }}>
                  <div>Adhesion: <span style={{ color: 'var(--color-emerald)' }}>0.28 μ</span></div>
                  <div>Tractive: <span style={{ color: 'var(--color-amber)' }}>285 kN</span></div>
                  <div>Brake: <span style={{ color: 'var(--color-rose)' }}>0.9 m/s²</span></div>
                  <div>Power: <span style={{ color: 'var(--color-purple)' }}>4.2 MW</span></div>
                </div>
              </div>
            ))}
          </div>
          <div className="card">
            <div className="card-title mb-md">Catenary Power Flow</div>
            {['Sector A (25kV)', 'Sector B (25kV)', 'Sector C (15kV)'].map((s, i) => (
              <div key={i} style={{ marginBottom: 12 }}>
                <div className="flex justify-between mb-xs" style={{ fontSize: 11 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{s}</span>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-cyan)' }}>
                    {(60 + Math.random() * 30).toFixed(1)} MW
                  </span>
                </div>
                <div className="progress-bar-wrapper">
                  <div className="progress-bar-fill" style={{
                    width: `${40 + Math.random() * 50}%`,
                    '--progress-color': 'var(--color-amber)',
                  } as React.CSSProperties} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
