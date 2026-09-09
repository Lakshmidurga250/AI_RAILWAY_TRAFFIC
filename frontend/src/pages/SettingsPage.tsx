import React, { useState } from 'react';

// ─── Toggle Switch ────────────────────────────────────────────
function Toggle({ checked, onChange, id }: { checked: boolean; onChange: (v: boolean) => void; id?: string }) {
  return (
    <button
      id={id}
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      style={{
        width: 40, height: 22, borderRadius: 99, border: 'none', cursor: 'pointer',
        background: checked ? 'var(--color-cyan)' : 'var(--color-border)',
        transition: 'background 0.2s', position: 'relative', flexShrink: 0,
        boxShadow: checked ? '0 0 10px rgba(0,229,255,0.35)' : 'none',
      }}
    >
      <span style={{
        position: 'absolute', top: 3, left: checked ? 21 : 3,
        width: 16, height: 16, borderRadius: '50%', background: '#fff',
        transition: 'left 0.2s', display: 'block',
        boxShadow: '0 1px 4px rgba(0,0,0,0.3)',
      }} />
    </button>
  );
}

// ─── Slider ───────────────────────────────────────────────────
function Slider({ value, min, max, step = 1, onChange, unit = '' }: {
  value: number; min: number; max: number; step?: number;
  onChange: (v: number) => void; unit?: string;
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        style={{
          flex: 1, accentColor: 'var(--color-cyan)',
          height: 4, cursor: 'pointer',
        }}
      />
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-cyan)', minWidth: 52, textAlign: 'right' }}>
        {value}{unit}
      </span>
    </div>
  );
}

// ─── Section ──────────────────────────────────────────────────
function SettingsSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{
        fontSize: 10, fontFamily: 'var(--font-mono)', textTransform: 'uppercase',
        letterSpacing: '1.5px', color: 'var(--text-muted)', marginBottom: 12,
        paddingBottom: 6, borderBottom: '1px solid var(--color-border)',
      }}>{title}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>{children}</div>
    </div>
  );
}

function SettingsRow({ label, desc, children }: { label: string; desc?: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16 }}>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 500 }}>{label}</div>
        {desc && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{desc}</div>}
      </div>
      <div style={{ flexShrink: 0, minWidth: 180, display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>{children}</div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────
export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'simulation' | 'display' | 'notifications' | 'api' | 'users' | 'system'>('simulation');

  // Simulation settings
  const [simSpeed, setSimSpeed]           = useState(1);
  const [conflictSens, setConflictSens]   = useState(75);
  const [autoResolve, setAutoResolve]     = useState(true);
  const [ecoMode, setEcoMode]             = useState(true);
  const [headwayMin, setHeadwayMin]       = useState(3);
  const [maxTrains, setMaxTrains]         = useState(12);
  const [physicsAccuracy, setPhysicsAcc]  = useState(85);

  // Display settings
  const [darkMode]                        = useState(true);
  const [animations, setAnimations]       = useState(true);
  const [glowEffects, setGlowEffects]     = useState(true);
  const [compactMode, setCompactMode]     = useState(false);
  const [showCoords, setShowCoords]       = useState(false);
  const [refreshRate, setRefreshRate]     = useState(4);
  const [mapStyle, setMapStyle]           = useState<'satellite' | 'schematic' | 'topology'>('schematic');

  // Notification settings
  const [criticalAlerts, setCriticalAlerts] = useState(true);
  const [delayAlerts, setDelayAlerts]       = useState(true);
  const [systemAlerts, setSystemAlerts]     = useState(false);
  const [soundEnabled, setSoundEnabled]     = useState(false);
  const [delayThresh, setDelayThresh]       = useState(5);
  const [alertEmail, setAlertEmail]         = useState('dispatcher@railway-ai.internal');

  // API settings
  const [wsEnabled, setWsEnabled]           = useState(true);
  const [metricsEnabled, setMetricsEnabled] = useState(true);
  const [rateLimitEnabled, setRateLimitEnabled] = useState(true);
  const [corsMode, setCorsMode]             = useState<'strict' | 'permissive'>('strict');
  const [apiKey]                            = useState('rky_prod_a1b2c3d4e5f6g7h8i9j0');

  // Save state
  const [saving, setSaving]               = useState(false);
  const [saved, setSaved]                 = useState(false);

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    }, 1000);
  };

  const USERS = [
    { name: 'Lead Railway Dispatcher', username: 'admin', role: 'admin',      status: 'ACTIVE',   last: '16:08 today' },
    { name: 'Ops Controller',          username: 'ops01', role: 'operator',   status: 'ACTIVE',   last: '15:42 today' },
    { name: 'Signal Engineer',         username: 'sig01', role: 'viewer',     status: 'ACTIVE',   last: '14:20 today' },
    { name: 'Maintenance Tech',        username: 'mnt01', role: 'viewer',     status: 'INACTIVE', last: '2 days ago' },
  ];

  const roleColor: Record<string, string> = {
    admin: '#a855f7', operator: '#00e5ff', viewer: '#fbbf24',
  };

  return (
    <div>
      {/* Header */}
      <div className="section-header mb-lg">
        <div className="section-dot" style={{ background: 'var(--color-amber)' }} />
        <h2>System Settings</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          {saved && <span className="badge badge-emerald" style={{ animation: 'fadeIn 0.3s' }}>✓ Saved</span>}
          <button
            id="settings-save-btn"
            className={`btn ${saving ? 'btn-outline' : 'btn-primary'}`}
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? '⟳ Saving…' : '💾 Save Changes'}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 24 }}>
        {/* Left nav */}
        <div style={{ width: 180, flexShrink: 0 }}>
          <div style={{
            background: 'var(--color-bg-surface)', borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--color-border)', overflow: 'hidden',
          }}>
            {[
              { id: 'simulation',    icon: '🔬', label: 'Simulation' },
              { id: 'display',       icon: '🖥',  label: 'Display' },
              { id: 'notifications', icon: '🔔', label: 'Alerts' },
              { id: 'api',           icon: '🔌', label: 'API & WebSocket' },
              { id: 'users',         icon: '👥', label: 'Users' },
              { id: 'system',        icon: '⚙️', label: 'System Info' },
            ].map(t => (
              <button
                key={t.id}
                id={`settings-tab-${t.id}`}
                onClick={() => setActiveTab(t.id as any)}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 10,
                  padding: '11px 16px', border: 'none', cursor: 'pointer', textAlign: 'left',
                  fontSize: 13, fontWeight: 500, transition: 'all 0.12s',
                  background: activeTab === t.id ? 'var(--color-bg-active)' : 'transparent',
                  color: activeTab === t.id ? 'var(--color-cyan)' : 'var(--text-secondary)',
                  borderLeft: `3px solid ${activeTab === t.id ? 'var(--color-cyan)' : 'transparent'}`,
                }}
                onMouseEnter={e => { if (activeTab !== t.id) { e.currentTarget.style.background = 'var(--color-bg-hover)'; e.currentTarget.style.color = 'var(--text-primary)'; } }}
                onMouseLeave={e => { if (activeTab !== t.id) { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)'; } }}
              >
                <span style={{ fontSize: 15 }}>{t.icon}</span>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Right content */}
        <div style={{ flex: 1 }}>
          {/* ── SIMULATION ── */}
          {activeTab === 'simulation' && (
            <div className="card">
              <div className="card-title mb-lg">Simulation Engine Configuration</div>

              <SettingsSection title="Simulation Core">
                <SettingsRow label="Default Time Acceleration" desc="Simulation speed multiplier at startup">
                  <div style={{ width: '100%' }}>
                    <Slider value={simSpeed} min={1} max={50} step={1} onChange={setSimSpeed} unit="×" />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>
                      <span>1× (real-time)</span><span>50× (max)</span>
                    </div>
                  </div>
                </SettingsRow>
                <SettingsRow label="Maximum Concurrent Trains" desc="Hard cap on number of active train agents">
                  <div style={{ width: '100%' }}>
                    <Slider value={maxTrains} min={2} max={50} step={1} onChange={setMaxTrains} unit="" />
                  </div>
                </SettingsRow>
                <SettingsRow label="Minimum Headway" desc="Enforced minimum spacing between trains">
                  <div style={{ width: '100%' }}>
                    <Slider value={headwayMin} min={1} max={15} step={0.5} onChange={setHeadwayMin} unit=" min" />
                  </div>
                </SettingsRow>
                <SettingsRow label="Physics Accuracy" desc="Trade-off between realism and performance">
                  <div style={{ width: '100%' }}>
                    <Slider value={physicsAccuracy} min={10} max={100} step={5} onChange={setPhysicsAcc} unit="%" />
                  </div>
                </SettingsRow>
              </SettingsSection>

              <SettingsSection title="Conflict Detection">
                <SettingsRow label="Detection Sensitivity" desc="Higher = earlier warning, more false positives">
                  <div style={{ width: '100%' }}>
                    <Slider value={conflictSens} min={10} max={100} step={5} onChange={setConflictSens} unit="%" />
                  </div>
                </SettingsRow>
                <SettingsRow label="Auto-Resolve Conflicts" desc="AI automatically applies resolution strategies">
                  <Toggle id="toggle-auto-resolve" checked={autoResolve} onChange={setAutoResolve} />
                </SettingsRow>
              </SettingsSection>

              <SettingsSection title="Optimization">
                <SettingsRow label="Eco-Driving Mode" desc="Enable energy-optimal speed profiles by default">
                  <Toggle id="toggle-eco-mode" checked={ecoMode} onChange={setEcoMode} />
                </SettingsRow>
                <SettingsRow label="Optimization Algorithm">
                  <select className="form-select" style={{ fontSize: 12 }} id="opt-algorithm-select">
                    <option>Multi-Objective (default)</option>
                    <option>Pareto + Weighted Sum</option>
                    <option>Genetic Algorithm</option>
                    <option>Particle Swarm</option>
                  </select>
                </SettingsRow>
              </SettingsSection>
            </div>
          )}

          {/* ── DISPLAY ── */}
          {activeTab === 'display' && (
            <div className="card">
              <div className="card-title mb-lg">Display & Interface Preferences</div>

              <SettingsSection title="Theme">
                <SettingsRow label="Dark Mode" desc="Dark glassmorphism theme (restart to apply)">
                  <Toggle id="toggle-dark-mode" checked={darkMode} onChange={() => {}} />
                </SettingsRow>
                <SettingsRow label="Glow Effects" desc="Neon glow on active elements and badges">
                  <Toggle id="toggle-glow" checked={glowEffects} onChange={setGlowEffects} />
                </SettingsRow>
                <SettingsRow label="Micro-Animations" desc="Smooth transitions and hover effects">
                  <Toggle id="toggle-animations" checked={animations} onChange={setAnimations} />
                </SettingsRow>
                <SettingsRow label="Compact Mode" desc="Reduce padding for information density">
                  <Toggle id="toggle-compact" checked={compactMode} onChange={setCompactMode} />
                </SettingsRow>
              </SettingsSection>

              <SettingsSection title="Map">
                <SettingsRow label="Map Style">
                  <div style={{ display: 'flex', gap: 6 }}>
                    {(['schematic', 'satellite', 'topology'] as const).map(s => (
                      <button key={s} onClick={() => setMapStyle(s)}
                        style={{
                          padding: '4px 10px', borderRadius: 6, border: 'none', cursor: 'pointer',
                          fontSize: 11, fontFamily: 'var(--font-mono)', textTransform: 'capitalize',
                          background: mapStyle === s ? 'var(--color-cyan)' : 'var(--color-bg-elevated)',
                          color: mapStyle === s ? '#000' : 'var(--text-secondary)',
                          transition: 'all 0.15s',
                        }}>{s}</button>
                    ))}
                  </div>
                </SettingsRow>
                <SettingsRow label="Show GPS Coordinates" desc="Display lat/lng on train hover">
                  <Toggle id="toggle-coords" checked={showCoords} onChange={setShowCoords} />
                </SettingsRow>
              </SettingsSection>

              <SettingsSection title="Data Refresh">
                <SettingsRow label="Poll Interval" desc="How often the frontend fetches new data">
                  <div style={{ width: '100%' }}>
                    <Slider value={refreshRate} min={1} max={30} step={1} onChange={setRefreshRate} unit=" s" />
                    <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>Current: every {refreshRate}s</div>
                  </div>
                </SettingsRow>
              </SettingsSection>
            </div>
          )}

          {/* ── NOTIFICATIONS ── */}
          {activeTab === 'notifications' && (
            <div className="card">
              <div className="card-title mb-lg">Alert & Notification Settings</div>

              <SettingsSection title="Alert Types">
                <SettingsRow label="Critical Conflict Alerts" desc="CRITICAL and HIGH severity conflict notifications">
                  <Toggle id="toggle-critical-alerts" checked={criticalAlerts} onChange={setCriticalAlerts} />
                </SettingsRow>
                <SettingsRow label="Delay Threshold Alerts" desc={`Alert when train delay exceeds threshold`}>
                  <Toggle id="toggle-delay-alerts" checked={delayAlerts} onChange={setDelayAlerts} />
                </SettingsRow>
                <SettingsRow label="System & Maintenance Alerts" desc="Backend events, model reload, engine restart">
                  <Toggle id="toggle-system-alerts" checked={systemAlerts} onChange={setSystemAlerts} />
                </SettingsRow>
                <SettingsRow label="Sound Notifications" desc="Play audio on CRITICAL severity events">
                  <Toggle id="toggle-sound" checked={soundEnabled} onChange={setSoundEnabled} />
                </SettingsRow>
              </SettingsSection>

              <SettingsSection title="Thresholds">
                <SettingsRow label="Delay Alert Threshold" desc="Alert when delay exceeds this value">
                  <div style={{ width: '100%' }}>
                    <Slider value={delayThresh} min={1} max={30} step={1} onChange={setDelayThresh} unit=" min" />
                  </div>
                </SettingsRow>
              </SettingsSection>

              <SettingsSection title="Email Notifications">
                <SettingsRow label="Alert Email Address" desc="Receive critical alerts via email">
                  <input
                    className="form-input"
                    type="email"
                    value={alertEmail}
                    onChange={e => setAlertEmail(e.target.value)}
                    style={{ fontSize: 12, width: '100%' }}
                    id="alert-email-input"
                  />
                </SettingsRow>
                <SettingsRow label="Email Frequency">
                  <select className="form-select" style={{ fontSize: 12 }} id="email-freq-select">
                    <option>Immediate (per event)</option>
                    <option>Digest (every 15 min)</option>
                    <option>Hourly digest</option>
                    <option>Disabled</option>
                  </select>
                </SettingsRow>
              </SettingsSection>
            </div>
          )}

          {/* ── API ── */}
          {activeTab === 'api' && (
            <div className="card">
              <div className="card-title mb-lg">API, WebSocket & Integration Settings</div>

              <SettingsSection title="REST API">
                <SettingsRow label="API Version">
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-cyan)' }}>v2.4.0</span>
                </SettingsRow>
                <SettingsRow label="Rate Limiting" desc="Enforce per-IP request limits">
                  <Toggle id="toggle-rate-limit" checked={rateLimitEnabled} onChange={setRateLimitEnabled} />
                </SettingsRow>
                <SettingsRow label="CORS Policy">
                  <div style={{ display: 'flex', gap: 6 }}>
                    {(['strict', 'permissive'] as const).map(s => (
                      <button key={s} onClick={() => setCorsMode(s)}
                        style={{
                          padding: '4px 12px', borderRadius: 6, border: 'none', cursor: 'pointer',
                          fontSize: 11, fontFamily: 'var(--font-mono)', textTransform: 'capitalize',
                          background: corsMode === s ? (s === 'strict' ? 'var(--color-emerald)' : 'var(--color-amber)') : 'var(--color-bg-elevated)',
                          color: corsMode === s ? '#000' : 'var(--text-secondary)',
                          transition: 'all 0.15s',
                        }}>{s}</button>
                    ))}
                  </div>
                </SettingsRow>
                <SettingsRow label="API Key" desc="Used for external integrations (read-only here)">
                  <div style={{
                    fontFamily: 'var(--font-mono)', fontSize: 11, padding: '6px 10px',
                    background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--color-border)', color: 'var(--color-amber)',
                    letterSpacing: '1px',
                  }}>
                    {apiKey.slice(0, 12)}••••••••••••
                  </div>
                </SettingsRow>
              </SettingsSection>

              <SettingsSection title="WebSocket">
                <SettingsRow label="WebSocket Server" desc="Real-time bidirectional event stream">
                  <Toggle id="toggle-ws" checked={wsEnabled} onChange={setWsEnabled} />
                </SettingsRow>
                <SettingsRow label="WS Endpoint">
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--color-cyan)' }}>ws://localhost:8000/ws</span>
                </SettingsRow>
              </SettingsSection>

              <SettingsSection title="Prometheus Metrics">
                <SettingsRow label="Metrics Endpoint" desc="Expose /metrics for Prometheus scraping">
                  <Toggle id="toggle-metrics" checked={metricsEnabled} onChange={setMetricsEnabled} />
                </SettingsRow>
                <SettingsRow label="Metrics URL">
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                    {metricsEnabled ? 'http://localhost:8000/metrics' : '— disabled —'}
                  </span>
                </SettingsRow>
              </SettingsSection>
            </div>
          )}

          {/* ── USERS ── */}
          {activeTab === 'users' && (
            <div className="card">
              <div className="card-title mb-md">User Management</div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 16 }}>
                <button className="btn btn-primary" style={{ fontSize: 12 }} id="add-user-btn">
                  + Add User
                </button>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                      {['Full Name', 'Username', 'Role', 'Status', 'Last Active', 'Actions'].map(h => (
                        <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 500 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {USERS.map((u, i) => (
                      <tr key={i}
                        style={{ borderBottom: '1px solid rgba(30,45,68,0.5)' }}
                        onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
                        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                        <td style={{ padding: '12px 12px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <div style={{
                              width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
                              background: `linear-gradient(135deg, ${roleColor[u.role]}44, ${roleColor[u.role]}22)`,
                              border: `1px solid ${roleColor[u.role]}60`,
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: 13, color: roleColor[u.role], fontWeight: 700,
                            }}>
                              {u.name.charAt(0)}
                            </div>
                            <span style={{ fontWeight: 500, fontSize: 13 }}>{u.name}</span>
                          </div>
                        </td>
                        <td style={{ padding: '12px 12px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-cyan)' }}>{u.username}</td>
                        <td style={{ padding: '12px 12px' }}>
                          <span style={{
                            fontSize: 10, padding: '2px 8px', borderRadius: 99, fontFamily: 'var(--font-mono)',
                            background: roleColor[u.role] + '22', color: roleColor[u.role],
                            border: `1px solid ${roleColor[u.role]}40`,
                          }}>{u.role}</span>
                        </td>
                        <td style={{ padding: '12px 12px' }}>
                          <span className={`badge ${u.status === 'ACTIVE' ? 'badge-emerald' : 'badge-muted'}`}>{u.status}</span>
                        </td>
                        <td style={{ padding: '12px 12px', fontSize: 11, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{u.last}</td>
                        <td style={{ padding: '12px 12px' }}>
                          <div style={{ display: 'flex', gap: 6 }}>
                            <button className="btn btn-outline" style={{ fontSize: 10, padding: '4px 10px' }}>Edit</button>
                            {u.username !== 'admin' && (
                              <button className="btn" style={{ fontSize: 10, padding: '4px 10px', background: 'rgba(255,77,109,0.1)', color: 'var(--color-rose)', border: '1px solid rgba(255,77,109,0.3)' }}>
                                Remove
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── SYSTEM INFO ── */}
          {activeTab === 'system' && (
            <div>
              <div className="grid-2 mb-lg">
                {[
                  { title: 'Application', rows: [
                    { k: 'Name', v: 'RailOpt AI Control Center' },
                    { k: 'Version', v: 'v2.4.0' },
                    { k: 'Build', v: 'prod-2026-09-09-stable' },
                    { k: 'Environment', v: 'PRODUCTION' },
                    { k: 'License', v: 'Enterprise' },
                  ]},
                  { title: 'Backend Runtime', rows: [
                    { k: 'Framework', v: 'FastAPI 0.111' },
                    { k: 'Python', v: '3.12.4' },
                    { k: 'Database', v: 'SQLite 3.45 (railway_ai.db)' },
                    { k: 'ORM', v: 'SQLAlchemy 2.0' },
                    { k: 'Auth', v: 'JWT / RBAC' },
                  ]},
                  { title: 'Frontend Runtime', rows: [
                    { k: 'Framework', v: 'React 18.3 + Vite' },
                    { k: 'Language', v: 'TypeScript 5.4' },
                    { k: 'CSS', v: 'Vanilla CSS (41 KB)' },
                    { k: 'Fonts', v: 'Inter + JetBrains Mono + Orbitron' },
                  ]},
                  { title: 'AI / ML Stack', rows: [
                    { k: 'Delay Prediction', v: 'GBM + LSTM (94.2% acc)' },
                    { k: 'RL Dispatcher', v: 'PPO MARL (multi-agent)' },
                    { k: 'Explainability', v: 'SHAP + LIME (XAI)' },
                    { k: 'Optimization', v: 'Multi-Obj + PSO + Dijkstra/A*' },
                  ]},
                ].map((section, i) => (
                  <div key={i} className="card">
                    <div className="card-title mb-md">{section.title}</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {section.rows.map((r, j) => (
                        <div key={j} className="flex justify-between" style={{ fontSize: 12 }}>
                          <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>{r.k}</span>
                          <span style={{ color: 'var(--text-primary)', textAlign: 'right', maxWidth: 200 }}>{r.v}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Danger Zone */}
              <div className="card" style={{ border: '1px solid rgba(255,77,109,0.3)', background: 'rgba(255,77,109,0.03)' }}>
                <div className="card-title mb-md" style={{ color: 'var(--color-rose)' }}>⚠ Danger Zone</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {[
                    { label: 'Reset All Conflicts',   desc: 'Clear active conflict log — irreversible', btn: 'Reset Conflicts' },
                    { label: 'Restart Simulation',    desc: 'Stop all trains and reinitialise the engine', btn: 'Restart Engine' },
                    { label: 'Flush Analytics Cache', desc: 'Clear all KPI and trend data caches', btn: 'Flush Cache' },
                    { label: 'Factory Reset',         desc: 'Restore all settings to defaults', btn: 'Factory Reset' },
                  ].map((a, i) => (
                    <div key={i} className="flex justify-between items-center" style={{ padding: '10px 0', borderBottom: i < 3 ? '1px solid rgba(255,77,109,0.1)' : 'none' }}>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 500 }}>{a.label}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{a.desc}</div>
                      </div>
                      <button className="btn" style={{
                        fontSize: 11, padding: '6px 14px', flexShrink: 0,
                        background: 'rgba(255,77,109,0.1)', color: 'var(--color-rose)',
                        border: '1px solid rgba(255,77,109,0.35)', borderRadius: 'var(--radius-sm)',
                      }}>
                        {a.btn}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
