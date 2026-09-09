import React from 'react';
import type { Conflict, Train } from '../types';

interface AlertsPanelProps {
  open: boolean;
  conflicts: Conflict[];
  trains: Train[];
  onClose: () => void;
}

function timeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60)  return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

export function AlertsPanel({ open, conflicts, trains, onClose }: AlertsPanelProps) {
  const delayedTrains = trains.filter(t => (t.current_delay_minutes || 0) > 2);

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed', inset: 0,
            background: 'rgba(0,0,0,0.3)',
            zIndex: 999,
          }}
        />
      )}

      {/* Panel */}
      <aside className={`slide-panel ${open ? 'open' : ''}`}>
        <div className="flex items-center justify-between mb-lg">
          <div className="flex items-center gap-sm">
            <span style={{ fontSize: 18 }}>🔔</span>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
              Alerts &amp; Events
            </h2>
          </div>
          <button className="btn btn-ghost btn-icon" onClick={onClose} id="close-alerts-btn">✕</button>
        </div>

        {/* Active Conflicts */}
        {conflicts.length > 0 && (
          <section className="mb-lg">
            <div className="card-title mb-sm">Active Conflicts ({conflicts.length})</div>
            {conflicts.map((c, i) => (
              <div key={i} className="alert-item critical">
                <span className="alert-icon">⚠️</span>
                <div className="alert-content">
                  <div className="alert-title">
                    {String(c.conflict_type || 'Conflict').replace(/_/g, ' ')}
                  </div>
                  <div className="alert-desc">
                    Trains: {Array.isArray(c.train_ids) ? c.train_ids.join(', ') : '—'}
                  </div>
                  <div className="alert-desc" style={{ color: 'var(--color-rose)', marginTop: 2 }}>
                    {c.description || 'Conflict detected on network'}
                  </div>
                </div>
                <div className="alert-time">{timeAgo(new Date(c.detected_at || Date.now()))}</div>
              </div>
            ))}
          </section>
        )}

        {/* Delayed Trains */}
        {delayedTrains.length > 0 && (
          <section className="mb-lg">
            <div className="card-title mb-sm">Delayed Trains ({delayedTrains.length})</div>
            {delayedTrains.map(t => (
              <div key={t.id} className="alert-item warning">
                <span className="alert-icon">🚄</span>
                <div className="alert-content">
                  <div className="alert-title">{t.train_number}</div>
                  <div className="alert-desc">
                    Delay: +{t.current_delay_minutes?.toFixed(1)} min
                  </div>
                </div>
                <span className="badge badge-amber">{t.status}</span>
              </div>
            ))}
          </section>
        )}

        {/* Empty state */}
        {conflicts.length === 0 && delayedTrains.length === 0 && (
          <div style={{
            textAlign: 'center',
            padding: '48px 16px',
            color: 'var(--text-muted)',
          }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
              No active alerts
            </div>
            <div style={{ fontSize: 11, marginTop: 6 }}>
              All systems operating normally
            </div>
          </div>
        )}

        {/* System events */}
        <section>
          <div className="card-title mb-sm">System Events</div>
          <div className="live-log dark-scroll">
            {[
              { level: 'INFO',  msg: 'Simulation tick completed',        time: '15:37:40' },
              { level: 'INFO',  msg: 'Route optimizer cycle finished',   time: '15:37:35' },
              { level: 'WARN',  msg: 'Platform 3A approaching capacity', time: '15:37:20' },
              { level: 'INFO',  msg: 'CBI route R-12 set successfully',  time: '15:37:15' },
              { level: 'DEBUG', msg: 'Petri-Net verification passed',    time: '15:36:58' },
              { level: 'INFO',  msg: 'AI delay model retrained (7ms)',   time: '15:36:45' },
              { level: 'INFO',  msg: 'Physics engine tick OK',           time: '15:36:30' },
            ].map((entry, i) => (
              <div key={i} className="log-entry">
                <span className="log-timestamp">{entry.time}</span>
                <span className={`log-level ${entry.level}`}>{entry.level}</span>
                <span className="log-message">{entry.msg}</span>
              </div>
            ))}
          </div>
        </section>
      </aside>
    </>
  );
}
