import React, { useState } from 'react';
import type { Train, KPIData } from '../types';

interface AIInsightsPageProps {
  trains: Train[];
  kpis: Partial<KPIData>;
}

export function AIInsightsPage({ trains, kpis }: AIInsightsPageProps) {
  const [activeTab, setActiveTab] = useState<'delay' | 'congestion' | 'rl' | 'xai'>('delay');

  return (
    <div>
      <div className="section-header mb-lg">
        <div className="section-dot" style={{ background: 'var(--color-purple)' }} />
        <h2>AI Intelligence Hub</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <span className="badge badge-emerald">Models Online</span>
          <span className="badge badge-cyan">GPU Active</span>
        </div>
      </div>

      {/* AI Status Cards */}
      <div className="grid-4 mb-lg">
        {[
          { label: 'Delay Prediction', acc: '94.2%', model: 'GBM + LSTM', status: 'green' },
          { label: 'Congestion Pred.', acc: '91.8%', model: 'Random Forest', status: 'green' },
          { label: 'RL Dispatcher',    acc: '+3.4',  model: 'PPO MARL',     status: 'blue' },
          { label: 'XAI Explainer',   acc: '0.87',  model: 'SHAP + LIME',  status: 'purple' },
        ].map((m, i) => (
          <div key={i} className="card">
            <div className="card-title mb-sm">{m.label}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 22, fontWeight: 700,
              color: m.status === 'green' ? 'var(--color-emerald)' : m.status === 'blue' ? 'var(--color-cyan)' : 'var(--color-purple)',
              marginBottom: 4 }}>
              {m.acc}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{m.model}</div>
            <div className="flex items-center gap-xs mt-sm">
              <div className="status-dot running pulse" />
              <span style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Live inference</span>
            </div>
          </div>
        ))}
      </div>

      <div className="tabs-header">
        {[
          { id: 'delay',      label: '⏱ Delay Prediction' },
          { id: 'congestion', label: '🔴 Congestion' },
          { id: 'rl',         label: '🤖 RL Dispatcher' },
          { id: 'xai',        label: '🔍 Explainability' },
        ].map(t => (
          <button key={t.id} className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id as any)}>
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'delay' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-title mb-md">Delay Risk Predictions</div>
            {[
              { train: 'ICE-1401', prob: 12, pred: 2.1, reason: 'Platform congestion', risk: 'LOW' },
              { train: 'RE-2201',  prob: 67, pred: 8.4, reason: 'Signal headway conflict', risk: 'HIGH' },
              { train: 'IC-3301',  prob: 34, pred: 3.8, reason: 'Junction bottleneck', risk: 'MEDIUM' },
              { train: 'FX-4401',  prob: 8,  pred: 1.2, reason: 'Grade restriction', risk: 'LOW' },
              { train: 'RE-2205',  prob: 78, pred: 11.2, reason: 'Following train conflict', risk: 'CRITICAL' },
            ].map((p, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 12px', marginBottom: 8,
                background: 'var(--color-bg-elevated)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--color-border)',
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-cyan)' }}>{p.train}</div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>{p.reason}</div>
                  <div style={{ marginTop: 6 }}>
                    <div className="progress-bar-wrapper" style={{ height: 4 }}>
                      <div className="progress-bar-fill" style={{
                        width: `${p.prob}%`,
                        '--progress-color': p.prob > 60 ? 'var(--color-rose)' : p.prob > 30 ? 'var(--color-amber)' : 'var(--color-emerald)',
                      } as React.CSSProperties} />
                    </div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700,
                    color: p.prob > 60 ? 'var(--color-rose)' : p.prob > 30 ? 'var(--color-amber)' : 'var(--color-emerald)' }}>
                    +{p.pred}m
                  </div>
                  <span className={`badge ${p.risk === 'CRITICAL' ? 'badge-rose' : p.risk === 'HIGH' ? 'badge-amber' : p.risk === 'MEDIUM' ? 'badge-blue' : 'badge-emerald'}`}>
                    {p.risk}
                  </span>
                </div>
              </div>
            ))}
          </div>
          <div className="card">
            <div className="card-title mb-md">Feature Importance (Top Delay Factors)</div>
            {[
              { feature: 'Headway Deficit',   importance: 0.34, color: 'var(--color-rose)' },
              { feature: 'Platform Occ.',     importance: 0.22, color: 'var(--color-amber)' },
              { feature: 'Signal Aspect',     importance: 0.18, color: 'var(--color-cyan)' },
              { feature: 'Train Priority',    importance: 0.12, color: 'var(--color-purple)' },
              { feature: 'Track Gradient',    importance: 0.08, color: 'var(--color-blue)' },
              { feature: 'Weather Index',     importance: 0.06, color: 'var(--color-emerald)' },
            ].map((f, i) => (
              <div key={i} className="metric-bar-item">
                <div className="metric-bar-label">{f.feature}</div>
                <div className="metric-bar-track">
                  <div className="metric-bar-fill" style={{
                    width: `${f.importance * 100}%`,
                    '--bar-color': f.color,
                  } as React.CSSProperties} />
                </div>
                <div className="metric-bar-value">{(f.importance * 100).toFixed(0)}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'rl' && (
        <div className="grid-2">
          <div className="card">
            <div className="card-title mb-md">PPO MARL Training Metrics</div>
            <div className="grid-2" style={{ gap: 8, marginBottom: 16 }}>
              {[
                { label: 'Episode Reward', value: '127.4', color: 'var(--color-emerald)' },
                { label: 'Policy Loss',    value: '0.023', color: 'var(--color-cyan)' },
                { label: 'Value Loss',     value: '0.041', color: 'var(--color-amber)' },
                { label: 'Entropy',        value: '1.84',  color: 'var(--color-purple)' },
                { label: 'Safety Violations', value: '0', color: 'var(--color-emerald)' },
                { label: 'Action Masks',   value: '12',    color: 'var(--color-blue)' },
              ].map((m, i) => (
                <div key={i} style={{
                  background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)', padding: '8px 10px',
                }}>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{m.label}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 20, fontWeight: 700, color: m.color }}>{m.value}</div>
                </div>
              ))}
            </div>
            <div className="card-title mb-sm">Agent Status</div>
            {['Agent-1 (North)', 'Agent-2 (East)', 'Agent-3 (Central)', 'Agent-4 (South)', 'Agent-5 (West)', 'Agent-6 (Yard)'].map((a, i) => (
              <div key={i} className="flex items-center gap-sm mb-xs" style={{ fontSize: 12 }}>
                <div className="status-dot running pulse" />
                <span style={{ color: 'var(--text-secondary)' }}>{a}</span>
                <span style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', color: 'var(--color-cyan)', fontSize: 11 }}>
                  R: +{(Math.random() * 5 + 20).toFixed(1)}
                </span>
              </div>
            ))}
          </div>
          <div className="card">
            <div className="card-title mb-md">Safety Shield Status</div>
            <div style={{ padding: '16px', background: 'rgba(0,245,160,0.08)', borderRadius: 'var(--radius-md)', border: '1px solid rgba(0,245,160,0.2)', marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-emerald)' }}>✅ ERTMS Level 2 Compliant</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 4 }}>Safety Shield active — 0 violations in last 1000 steps</div>
            </div>
            {[
              { check: 'Headway Enforcement',    ok: true },
              { check: 'Route Conflict Block',   ok: true },
              { check: 'Speed Limit Adherence',  ok: true },
              { check: 'Signal Override Guard',  ok: true },
              { check: 'Emergency Stop Trigger', ok: true },
            ].map((c, i) => (
              <div key={i} className="flex items-center gap-sm mb-sm" style={{ fontSize: 12 }}>
                <span>{c.ok ? '✅' : '❌'}</span>
                <span style={{ color: 'var(--text-secondary)' }}>{c.check}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'congestion' && (
        <div className="card">
          <div className="card-title mb-md">Network Congestion Heatmap</div>
          <div className="grid-auto" style={{ gridTemplateColumns: 'repeat(8, 1fr)', gap: 4 }}>
            {Array.from({ length: 48 }).map((_, i) => {
              const load = Math.random();
              const color = load > 0.8 ? '#ff4d6d' : load > 0.6 ? '#fbbf24' : load > 0.3 ? '#00e5ff' : '#1e2d44';
              return (
                <div key={i} className="heatmap-cell" style={{ background: color, opacity: 0.5 + load * 0.5 }}
                  title={`Section ${i + 1}: ${(load * 100).toFixed(0)}% load`} />
              );
            })}
          </div>
          <div className="flex gap-lg mt-md" style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>
            {[['#1e2d44', 'Low (<30%)'], ['#00e5ff', 'Moderate'], ['#fbbf24', 'High (>60%)'], ['#ff4d6d', 'Critical (>80%)']].map(([c, l]) => (
              <div key={l} className="flex items-center gap-xs">
                <div style={{ width: 12, height: 12, background: c, borderRadius: 2 }} />
                <span style={{ color: 'var(--text-secondary)' }}>{l}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'xai' && (
        <div className="card">
          <div className="card-title mb-md">SHAP Explanation — RE-2201 Delay (+8.4 min)</div>
          <div style={{ padding: '12px', background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)', marginBottom: 16, fontFamily: 'var(--font-mono)', fontSize: 11 }}>
            Model prediction: <span style={{ color: 'var(--color-rose)' }}>+8.4 min delay</span> (67% confidence)
          </div>
          {[
            { feature: 'Headway to following train: 2.1 min', shap: +3.2, dir: 'increase' },
            { feature: 'Platform occupation: 94%',            shap: +2.1, dir: 'increase' },
            { feature: 'Signal at YELLOW aspect',             shap: +1.8, dir: 'increase' },
            { feature: 'Train priority: P2 (medium)',         shap: -0.9, dir: 'decrease' },
            { feature: 'Speed: 142 km/h (near limit)',        shap: +0.6, dir: 'increase' },
            { feature: 'Weather: clear',                      shap: -0.4, dir: 'decrease' },
          ].map((s, i) => (
            <div key={i} className="flex items-center gap-sm mb-sm">
              <div style={{ flex: 1, fontSize: 11, color: 'var(--text-secondary)' }}>{s.feature}</div>
              <div style={{ width: 120, height: 12, background: 'var(--color-bg-elevated)', borderRadius: 6, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${Math.abs(s.shap) / 3.2 * 100}%`,
                  background: s.dir === 'increase' ? 'var(--color-rose)' : 'var(--color-emerald)',
                  borderRadius: 6,
                  float: s.dir === 'increase' ? 'right' : 'left',
                }} />
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, width: 50, textAlign: 'right',
                color: s.dir === 'increase' ? 'var(--color-rose)' : 'var(--color-emerald)' }}>
                {s.dir === 'increase' ? '+' : ''}{s.shap.toFixed(1)}m
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
