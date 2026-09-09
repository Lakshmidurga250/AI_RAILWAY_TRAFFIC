import React, { useState } from 'react';
import type { AppState } from '../App';

interface DigitalTwinPageProps {
  state: AppState;
}

export function DigitalTwinPage({ state }: DigitalTwinPageProps) {
  const [syncMode, setSyncMode] = useState<'realtime' | 'predictive' | 'replay'>('realtime');

  return (
    <div>
      <div className="section-header mb-lg">
        <div className="section-dot" style={{ background: 'var(--color-indigo, #6366f1)' }} />
        <h2>Digital Twin</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          {(['realtime', 'predictive', 'replay'] as const).map(m => (
            <button key={m} className={`btn btn-sm ${syncMode === m ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setSyncMode(m)} id={`twin-mode-${m}`}>
              {m === 'realtime' ? '🔴 Real-Time' : m === 'predictive' ? '🔮 Predictive' : '⏪ Replay'}
            </button>
          ))}
        </div>
      </div>

      {/* Sync Status */}
      <div className="grid-4 mb-lg">
        {[
          { label: 'Sync Latency',     value: '12 ms',   color: 'var(--color-emerald)' },
          { label: 'Model Fidelity',   value: '99.8%',   color: 'var(--color-cyan)' },
          { label: 'Twin Objects',     value: '2,841',   color: 'var(--color-purple)' },
          { label: 'Prediction Horizon', value: '15 min', color: 'var(--color-amber)' },
        ].map((s, i) => (
          <div key={i} className="kpi-card" style={{ '--kpi-color': s.color } as React.CSSProperties}>
            <div className="kpi-label">{s.label}</div>
            <div className="kpi-value" style={{ fontSize: 22 }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        {/* 3D View placeholder */}
        <div className="card" style={{ gridColumn: '1' }}>
          <div className="card-title mb-md">Network Digital Twin — Live View</div>
          <div style={{
            height: 340,
            background: 'var(--color-bg-base)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            overflow: 'hidden',
          }}>
            {/* Animated grid */}
            <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.3 }}>
              {Array.from({ length: 8 }).map((_, i) => (
                <line key={`v${i}`} x1={`${i * 14}%`} y1="0" x2={`${i * 14}%`} y2="100%" stroke="#00e5ff" strokeWidth="0.5" />
              ))}
              {Array.from({ length: 6 }).map((_, i) => (
                <line key={`h${i}`} x1="0" y1={`${i * 18}%`} x2="100%" y2={`${i * 18}%`} stroke="#00e5ff" strokeWidth="0.5" />
              ))}
            </svg>
            {/* Pulsing nodes */}
            <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
              {[[30, 45], [55, 25], [70, 55], [45, 70], [20, 60]].map(([cx, cy], i) => (
                <g key={i}>
                  <circle cx={`${cx}%`} cy={`${cy}%`} r="8" fill="rgba(0,229,255,0.1)" stroke="#00e5ff" strokeWidth="1">
                    <animate attributeName="r" values="8;12;8" dur={`${1.5 + i * 0.3}s`} repeatCount="indefinite" />
                  </circle>
                  <circle cx={`${cx}%`} cy={`${cy}%`} r="3" fill="#00e5ff" />
                </g>
              ))}
              {/* Animated train markers */}
              {state.trains.slice(0, 4).map((t, i) => (
                <circle key={t.id} cx={`${25 + i * 15}%`} cy={`${30 + i * 10}%`} r="5" fill="#00f5a0">
                  <animate attributeName="cx" values={`${25 + i * 15}%;${30 + i * 15}%;${25 + i * 15}%`}
                    dur={`${3 + i}s`} repeatCount="indefinite" />
                </circle>
              ))}
            </svg>
            <div style={{
              position: 'relative', zIndex: 1,
              textAlign: 'center', color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono)', fontSize: 12,
            }}>
              <div style={{ fontSize: 32, marginBottom: 8 }}>🌐</div>
              Digital Twin — {syncMode} mode
            </div>
          </div>
        </div>

        {/* State comparison */}
        <div className="flex flex-col gap-lg">
          <div className="card">
            <div className="card-title mb-md">Physical vs Digital State</div>
            {state.trains.slice(0, 4).map((t, i) => (
              <div key={i} style={{ marginBottom: 12 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--color-cyan)', marginBottom: 4 }}>{t.train_number}</div>
                <div className="flex gap-md" style={{ fontSize: 10 }}>
                  <div style={{ flex: 1, padding: '6px 8px', background: 'var(--color-bg-elevated)', borderRadius: 6 }}>
                    <div style={{ color: 'var(--text-muted)' }}>Physical</div>
                    <div style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                      {t.current_speed_kmh?.toFixed(0)} km/h
                    </div>
                  </div>
                  <div style={{ flex: 1, padding: '6px 8px', background: 'rgba(99,102,241,0.1)', borderRadius: 6, border: '1px solid rgba(99,102,241,0.3)' }}>
                    <div style={{ color: 'var(--text-muted)' }}>Twin</div>
                    <div style={{ color: '#a5b4fc', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                      {((t.current_speed_kmh || 0) + (Math.random() * 2 - 1)).toFixed(0)} km/h
                    </div>
                  </div>
                  <div style={{ padding: '6px 8px', background: 'var(--color-bg-elevated)', borderRadius: 6 }}>
                    <div style={{ color: 'var(--text-muted)' }}>Δ</div>
                    <div style={{ color: 'var(--color-emerald)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>0.4%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-title mb-md">What-If Scenarios</div>
            {[
              { scenario: 'Signal failure at HUB',     impact: '+4.2 min avg delay',   risk: 'HIGH' },
              { scenario: 'Train breakdown — ICE-1401', impact: '+8.5 min cascading',  risk: 'CRITICAL' },
              { scenario: 'Platform closure at NORTH',  impact: '+2.1 min rerouting',  risk: 'MEDIUM' },
            ].map((s, i) => (
              <div key={i} style={{
                padding: '10px 12px', marginBottom: 8,
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)', fontSize: 11,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ color: 'var(--text-primary)' }}>{s.scenario}</span>
                  <span className={`badge ${s.risk === 'CRITICAL' ? 'badge-rose' : s.risk === 'HIGH' ? 'badge-amber' : 'badge-blue'}`}>
                    {s.risk}
                  </span>
                </div>
                <div style={{ color: 'var(--color-rose)', fontFamily: 'var(--font-mono)' }}>{s.impact}</div>
                <button className="btn btn-ghost btn-sm" style={{ marginTop: 6, fontSize: 10 }}>▶ Simulate</button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
