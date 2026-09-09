import React, { useEffect, useRef } from 'react';
import type { AppState } from '../App';
import type { Train, Conflict, KPIData } from '../types';

interface DashboardPageProps {
  state: AppState;
  onSimControl: (action: 'start' | 'pause' | 'stop' | 'step') => void;
}

// ─── KPI Card ──────────────────────────────────────────────────
interface KpiCardProps {
  label: string;
  value: string | number;
  unit?: string;
  color: string;
  icon: string;
  delta?: number;
  deltaLabel?: string;
  sparkData?: number[];
}

function KpiCard({ label, value, unit, color, icon, delta, deltaLabel, sparkData }: KpiCardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || !sparkData?.length) return;
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;
    const W = canvasRef.current.width;
    const H = canvasRef.current.height;
    ctx.clearRect(0, 0, W, H);

    const min = Math.min(...sparkData);
    const max = Math.max(...sparkData);
    const range = max - min || 1;

    ctx.beginPath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    sparkData.forEach((v, i) => {
      const x = (i / (sparkData.length - 1)) * W;
      const y = H - ((v - min) / range) * (H - 4) - 2;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Fill area
    ctx.lineTo(W, H);
    ctx.lineTo(0, H);
    ctx.closePath();
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, color + '33');
    grad.addColorStop(1, color + '00');
    ctx.fillStyle = grad;
    ctx.fill();
  }, [sparkData, color]);

  return (
    <div className="kpi-card" style={{ '--kpi-color': color } as React.CSSProperties}>
      <div className="flex items-center justify-between mb-sm">
        <div className="kpi-label">{label}</div>
        <span style={{ fontSize: 18, opacity: 0.8 }}>{icon}</span>
      </div>
      <div className="kpi-value">
        {value}
        {unit && <span className="kpi-unit">{unit}</span>}
      </div>
      {delta !== undefined && (
        <div className={`kpi-delta ${delta >= 0 ? 'positive' : 'negative'}`}>
          <span>{delta >= 0 ? '▲' : '▼'}</span>
          <span>{Math.abs(delta).toFixed(1)}{unit}</span>
          {deltaLabel && <span style={{ color: 'var(--text-muted)', marginLeft: 4 }}>{deltaLabel}</span>}
        </div>
      )}
      {sparkData && (
        <canvas
          ref={canvasRef}
          className="kpi-sparkline"
          width={140}
          height={32}
          style={{ width: '100%', height: 32, marginTop: 8 }}
        />
      )}
    </div>
  );
}

// ─── Mini Bar Chart ─────────────────────────────────────────────
function MiniBarChart({ data, color }: { data: { label: string; value: number; max?: number }[]; color: string }) {
  return (
    <div>
      {data.map((d, i) => (
        <div key={i} className="metric-bar-item">
          <div className="metric-bar-label" title={d.label}>{d.label}</div>
          <div className="metric-bar-track">
            <div
              className="metric-bar-fill"
              style={{
                width: `${Math.min(100, (d.value / (d.max || 100)) * 100)}%`,
                '--bar-color': color,
              } as React.CSSProperties}
            />
          </div>
          <div className="metric-bar-value">{d.value}</div>
        </div>
      ))}
    </div>
  );
}

// ─── Train Status Table ────────────────────────────────────────
function TrainStatusTable({ trains }: { trains: Train[] }) {
  const getStatusBadge = (status: string) => {
    const map: Record<string, string> = {
      running: 'badge-emerald',
      delayed: 'badge-amber',
      stopped: 'badge-rose',
      maintenance: 'badge-purple',
    };
    return map[status?.toLowerCase()] || 'badge-muted';
  };

  return (
    <div className="data-table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>Train #</th>
            <th>Type</th>
            <th>Speed (km/h)</th>
            <th>Delay (min)</th>
            <th>Location</th>
            <th>Priority</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {trains.length === 0 ? (
            <tr>
              <td colSpan={7} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                No trains loaded — start simulation
              </td>
            </tr>
          ) : (
            trains.map(t => (
              <tr
                key={t.id}
                className={
                  (t.current_delay_minutes || 0) > 5 ? 'row-danger' :
                  (t.current_delay_minutes || 0) > 2 ? 'row-warning' : ''
                }
              >
                <td className="font-mono text-cyan">{t.train_number}</td>
                <td>{t.train_type}</td>
                <td className="font-mono text-bright">{t.current_speed_kmh?.toFixed(0) ?? '—'}</td>
                <td className={`font-mono ${(t.current_delay_minutes || 0) > 2 ? 'text-amber' : 'text-emerald'}`}>
                  {(t.current_delay_minutes || 0) > 0 ? `+${t.current_delay_minutes?.toFixed(1)}` : '0.0'}
                </td>
                <td style={{ color: 'var(--text-secondary)', fontSize: 11 }}>
                  {t.current_station || t.next_station || '—'}
                </td>
                <td className="font-mono">
                  <span className={`badge ${t.priority > 3 ? 'badge-rose' : t.priority > 1 ? 'badge-amber' : 'badge-muted'}`}>
                    P{t.priority}
                  </span>
                </td>
                <td>
                  <span className={`badge ${getStatusBadge(t.status)}`}>{t.status}</span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// ─── Conflict List ─────────────────────────────────────────────
function ConflictList({ conflicts }: { conflicts: Conflict[] }) {
  if (conflicts.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>✅</div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>No active conflicts</div>
      </div>
    );
  }
  return (
    <div>
      {conflicts.slice(0, 8).map((c, i) => (
        <div key={i} className="alert-item critical mb-sm">
          <span className="alert-icon">⚠️</span>
          <div className="alert-content">
            <div className="alert-title">{String(c.conflict_type || 'CONFLICT').replace(/_/g, ' ')}</div>
            <div className="alert-desc">Trains: {Array.isArray(c.train_ids) ? c.train_ids.join(', ') : '—'}</div>
          </div>
          <span className={`badge ${c.severity === 'critical' ? 'badge-rose' : 'badge-amber'}`}>
            {c.severity || 'HIGH'}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Network Status Summary ────────────────────────────────────
function NetworkSummary({ trains, kpis }: { trains: Train[]; kpis: Partial<KPIData> }) {
  const lines = [
    { label: 'Line A (North–Central)', trains: 4, util: 78, color: 'var(--color-cyan)' },
    { label: 'Line B (East–West)',      trains: 3, util: 65, color: 'var(--color-emerald)' },
    { label: 'Line C (South Loop)',     trains: 2, util: 45, color: 'var(--color-purple)' },
    { label: 'Freight Corridor',        trains: 1, util: 30, color: 'var(--color-amber)' },
  ];

  return (
    <div>
      {lines.map((line, i) => (
        <div key={i} className="mb-md">
          <div className="flex items-center justify-between mb-xs">
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{line.label}</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)' }}>
              {line.trains} trains · {line.util}%
            </span>
          </div>
          <div className="progress-bar-wrapper">
            <div
              className="progress-bar-fill"
              style={{
                width: `${line.util}%`,
                '--progress-color': line.color,
              } as React.CSSProperties}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── AI Prediction Summary ─────────────────────────────────────
function AIPredictionSummary({ trains }: { trains: Train[] }) {
  const predictions = [
    { train: 'ICE-1401', risk: 'HIGH',   delay: 8.2, reason: 'Platform congestion at Node-C' },
    { train: 'RE-2205',  risk: 'MEDIUM', delay: 3.5, reason: 'Signal headway deficit' },
    { train: 'IC-3301',  risk: 'LOW',    delay: 1.2, reason: 'Minor speed restriction' },
  ];

  return (
    <div>
      <div className="card-title mb-md">AI Delay Predictions</div>
      {predictions.map((p, i) => (
        <div key={i} className="flex items-center gap-sm mb-md" style={{
          padding: '10px 12px',
          background: 'var(--color-bg-elevated)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
        }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--color-cyan)' }}>
              {p.train}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>{p.reason}</div>
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: 14,
            fontWeight: 700,
            color: p.risk === 'HIGH' ? 'var(--color-rose)' : p.risk === 'MEDIUM' ? 'var(--color-amber)' : 'var(--color-emerald)',
          }}>
            +{p.delay}m
          </div>
          <span className={`badge ${p.risk === 'HIGH' ? 'badge-rose' : p.risk === 'MEDIUM' ? 'badge-amber' : 'badge-emerald'}`}>
            {p.risk}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Main Dashboard Page ───────────────────────────────────────
export function DashboardPage({ state, onSimControl }: DashboardPageProps) {
  const { trains, conflicts, kpis } = state;

  // Spark data (simulate historical trend)
  const puncSpark = [95.2, 95.8, 96.1, 95.9, 96.4, 96.8, 97.1, 96.8];
  const delaySpark = [2.1, 1.9, 1.7, 2.0, 1.5, 1.4, 1.6, 1.4];
  const throughputSpark = [22, 23, 24, 23.5, 24.2, 24.5, 24.8, 24.5];

  return (
    <div>
      {/* Page header */}
      <div className="section-header mb-lg">
        <div className="section-dot" />
        <h2>Operations Dashboard</h2>
        <div style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
          Last updated: {state.lastUpdated?.toLocaleTimeString() || '—'}
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid-5 mb-lg">
        <KpiCard
          label="Punctuality Rate"
          value={kpis.punctuality_rate ?? 96.8}
          unit="%"
          color="var(--color-emerald)"
          icon="✅"
          delta={0.3}
          deltaLabel="vs yesterday"
          sparkData={puncSpark}
        />
        <KpiCard
          label="Avg Delay"
          value={(kpis.average_delay_minutes ?? 1.4).toFixed(1)}
          unit=" min"
          color="var(--color-cyan)"
          icon="⏱"
          delta={-0.2}
          deltaLabel="vs yesterday"
          sparkData={delaySpark}
        />
        <KpiCard
          label="Active Fleet"
          value={kpis.active_trains ?? trains.length}
          unit=" trains"
          color="var(--color-blue)"
          icon="🚄"
        />
        <KpiCard
          label="Active Conflicts"
          value={conflicts.length}
          color={conflicts.length > 0 ? 'var(--color-rose)' : 'var(--color-emerald)'}
          icon={conflicts.length > 0 ? '⚠️' : '✅'}
        />
        <KpiCard
          label="Throughput"
          value={(kpis.network_throughput_tph ?? 24.5).toFixed(1)}
          unit=" TPH"
          color="var(--color-purple)"
          icon="📈"
          sparkData={throughputSpark}
        />
      </div>

      {/* Main grid */}
      <div className="grid-2 mb-lg">
        {/* Fleet Status Table */}
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <div className="card-header">
            <div className="card-title">🚄 Live Fleet Telemetry</div>
            <div className="flex gap-sm">
              <span className="badge badge-emerald">
                {trains.filter(t => t.status === 'running').length} Running
              </span>
              <span className="badge badge-amber">
                {trains.filter(t => (t.current_delay_minutes || 0) > 2).length} Delayed
              </span>
            </div>
          </div>
          <TrainStatusTable trains={trains} />
        </div>
      </div>

      {/* Bottom grid */}
      <div className="grid-3">
        {/* Active Conflicts */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">⚠️ Active Conflicts</div>
            {conflicts.length > 0 && (
              <span className="badge badge-rose">{conflicts.length}</span>
            )}
          </div>
          <ConflictList conflicts={conflicts} />
        </div>

        {/* Network Line Utilization */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">🗺 Network Utilization</div>
          </div>
          <NetworkSummary trains={trains} kpis={kpis} />

          <div className="section-divider" />

          <div className="card-title mb-sm">Station Load</div>
          <MiniBarChart
            color="var(--color-cyan)"
            data={[
              { label: 'Central Hub',  value: 82, max: 100 },
              { label: 'North Term.',  value: 65, max: 100 },
              { label: 'East Jct.',   value: 71, max: 100 },
              { label: 'South Gate',  value: 48, max: 100 },
              { label: 'West Yard',   value: 33, max: 100 },
            ]}
          />
        </div>

        {/* AI Predictions */}
        <div className="card">
          <AIPredictionSummary trains={trains} />

          <div className="section-divider" />

          {/* RL Dispatcher status */}
          <div className="card-title mb-md">🤖 RL Dispatcher</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[
              { label: 'Decisions/sec', value: '127', color: 'var(--color-cyan)' },
              { label: 'Reward (avg)',   value: '+3.4', color: 'var(--color-emerald)' },
              { label: 'Safety Events', value: '0',   color: 'var(--color-emerald)' },
              { label: 'MARL Agents',   value: '6',   color: 'var(--color-purple)' },
            ].map((m, i) => (
              <div key={i} style={{
                background: 'var(--color-bg-elevated)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: '8px 10px',
              }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  {m.label}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: m.color, marginTop: 2 }}>
                  {m.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
