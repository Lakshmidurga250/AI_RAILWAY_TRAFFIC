import React from 'react';
import type { AppState } from '../App';
import type { PageId } from '../App';

interface TopBarProps {
  state: AppState;
  onSimControl: (action: 'start' | 'pause' | 'stop' | 'step') => void;
  alertCount: number;
  onAlertsToggle: () => void;
  onMenuToggle: () => void;
}

function formatSimTime(seconds: number): string {
  const d = new Date(seconds * 1000);
  return d.toISOString().substring(11, 19);
}

export function TopBar({ state, onSimControl, alertCount, onAlertsToggle, onMenuToggle }: TopBarProps) {
  const now = new Date();
  const timeStr = now.toLocaleTimeString('en-IN', { hour12: false });
  const dateStr = now.toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short' });

  return (
    <header className="topbar">
      {/* Left: Brand */}
      <div className="flex items-center gap-md">
        <button className="btn btn-ghost btn-icon" onClick={onMenuToggle} id="menu-toggle-btn" title="Toggle sidebar">
          ☰
        </button>
        <div className="topbar-logo">
          <div className="topbar-logo-icon">🚄</div>
          <div>
            <div className="topbar-brand-name">RAILOPT AI</div>
            <div className="topbar-subtitle">Intelligent Railway Traffic Management</div>
          </div>
        </div>
      </div>

      {/* Center: Sim controls */}
      <div className="sim-controls">
        <div className="sim-control-group">
          <button
            id="sim-start-btn"
            className={`btn btn-sm ${state.simRunning ? 'btn-outline' : 'btn-success'}`}
            onClick={() => onSimControl('start')}
            title="Start simulation"
          >
            ▶ Start
          </button>
          <button
            id="sim-pause-btn"
            className="btn btn-sm btn-warning"
            onClick={() => onSimControl('pause')}
            title="Pause simulation"
          >
            ⏸ Pause
          </button>
          <button
            id="sim-step-btn"
            className="btn btn-sm btn-outline"
            onClick={() => onSimControl('step')}
            title="Step 10 seconds"
          >
            ⏭ Step
          </button>
        </div>

        <div className="sim-time-display" title="Simulation time">
          {formatSimTime(state.simTime)}
        </div>

        <div className="sim-control-group speed-selector">
          {[1, 5, 10, 60].map(spd => (
            <button
              key={spd}
              className={`speed-btn ${state.simSpeed === spd ? 'active' : ''}`}
              onClick={() => {/* handled in App */}}
              title={`${spd}x speed`}
            >
              {spd}×
            </button>
          ))}
        </div>
      </div>

      {/* Right: Status & alerts */}
      <div className="flex items-center gap-md">
        {/* System health */}
        <div className="topbar-status">
          <span className={`status-dot ${state.simRunning ? 'running pulse' : 'stopped'}`} />
          <span>{state.simRunning ? 'LIVE' : 'PAUSED'}</span>
        </div>

        {/* Train count */}
        <div className="topbar-status">
          <span style={{ color: 'var(--color-cyan)' }}>🚄</span>
          <span>{state.trains.length} trains</span>
        </div>

        {/* Clock */}
        <div className="topbar-status">
          <span style={{ color: 'var(--text-muted)' }}>🕐</span>
          <span>{timeStr}</span>
          <span style={{ color: 'var(--text-muted)', marginLeft: '4px' }}>{dateStr}</span>
        </div>

        {/* Alerts bell */}
        <button
          id="alerts-panel-btn"
          className="btn btn-ghost btn-icon"
          onClick={onAlertsToggle}
          title="Toggle alerts panel"
          style={{ position: 'relative' }}
        >
          🔔
          {alertCount > 0 && (
            <span style={{
              position: 'absolute',
              top: '-4px',
              right: '-4px',
              background: 'var(--color-rose)',
              color: 'white',
              fontSize: '9px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 700,
              padding: '1px 4px',
              borderRadius: '999px',
              minWidth: '16px',
              textAlign: 'center',
            }}>
              {alertCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
