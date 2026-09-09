import React, { useEffect, useRef, useState } from 'react';
import type { AppState } from '../App';

interface AnalyticsPageProps {
  state: AppState;
}

// ─── Bar Chart (canvas) ───────────────────────────────────────
interface BarChartProps {
  data: { label: string; value: number; value2?: number }[];
  color?: string;
  color2?: string;
  height?: number;
  maxValue?: number;
}

function BarChart({ data, color = '#00e5ff', color2, height = 120, maxValue }: BarChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.offsetWidth || 400;
    const H = height;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, W, H);

    const max = maxValue ?? Math.max(...data.map(d => Math.max(d.value, d.value2 ?? 0)), 1);
    const padL = 8, padR = 8, padT = 8, padB = 28;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;
    const barGroupW = chartW / data.length;
    const hasTwo = !!color2;
    const gap = 3;
    const barW = hasTwo ? (barGroupW - gap * 3) / 2 : barGroupW - gap * 2;

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    ctx.lineWidth = 1;
    for (let i = 1; i <= 4; i++) {
      const y = padT + chartH - (i / 4) * chartH;
      ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    }

    data.forEach((d, i) => {
      const x = padL + i * barGroupW + gap;

      const drawBar = (val: number, bx: number, bw: number, col: string) => {
        const bh = (val / max) * chartH;
        const by = padT + chartH - bh;
        const grad = ctx.createLinearGradient(0, by, 0, padT + chartH);
        grad.addColorStop(0, col);
        grad.addColorStop(1, col + '33');
        ctx.fillStyle = grad;
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(bx, by, bw, bh, [3, 3, 0, 0]);
        else ctx.rect(bx, by, bw, bh);
        ctx.fill();
      };

      drawBar(d.value, x, barW, color);
      if (hasTwo && d.value2 !== undefined && color2) {
        drawBar(d.value2, x + barW + gap, barW, color2);
      }

      ctx.fillStyle = 'rgba(139,159,190,0.65)';
      ctx.font = '9px Inter, sans-serif';
      ctx.textAlign = 'center';
      const labelX = x + barW / 2 + (hasTwo ? barW / 2 + gap / 2 : 0);
      ctx.fillText(d.label, labelX, H - 8);
    });
  }, [data, color, color2, height, maxValue]);

  return <canvas ref={canvasRef} style={{ width: '100%', height, display: 'block' }} />;
}

// ─── Donut Chart ──────────────────────────────────────────────
interface DonutSegment { label: string; value: number; color: string; }
function DonutChart({ segments, size = 140, centerLabel = '' }: { segments: DonutSegment[]; size?: number; centerLabel?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, size, size);

    const total = segments.reduce((s, seg) => s + seg.value, 0) || 1;
    const cx = size / 2, cy = size / 2, r = size / 2 - 8, inner = r * 0.58;
    let angle = -Math.PI / 2;

    segments.forEach(seg => {
      const sweep = (seg.value / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, r, angle, angle + sweep);
      ctx.closePath();
      ctx.fillStyle = seg.color;
      ctx.fill();
      angle += sweep;
    });

    ctx.beginPath(); ctx.arc(cx, cy, inner, 0, Math.PI * 2);
    ctx.fillStyle = '#080d1a'; ctx.fill();

    ctx.fillStyle = '#f0f6ff';
    ctx.font = `bold 18px Inter, sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(centerLabel || String(total), cx, cy - 8);
    ctx.fillStyle = '#556273'; ctx.font = '10px Inter, sans-serif';
    ctx.fillText('trains', cx, cy + 10);
  }, [segments, size, centerLabel]);
  return <canvas ref={canvasRef} style={{ width: size, height: size, display: 'block' }} />;
}

// ─── Sparkline ────────────────────────────────────────────────
function Sparkline({ data, color = '#00e5ff', height = 36 }: { data: number[]; color?: string; height?: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || data.length < 2) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.offsetWidth || 100;
    canvas.width = W * dpr; canvas.height = height * dpr;
    ctx.scale(dpr, dpr); ctx.clearRect(0, 0, W, height);
    const mn = Math.min(...data), mx = Math.max(...data), rng = mx - mn || 1;
    ctx.beginPath(); ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.lineJoin = 'round';
    data.forEach((v, i) => {
      const x = (i / (data.length - 1)) * W;
      const y = height - ((v - mn) / rng) * (height - 6) - 3;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
    ctx.lineTo(W, height); ctx.lineTo(0, height); ctx.closePath();
    const grad = ctx.createLinearGradient(0, 0, 0, height);
    grad.addColorStop(0, color + '33'); grad.addColorStop(1, color + '00');
    ctx.fillStyle = grad; ctx.fill();
  }, [data, color, height]);
  return <canvas ref={canvasRef} style={{ width: '100%', height, display: 'block' }} />;
}

// ─── Main Component ───────────────────────────────────────────
export function AnalyticsPage({ state }: AnalyticsPageProps) {
  const { kpis, trains, conflicts } = state;
  const [activeTab, setActiveTab] = useState<'overview' | 'performance' | 'energy' | 'events'>('overview');

  const punctuality   = kpis.punctuality_rate ?? 96.8;
  const avgDelay      = kpis.average_delay_minutes ?? 1.4;
  const activeTrains  = kpis.active_trains ?? trains.length;
  const conflictCount = kpis.total_conflicts_active ?? conflicts.length;
  const throughput    = kpis.network_throughput_tph ?? 24.5;
  const energyKwh     = kpis.total_energy_kwh ?? 18240;
  const co2Saved      = kpis.co2_saved_kg ?? 1381;

  const hourlyPunctuality = [
    { label: '07:00', value: 91.2 }, { label: '08:00', value: 88.5 },
    { label: '09:00', value: 89.1 }, { label: '10:00', value: 94.3 },
    { label: '11:00', value: 95.8 }, { label: '12:00', value: 96.1 },
    { label: '13:00', value: 96.8 }, { label: '14:00', value: 95.4 },
    { label: '15:00', value: 94.9 }, { label: '16:00', value: 90.2 },
    { label: '17:00', value: 87.6 }, { label: '18:00', value: 88.9 },
  ];

  const energyData = [
    { label: '06:00', value: 1200, value2: 380 },
    { label: '08:00', value: 3400, value2: 950 },
    { label: '10:00', value: 2100, value2: 620 },
    { label: '12:00', value: 1950, value2: 590 },
    { label: '14:00', value: 2200, value2: 640 },
    { label: '16:00', value: 3800, value2: 1100 },
    { label: '18:00', value: 2900, value2: 870 },
  ];

  const onTime = Math.max(1, Math.round(activeTrains * (punctuality / 100)));
  const delayed = Math.max(0, activeTrains - onTime);
  const delaySegments: DonutSegment[] = [
    { label: 'On Time',     value: onTime,                              color: '#00f5a0' },
    { label: 'Minor',       value: Math.max(0, Math.round(delayed * 0.60)), color: '#fbbf24' },
    { label: 'Moderate',    value: Math.max(0, Math.round(delayed * 0.30)), color: '#f97316' },
    { label: 'Severe',      value: Math.max(0, Math.round(delayed * 0.10)), color: '#ff4d6d' },
  ].filter(s => s.value > 0);

  const stations = [
    { name: 'NORTH HUB',   trains: 3, occupancy: 78 },
    { name: 'CENTRAL',     trains: 5, occupancy: 92 },
    { name: 'EAST DEPOT',  trains: 2, occupancy: 45 },
    { name: 'WEST YARD',   trains: 1, occupancy: 31 },
    { name: 'SOUTH GATE',  trains: 2, occupancy: 56 },
    { name: 'NE JUNCTION', trains: 1, occupancy: 22 },
  ];

  const events = [
    { time: '16:08', type: 'CONFLICT', severity: 'HIGH',   msg: 'Head-on risk: ICE-1401 ↔ REG-2205 at CENTRAL' },
    { time: '16:05', type: 'RESOLVE',  severity: 'INFO',   msg: 'Conflict resolved: REG-2201 rerouted via EAST' },
    { time: '16:01', type: 'DELAY',    severity: 'MEDIUM', msg: 'ICE-1402 +4.2 min — signal queue at NE JUNCTION' },
    { time: '15:58', type: 'ENERGY',   severity: 'INFO',   msg: 'Eco-drive active for 4 trains — 120 kWh saved' },
    { time: '15:52', type: 'CONFLICT', severity: 'MEDIUM', msg: 'Platform contention at CENTRAL — REG-2203 held' },
    { time: '15:47', type: 'SYSTEM',   severity: 'INFO',   msg: 'Simulation speed 5x by dispatcher' },
    { time: '15:41', type: 'DELAY',    severity: 'LOW',    msg: 'REG-2204 +1.8 min — minor signal at WEST' },
    { time: '15:35', type: 'RESOLVE',  severity: 'INFO',   msg: '3 trains rescheduled by optimizer' },
  ];

  const sevColor: Record<string, string> = {
    HIGH: '#ff4d6d', MEDIUM: '#fbbf24', LOW: '#00e5ff', INFO: '#00f5a0', CRITICAL: '#ff4d6d',
  };
  const typeIcon: Record<string, string> = {
    CONFLICT: '⚠️', RESOLVE: '✅', DELAY: '⏱', ENERGY: '⚡', SYSTEM: '🔧',
  };

  return (
    <div>
      {/* Header */}
      <div className="section-header mb-lg">
        <div className="section-dot" style={{ background: 'var(--color-indigo)' }} />
        <h2>Network Analytics</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="badge badge-emerald">Live Data</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)' }}>
            Updated {state.lastUpdated ? state.lastUpdated.toLocaleTimeString() : '—'}
          </span>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid-5 mb-lg">
        {[
          { label: 'Punctuality',      value: `${punctuality.toFixed(1)}%`, icon: '🎯', color: '#00f5a0', spark: [94.2,95.1,94.8,95.6,96.1,96.4,96.8,punctuality], delta: +0.3 },
          { label: 'Avg Delay',        value: `${avgDelay.toFixed(1)} min`, icon: '⏱',  color: '#fbbf24', spark: [2.1,1.9,2.4,1.8,1.6,1.2,1.4,avgDelay],         delta: -0.4 },
          { label: 'Throughput',       value: `${throughput.toFixed(1)} tph`,icon: '🚄', color: '#00e5ff', spark: [22.1,23.4,24.0,24.5,23.8,24.5,25.1,throughput],  delta: +0.6 },
          { label: 'Active Conflicts', value: String(conflictCount),         icon: '⚠️', color: conflictCount > 0 ? '#ff4d6d' : '#00f5a0', spark: [2,1,3,2,1,0,1,conflictCount] },
          { label: 'CO₂ Saved',        value: `${co2Saved} kg`,             icon: '🌿', color: '#00f5a0', spark: [980,1100,1200,1250,1320,1381,1381,co2Saved] },
        ].map((k, i) => (
          <div key={i} className="kpi-card" style={{ '--kpi-color': k.color } as React.CSSProperties}>
            <div className="flex items-center justify-between mb-sm">
              <div className="kpi-label">{k.label}</div>
              <span style={{ fontSize: 16, opacity: 0.8 }}>{k.icon}</span>
            </div>
            <div className="kpi-value" style={{ fontSize: 20 }}>{k.value}</div>
            {k.delta !== undefined && (
              <div className={`kpi-delta ${k.delta >= 0 ? 'positive' : 'negative'}`} style={{ fontSize: 10 }}>
                <span>{k.delta >= 0 ? '▲' : '▼'} {Math.abs(k.delta).toFixed(1)} vs prev</span>
              </div>
            )}
            <div style={{ marginTop: 8 }}><Sparkline data={k.spark} color={k.color} height={30} /></div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="tabs-header" style={{ marginBottom: 20 }}>
        {[
          { id: 'overview',    label: '📊 Overview' },
          { id: 'performance', label: '⏱ Performance' },
          { id: 'energy',      label: '⚡ Energy' },
          { id: 'events',      label: '📋 Event Log' },
        ].map(t => (
          <button key={t.id} className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id as any)}>{t.label}</button>
        ))}
      </div>

      {/* ── OVERVIEW ── */}
      {activeTab === 'overview' && (
        <>
          <div className="grid-2 mb-lg">
            {/* Delay Distribution Donut */}
            <div className="card">
              <div className="card-title mb-md">Delay Distribution</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                <DonutChart segments={delaySegments} size={140} centerLabel={String(activeTrains)} />
                <div style={{ flex: 1 }}>
                  {delaySegments.map((s, i) => (
                    <div key={i} className="flex items-center justify-between mb-sm" style={{ fontSize: 12 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 10, height: 10, borderRadius: '50%', background: s.color, flexShrink: 0 }} />
                        <span style={{ color: 'var(--text-secondary)' }}>{s.label}</span>
                      </div>
                      <span style={{ fontFamily: 'var(--font-mono)', color: s.color, fontWeight: 600 }}>{s.value}</span>
                    </div>
                  ))}
                  <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--color-border)' }}>
                    <div className="flex justify-between" style={{ fontSize: 11 }}>
                      <span style={{ color: 'var(--text-muted)' }}>On-time threshold</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: '#00f5a0' }}>≤ 3 min</span>
                    </div>
                    <div className="flex justify-between mt-sm" style={{ fontSize: 11 }}>
                      <span style={{ color: 'var(--text-muted)' }}>Monitored trains</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>{activeTrains}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Station Utilization */}
            <div className="card">
              <div className="card-title mb-md">Station Utilization</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {stations.map((s, i) => (
                  <div key={i}>
                    <div className="flex justify-between" style={{ fontSize: 11, marginBottom: 3 }}>
                      <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{s.name}</span>
                      <div style={{ display: 'flex', gap: 12 }}>
                        <span style={{ color: 'var(--color-cyan)' }}>{s.trains} trains</span>
                        <span style={{ color: s.occupancy > 80 ? '#ff4d6d' : s.occupancy > 60 ? '#fbbf24' : '#00f5a0' }}>{s.occupancy}%</span>
                      </div>
                    </div>
                    <div style={{ height: 6, background: 'var(--color-bg-elevated)', borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', width: `${s.occupancy}%`, borderRadius: 3, transition: 'width 0.6s ease',
                        background: s.occupancy > 80 ? 'linear-gradient(90deg,#fbbf24,#ff4d6d)' : s.occupancy > 60 ? '#fbbf24' : '#00f5a0',
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Hourly Punctuality Chart */}
          <div className="card mb-lg">
            <div className="card-title mb-md">Hourly Punctuality Rate (%)</div>
            <BarChart data={hourlyPunctuality} color="#00e5ff" height={140} maxValue={100} />
            <div className="flex justify-between mt-sm" style={{ fontSize: 10, color: 'var(--text-muted)' }}>
              <span>Peak: 13:00 — 96.8%</span>
              <span>Trough: 17:00 — 87.6% (evening rush)</span>
            </div>
          </div>

          {/* Network health mini-tiles */}
          <div className="grid-4">
            {[
              { label: 'Track Utilization',   value: '67%',   color: '#00e5ff',  desc: '18/27 tracks active' },
              { label: 'Platform Occupancy',  value: '44%',   color: '#fbbf24',  desc: '8/18 platforms used' },
              { label: 'Signal Health',       value: '99.1%', color: '#00f5a0',  desc: '2 signals degraded' },
              { label: 'Fleet Availability',  value: '87.5%', color: '#a855f7',  desc: '7/8 trains operational' },
            ].map((m, i) => (
              <div key={i} className="card" style={{ textAlign: 'center', padding: 20 }}>
                <div style={{ fontSize: 26, fontFamily: 'var(--font-mono)', fontWeight: 800, color: m.color, marginBottom: 4 }}>{m.value}</div>
                <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>{m.label}</div>
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{m.desc}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── PERFORMANCE ── */}
      {activeTab === 'performance' && (
        <>
          <div className="grid-2 mb-lg">
            <div className="card">
              <div className="card-title mb-md">Punctuality by Hour (%)</div>
              <BarChart data={hourlyPunctuality} color="#00e5ff" height={160} maxValue={100} />
              <div style={{ marginTop: 10, display: 'flex', gap: 16, fontSize: 11 }}>
                <span style={{ color: 'var(--text-muted)' }}>Daily avg: <span style={{ color: '#00e5ff', fontFamily: 'var(--font-mono)' }}>93.8%</span></span>
                <span style={{ color: 'var(--text-muted)' }}>Target: <span style={{ color: '#00f5a0', fontFamily: 'var(--font-mono)' }}>95.0%</span></span>
              </div>
            </div>
            <div className="card">
              <div className="card-title mb-md">Avg Delay by Train Type (min)</div>
              <BarChart
                data={[
                  { label: 'ICE', value: 0.8 }, { label: 'REG', value: 2.1 },
                  { label: 'FRT', value: 3.4 }, { label: 'EXP', value: 1.1 }, { label: 'LCL', value: 4.2 },
                ]}
                color="#fbbf24" height={160} maxValue={8}
              />
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8 }}>Freight & Local trains show highest delays</div>
            </div>
          </div>

          {/* Train table */}
          <div className="card">
            <div className="card-title mb-md">Train Performance Breakdown</div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                    {['Train', 'Type', 'Status', 'Delay', 'Speed', 'Energy (kWh)', 'Priority'].map(h => (
                      <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 10, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 500 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {trains.length > 0 ? trains.map((t, i) => (
                    <tr key={t.id}
                      style={{ borderBottom: '1px solid rgba(30,45,68,0.5)' }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#00e5ff' }}>{t.train_number}</td>
                      <td style={{ padding: '10px 12px', color: 'var(--text-secondary)' }}>{t.train_type}</td>
                      <td style={{ padding: '10px 12px' }}>
                        <span className={`badge ${t.status === 'RUNNING' ? 'badge-emerald' : t.status === 'DWELLING' ? 'badge-cyan' : 'badge-muted'}`}>{t.status}</span>
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: t.current_delay_minutes > 5 ? '#ff4d6d' : t.current_delay_minutes > 2 ? '#fbbf24' : '#00f5a0' }}>
                        {t.current_delay_minutes > 0 ? `+${t.current_delay_minutes.toFixed(1)}` : '✓'}
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{t.current_speed_kmh.toFixed(0)}</td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#00e5ff' }}>{t.cumulative_energy_kwh.toFixed(0)}</td>
                      <td style={{ padding: '10px 12px' }}>
                        <div style={{ display: 'flex', gap: 2 }}>
                          {Array.from({ length: 5 }).map((_, pi) => (
                            <div key={pi} style={{ width: 6, height: 6, borderRadius: '50%', background: pi < t.priority ? '#fbbf24' : 'var(--color-border)' }} />
                          ))}
                        </div>
                      </td>
                    </tr>
                  )) : (
                    <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                      <div style={{ fontSize: 28, marginBottom: 8 }}>🚄</div>Awaiting live train data…
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* ── ENERGY ── */}
      {activeTab === 'energy' && (
        <>
          <div className="grid-4 mb-lg">
            {[
              { label: 'Total Consumed',   value: `${(energyKwh / 1000).toFixed(1)} MWh`,       color: '#00e5ff', icon: '⚡' },
              { label: 'Regenerated',      value: `${(energyKwh * 0.28 / 1000).toFixed(1)} MWh`, color: '#00f5a0', icon: '♻️' },
              { label: 'CO₂ Saved',        value: `${co2Saved} kg`,                              color: '#00f5a0', icon: '🌿' },
              { label: 'Eco-Drive Active', value: `4 / ${activeTrains} trains`,                  color: '#fbbf24', icon: '🍃' },
            ].map((m, i) => (
              <div key={i} className="kpi-card" style={{ '--kpi-color': m.color } as React.CSSProperties}>
                <div className="flex items-center justify-between mb-sm">
                  <div className="kpi-label">{m.label}</div>
                  <span style={{ fontSize: 18 }}>{m.icon}</span>
                </div>
                <div className="kpi-value" style={{ fontSize: 20 }}>{m.value}</div>
              </div>
            ))}
          </div>

          <div className="card mb-lg">
            <div className="card-title mb-sm">Energy Consumption vs Regeneration (kWh)</div>
            <div style={{ display: 'flex', gap: 16, fontSize: 11, marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 10, height: 10, borderRadius: 2, background: '#00e5ff' }} /><span style={{ color: 'var(--text-secondary)' }}>Consumed</span></div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 10, height: 10, borderRadius: 2, background: '#00f5a0' }} /><span style={{ color: 'var(--text-secondary)' }}>Regenerated</span></div>
            </div>
            <BarChart data={energyData} color="#00e5ff" color2="#00f5a0" height={180} maxValue={4500} />
          </div>

          {/* Speed profiles */}
          <div className="card">
            <div className="card-title mb-md">Eco-Drive Speed Profiles</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {['ICE-1401', 'REG-2201', 'ICE-1402', 'REG-2202'].map((name, i) => {
                const profile = [120, 150, 160, 140, 100, 80, 60, 80, 120, 155, 160, 135, 80, 45].map(v => v + (i * 5 % 20));
                const savings = [12.4, 8.7, 14.2, 9.1][i];
                return (
                  <div key={i} style={{ padding: 12, background: 'var(--color-bg-elevated)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 11 }}>
                      <span style={{ fontFamily: 'var(--font-mono)', color: '#00e5ff' }}>{name}</span>
                      <span style={{ color: '#00f5a0' }}>-{savings} kWh saved</span>
                    </div>
                    <Sparkline data={profile} color="#00e5ff" height={40} />
                    <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 4 }}>← Distance →</div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* ── EVENTS ── */}
      {activeTab === 'events' && (
        <div className="card">
          <div className="card-title mb-md">Recent Network Events</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {events.map((ev, i) => (
              <div key={i}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: 12,
                  padding: '10px 12px', borderRadius: 'var(--radius-sm)',
                  background: i % 2 === 0 ? 'var(--color-bg-elevated)' : 'transparent',
                  cursor: 'default', transition: 'background 0.1s',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--color-bg-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? 'var(--color-bg-elevated)' : 'transparent')}>
                <span style={{ fontSize: 14, width: 20, textAlign: 'center', flexShrink: 0 }}>{typeIcon[ev.type] || '•'}</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', width: 42, flexShrink: 0, paddingTop: 2 }}>{ev.time}</span>
                <span style={{
                  fontSize: 9, padding: '2px 7px', borderRadius: 99, flexShrink: 0,
                  background: (sevColor[ev.severity] || '#00e5ff') + '20',
                  color: sevColor[ev.severity] || '#00e5ff',
                  border: `1px solid ${(sevColor[ev.severity] || '#00e5ff')}40`,
                  fontFamily: 'var(--font-mono)', alignSelf: 'flex-start', marginTop: 1,
                }}>{ev.severity}</span>
                <span style={{ fontSize: 12, color: 'var(--text-secondary)', flex: 1 }}>{ev.msg}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16, textAlign: 'center', fontSize: 11, color: 'var(--text-muted)' }}>
            Showing 8 recent events · Polling every 4 s
          </div>
        </div>
      )}
    </div>
  );
}
