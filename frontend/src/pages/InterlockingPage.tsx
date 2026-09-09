import React, { useState } from 'react';

type CBIState = 'FREE' | 'LOCKED' | 'OCCUPIED' | 'FAILED';

interface Signal {
  id: string; aspect: 'GREEN' | 'YELLOW' | 'RED' | 'DARK';
}

interface Point {
  id: string; position: 'NORMAL' | 'REVERSE' | 'MOVING' | 'FAILED';
}

interface Route {
  id: string; name: string; state: 'FREE' | 'REQUESTED' | 'LOCKED' | 'OCCUPIED';
  from: string; to: string; conflictsWith: string[];
}

const SIGNALS: Signal[] = [
  { id: 'SIG-01', aspect: 'GREEN' },
  { id: 'SIG-02', aspect: 'YELLOW' },
  { id: 'SIG-03', aspect: 'RED' },
  { id: 'SIG-04', aspect: 'GREEN' },
  { id: 'SIG-05', aspect: 'RED' },
  { id: 'SIG-06', aspect: 'DARK' },
];

const POINTS: Point[] = [
  { id: 'P-01', position: 'NORMAL' },
  { id: 'P-02', position: 'REVERSE' },
  { id: 'P-03', position: 'NORMAL' },
  { id: 'P-04', position: 'MOVING' },
  { id: 'P-05', position: 'FAILED' },
];

const ROUTES: Route[] = [
  { id: 'R-01', name: 'Up Main',    state: 'LOCKED',    from: 'NORTH', to: 'HUB', conflictsWith: ['R-02'] },
  { id: 'R-02', name: 'Down Main',  state: 'FREE',      from: 'HUB',   to: 'NORTH', conflictsWith: ['R-01'] },
  { id: 'R-03', name: 'Up Loop',    state: 'OCCUPIED',  from: 'EAST',  to: 'HUB', conflictsWith: [] },
  { id: 'R-04', name: 'Shunt 1A',   state: 'REQUESTED', from: 'YARD',  to: 'WEST', conflictsWith: [] },
];

const ASPECT_COLORS: Record<string, string> = {
  GREEN:  '#00f5a0',
  YELLOW: '#fbbf24',
  RED:    '#ff4d6d',
  DARK:   '#374151',
};

export function InterlockingPage() {
  const [signals, setSignals] = useState<Signal[]>(SIGNALS);
  const [points, setPoints] = useState<Point[]>(POINTS);
  const [routes, setRoutes] = useState<Route[]>(ROUTES);
  const [log, setLog] = useState<string[]>([
    '15:44:02 INFO Route R-01 locked for ICE-1401',
    '15:43:58 INFO Signal SIG-01 cleared to GREEN',
    '15:43:45 WARN Point P-04 in transit (MOVING)',
    '15:43:30 ERROR Point P-05 failure detected',
    '15:43:20 INFO CBI Petri-Net verification PASSED',
  ]);

  const addLog = (msg: string) => {
    const ts = new Date().toLocaleTimeString();
    setLog(prev => [`${ts} ${msg}`, ...prev.slice(0, 19)]);
  };

  const requestRoute = (route: Route) => {
    if (route.state !== 'FREE') {
      addLog(`WARN Cannot set route ${route.id} — state: ${route.state}`);
      return;
    }
    setRoutes(prev => prev.map(r => r.id === route.id ? { ...r, state: 'LOCKED' } : r));
    addLog(`INFO Route ${route.id} (${route.name}) locked`);
  };

  const cancelRoute = (route: Route) => {
    setRoutes(prev => prev.map(r => r.id === route.id ? { ...r, state: 'FREE' } : r));
    addLog(`INFO Route ${route.id} cancelled/released`);
  };

  return (
    <div>
      <div className="section-header mb-lg">
        <div className="section-dot" style={{ background: 'var(--color-rose)' }} />
        <h2>Computer-Based Interlocking (CBI)</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <span className="badge badge-emerald">ERTMS Level 2</span>
          <span className="badge badge-cyan">Petri-Net Verified</span>
        </div>
      </div>

      <div className="grid-3 mb-lg">
        {/* Signals Panel */}
        <div className="card">
          <div className="card-title mb-md">Signal Aspects</div>
          <div className="grid-2" style={{ gap: 8 }}>
            {signals.map(sig => (
              <div key={sig.id} style={{
                padding: '10px 12px',
                background: 'var(--color-bg-elevated)',
                border: `1px solid ${ASPECT_COLORS[sig.aspect]}44`,
                borderRadius: 'var(--radius-md)',
                display: 'flex', alignItems: 'center', gap: 10,
              }}>
                {/* Signal lamp */}
                <div style={{
                  width: 14, height: 14,
                  borderRadius: '50%',
                  background: ASPECT_COLORS[sig.aspect],
                  boxShadow: sig.aspect !== 'DARK' ? `0 0 8px ${ASPECT_COLORS[sig.aspect]}` : undefined,
                  flexShrink: 0,
                }} />
                <div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-primary)' }}>{sig.id}</div>
                  <div style={{ fontSize: 9, color: ASPECT_COLORS[sig.aspect], fontFamily: 'var(--font-mono)' }}>{sig.aspect}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Points Panel */}
        <div className="card">
          <div className="card-title mb-md">Point Positions</div>
          {points.map(pt => (
            <div key={pt.id} style={{
              padding: '10px 12px', marginBottom: 8,
              background: 'var(--color-bg-elevated)',
              border: `1px solid ${pt.position === 'FAILED' ? 'var(--color-rose)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-md)',
              display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <span style={{ fontSize: 18 }}>
                {pt.position === 'NORMAL' ? '/' : pt.position === 'REVERSE' ? '\\' : pt.position === 'MOVING' ? '↔' : '❌'}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-primary)' }}>{pt.id}</div>
                <div style={{ fontSize: 9, fontFamily: 'var(--font-mono)', marginTop: 2, color:
                  pt.position === 'FAILED' ? 'var(--color-rose)' :
                  pt.position === 'MOVING' ? 'var(--color-amber)' :
                  'var(--color-emerald)' }}>
                  {pt.position}
                </div>
              </div>
              {pt.position !== 'FAILED' && (
                <button className="btn btn-ghost btn-sm" style={{ fontSize: 10 }}
                  onClick={() => addLog(`INFO Point ${pt.id} → ${pt.position === 'NORMAL' ? 'REVERSE' : 'NORMAL'}`)}>
                  Throw
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Routes Panel */}
        <div className="card">
          <div className="card-title mb-md">Route Table</div>
          {routes.map(r => (
            <div key={r.id} style={{
              padding: '10px 12px', marginBottom: 8,
              background: 'var(--color-bg-elevated)',
              border: `1px solid ${
                r.state === 'LOCKED' ? 'rgba(0,229,255,0.3)' :
                r.state === 'OCCUPIED' ? 'rgba(255,77,109,0.3)' :
                r.state === 'REQUESTED' ? 'rgba(251,191,36,0.3)' : 'var(--color-border)'
              }`,
              borderRadius: 'var(--radius-md)',
            }}>
              <div className="flex items-center justify-between mb-xs">
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--color-cyan)' }}>{r.id}</span>
                <span className={`badge ${
                  r.state === 'LOCKED' ? 'badge-cyan' :
                  r.state === 'OCCUPIED' ? 'badge-rose' :
                  r.state === 'REQUESTED' ? 'badge-amber' : 'badge-muted'
                }`}>{r.state}</span>
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-secondary)', marginBottom: 6 }}>
                {r.from} → {r.to} · {r.name}
              </div>
              <div className="flex gap-xs">
                {r.state === 'FREE' && (
                  <button className="btn btn-success btn-sm" style={{ fontSize: 10 }} onClick={() => requestRoute(r)}>Set</button>
                )}
                {(r.state === 'LOCKED' || r.state === 'REQUESTED') && (
                  <button className="btn btn-danger btn-sm" style={{ fontSize: 10 }} onClick={() => cancelRoute(r)}>Cancel</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* CBI Audit Log */}
      <div className="card">
        <div className="card-title mb-md">CBI Audit Log</div>
        <div className="live-log dark-scroll" style={{ height: 150 }}>
          {log.map((entry, i) => {
            const [ts, level, ...rest] = entry.split(' ');
            return (
              <div key={i} className="log-entry">
                <span className="log-timestamp">{ts}</span>
                <span className={`log-level ${level}`}>{level}</span>
                <span className="log-message">{rest.join(' ')}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
