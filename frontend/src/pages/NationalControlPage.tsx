import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

// ─── Types ────────────────────────────────────────────────────────────────────
interface ZoneKPI {
  zone: string;
  trains_running: number;
  on_time: number;
  delayed: number;
  cancelled: number;
  punctuality_pct: number;
  avg_delay_min: number;
  passenger_km: number;
  freight_tonne_km: number;
  energy_kwh: number;
  incidents: number;
  handoffs: number;
}

interface NationalKPI {
  zones_active: number;
  trains_running: number;
  trains_on_time: number;
  trains_delayed: number;
  trains_cancelled: number;
  national_punctuality_pct: number;
  passenger_km_today: number;
  freight_tonne_km_today: number;
  energy_kwh_consumed: number;
  incidents_today: number;
  zonal_handoffs_today: number;
  zones: ZoneKPI[];
}

interface Alert {
  alert_id: string;
  type: string;
  severity: string;
  zone: string;
  description: string;
  created_at: string;
}

interface FleetRecord {
  fleet_type: string;
  total: number;
  in_service: number;
  maintenance: number;
  utilisation_pct: number;
  avg_age_years: number;
}

// ─── Severity colours ─────────────────────────────────────────────────────────
const SEVERITY_COLOR: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#eab308',
  LOW:      '#3b82f6',
  WARNING:  '#f97316',
};

// ─── Zone colour heatmap (by punctuality) ─────────────────────────────────────
function punctualityColor(pct: number): string {
  if (pct >= 90) return '#22c55e';
  if (pct >= 80) return '#84cc16';
  if (pct >= 70) return '#eab308';
  if (pct >= 60) return '#f97316';
  return '#ef4444';
}

// ─── Mock data helper (used when backend is unavailable) ──────────────────────
function buildMockNational(): NationalKPI {
  const ZONES = [
    'NR','CR','WR','SR','SCR','ER','SER','NWR','NCR','ECR','NER','NFR','SWR','WCR','ECoR','SECR','MR','KR',
  ];
  const zones: ZoneKPI[] = ZONES.map(z => {
    const pct = 70 + Math.random() * 28;
    const running = Math.floor(30 + Math.random() * 120);
    const onTime  = Math.floor(running * (pct / 100));
    return {
      zone: z,
      trains_running: running,
      on_time: onTime,
      delayed: running - onTime,
      cancelled: Math.floor(Math.random() * 3),
      punctuality_pct: parseFloat(pct.toFixed(1)),
      avg_delay_min: parseFloat((Math.random() * 18).toFixed(1)),
      passenger_km: parseFloat((Math.random() * 4_000_000).toFixed(0)),
      freight_tonne_km: parseFloat((Math.random() * 2_000_000).toFixed(0)),
      energy_kwh: parseFloat((Math.random() * 800_000).toFixed(0)),
      incidents: Math.floor(Math.random() * 5),
      handoffs: Math.floor(Math.random() * 40),
    };
  });

  const totalRunning = zones.reduce((s, z) => s + z.trains_running, 0);
  const totalOnTime  = zones.reduce((s, z) => s + z.on_time, 0);
  const totalDelayed = zones.reduce((s, z) => s + z.delayed, 0);
  const totalCancelled = zones.reduce((s, z) => s + z.cancelled, 0);
  return {
    zones_active: ZONES.length,
    trains_running: totalRunning,
    trains_on_time: totalOnTime,
    trains_delayed: totalDelayed,
    trains_cancelled: totalCancelled,
    national_punctuality_pct: parseFloat(((totalOnTime / (totalOnTime + totalDelayed)) * 100).toFixed(1)),
    passenger_km_today: zones.reduce((s, z) => s + z.passenger_km, 0),
    freight_tonne_km_today: zones.reduce((s, z) => s + z.freight_tonne_km, 0),
    energy_kwh_consumed: zones.reduce((s, z) => s + z.energy_kwh, 0),
    incidents_today: zones.reduce((s, z) => s + z.incidents, 0),
    zonal_handoffs_today: zones.reduce((s, z) => s + z.handoffs, 0),
    zones,
  };
}

function buildMockAlerts(): Alert[] {
  const types = ['SIGNAL_FAILURE','TRACK_CLOSURE','DERAILMENT','FLOOD','OVERLOAD'];
  const zones = ['NR','CR','WR','SR','ECR'];
  return Array.from({ length: 4 }, (_, i) => ({
    alert_id: `NALRT_${String(i+1).padStart(5,'0')}`,
    type: types[i % types.length],
    severity: ['CRITICAL','HIGH','MEDIUM','HIGH'][i],
    zone: zones[i % zones.length],
    description: [
      'Signal failure at DLI – 12 trains affected',
      'Track closure NGP-BSL due to maintenance',
      'Slow order imposed MAS suburban corridor',
      'Flooding detected KGP-ADRA segment',
    ][i],
    created_at: new Date(Date.now() - (i+1)*720_000).toISOString(),
  }));
}

function buildMockFleet(): FleetRecord[] {
  return [
    { fleet_type:'WAP7 Electric Loco',  total:1200, in_service:950, maintenance:180, utilisation_pct:92.5, avg_age_years:8.2 },
    { fleet_type:'WDM3 Diesel Loco',    total:1800, in_service:1100, maintenance:500, utilisation_pct:76.3, avg_age_years:22.5 },
    { fleet_type:'WAG9 Freight Loco',   total:2400, in_service:1900, maintenance:380, utilisation_pct:87.7, avg_age_years:11.0 },
    { fleet_type:'LHB Coach',           total:45000,in_service:38000,maintenance:5000,utilisation_pct:88.9, avg_age_years:9.7 },
    { fleet_type:'Vande Bharat EMU',    total:450,  in_service:390,  maintenance:40, utilisation_pct:91.1, avg_age_years:2.8 },
    { fleet_type:'MEMU EMU',            total:1600, in_service:1350, maintenance:180, utilisation_pct:90.6, avg_age_years:12.4 },
  ];
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function MetricCard({ label, value, unit, color, icon }: {
  label: string; value: string | number; unit?: string; color?: string; icon?: string;
}) {
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 12,
      padding: '18px 22px',
      display: 'flex', flexDirection: 'column', gap: 6,
      minWidth: 140,
      boxShadow: '0 2px 12px rgba(0,0,0,0.18)',
    }}>
      <div style={{ fontSize: 22 }}>{icon}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || 'var(--text-primary)', letterSpacing: '-0.5px' }}>
        {value}<span style={{ fontSize: 13, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 4 }}>{unit}</span>
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
    </div>
  );
}

function ZoneRow({ zone, rank }: { zone: ZoneKPI; rank: number }) {
  const barWidth = `${zone.punctuality_pct}%`;
  const color = punctualityColor(zone.punctuality_pct);
  return (
    <tr style={{ borderBottom: '1px solid var(--color-border)', transition: 'background 0.15s' }}
        onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.04)')}
        onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}>
      <td style={{ padding: '10px 12px', color: 'var(--text-muted)', fontSize: 12 }}>{rank}</td>
      <td style={{ padding: '10px 12px', fontWeight: 700, fontSize: 13, fontFamily: 'var(--font-mono)' }}>
        {zone.zone}
      </td>
      <td style={{ padding: '10px 12px', fontSize: 12 }}>{zone.trains_running}</td>
      <td style={{ padding: '10px 12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ flex: 1, background: 'var(--color-border)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
            <div style={{ width: barWidth, background: color, height: '100%', borderRadius: 4, transition: 'width 0.6s ease' }} />
          </div>
          <span style={{ fontSize: 12, color, fontWeight: 700, minWidth: 42 }}>{zone.punctuality_pct}%</span>
        </div>
      </td>
      <td style={{ padding: '10px 12px', fontSize: 12, color: zone.avg_delay_min > 10 ? '#f97316' : 'var(--text-secondary)' }}>
        {zone.avg_delay_min}m
      </td>
      <td style={{ padding: '10px 12px', fontSize: 11, color: zone.incidents > 0 ? '#ef4444' : 'var(--text-muted)' }}>
        {zone.incidents}
      </td>
      <td style={{ padding: '10px 12px', fontSize: 11, color: 'var(--text-muted)' }}>
        {zone.handoffs}
      </td>
    </tr>
  );
}

function AlertRow({ alert }: { alert: Alert }) {
  const color = SEVERITY_COLOR[alert.severity] || '#888';
  const elapsed = Math.floor((Date.now() - new Date(alert.created_at).getTime()) / 60_000);
  return (
    <div style={{
      padding: '12px 16px',
      borderLeft: `3px solid ${color}`,
      background: `${color}11`,
      borderRadius: '0 8px 8px 0',
      marginBottom: 8,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: 11, fontWeight: 700, color, fontFamily: 'var(--font-mono)' }}>
            [{alert.severity}] {alert.type}
          </span>
          <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 8 }}>Zone: {alert.zone}</span>
        </div>
        <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{elapsed}m ago</span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>{alert.description}</div>
    </div>
  );
}

function FleetBar({ rec }: { rec: FleetRecord }) {
  const util = rec.utilisation_pct;
  const color = util >= 88 ? '#22c55e' : util >= 75 ? '#eab308' : '#ef4444';
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 12, fontWeight: 600 }}>{rec.fleet_type}</span>
        <span style={{ fontSize: 12, color, fontWeight: 700 }}>{util}%</span>
      </div>
      <div style={{ background: 'var(--color-border)', borderRadius: 4, height: 6, overflow: 'hidden' }}>
        <div style={{ width: `${util}%`, background: color, height: '100%', borderRadius: 4, transition: 'width 0.8s ease' }} />
      </div>
      <div style={{ display: 'flex', gap: 12, marginTop: 4, fontSize: 10, color: 'var(--text-muted)' }}>
        <span>In Service: {rec.in_service.toLocaleString()}</span>
        <span>Maintenance: {rec.maintenance.toLocaleString()}</span>
        <span>Age: {rec.avg_age_years}y</span>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export function NationalControlPage() {
  const [kpi, setKpi]         = useState<NationalKPI | null>(null);
  const [alerts, setAlerts]   = useState<Alert[]>([]);
  const [fleet, setFleet]     = useState<FleetRecord[]>([]);
  const [sortCol, setSortCol] = useState<keyof ZoneKPI>('punctuality_pct');
  const [sortAsc, setSortAsc] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const load = useCallback(async () => {
    try {
      // Try live backend; fall back to rich mock data
      const [ncrData, alertData, fleetData] = await Promise.all([
        (api as any).getNationalKPI?.().catch(() => null),
        (api as any).getNationalAlerts?.().catch(() => null),
        (api as any).getFleetUtilisation?.().catch(() => null),
      ]);
      setKpi(ncrData?.national_kpi || buildMockNational());
      setAlerts(alertData || buildMockAlerts());
      setFleet(fleetData || buildMockFleet());
    } catch {
      setKpi(buildMockNational());
      setAlerts(buildMockAlerts());
      setFleet(buildMockFleet());
    }
    setLastUpdate(new Date());
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [load]);

  const sortedZones = kpi
    ? [...kpi.zones].sort((a, b) => {
        const va = a[sortCol] as number;
        const vb = b[sortCol] as number;
        return sortAsc ? va - vb : vb - va;
      })
    : [];

  const handleSort = (col: keyof ZoneKPI) => {
    if (sortCol === col) setSortAsc(p => !p);
    else { setSortCol(col); setSortAsc(false); }
  };

  const thStyle = (col: keyof ZoneKPI): React.CSSProperties => ({
    padding: '10px 12px',
    fontSize: 11,
    color: sortCol === col ? 'var(--color-accent)' : 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.07em',
    cursor: 'pointer',
    userSelect: 'none',
    whiteSpace: 'nowrap',
  });

  if (!kpi) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 400 }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>🛰️</div>
          <div style={{ color: 'var(--text-muted)' }}>Loading National Control Room…</div>
        </div>
      </div>
    );
  }

  const criticalAlerts = alerts.filter(a => a.severity === 'CRITICAL').length;

  return (
    <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* ── Header ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 800, margin: 0, letterSpacing: '-0.5px' }}>
            🛰️ National Control Room
          </h1>
          <p style={{ color: 'var(--text-muted)', margin: '4px 0 0', fontSize: 13 }}>
            Indian Railways · All 18 Zones · Live Operations View
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {criticalAlerts > 0 && (
            <div style={{
              background: '#ef444422', border: '1px solid #ef4444',
              borderRadius: 8, padding: '6px 14px', fontSize: 13, color: '#ef4444', fontWeight: 700,
            }}>
              🚨 {criticalAlerts} CRITICAL
            </div>
          )}
          <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Updated {lastUpdate.toLocaleTimeString()}
          </div>
          <button
            id="ncr-refresh-btn"
            onClick={load}
            style={{
              background: 'var(--color-accent)', color: '#000', border: 'none',
              borderRadius: 8, padding: '7px 16px', cursor: 'pointer', fontWeight: 700, fontSize: 13,
            }}>
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* ── National KPI Cards ── */}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        <MetricCard icon="🚆" label="Trains Running" value={kpi.trains_running.toLocaleString()} color="var(--color-accent)" />
        <MetricCard icon="✅" label="National Punctuality" value={kpi.national_punctuality_pct} unit="%" color={punctualityColor(kpi.national_punctuality_pct)} />
        <MetricCard icon="⏱" label="Trains Delayed" value={kpi.trains_delayed.toLocaleString()} color="#f97316" />
        <MetricCard icon="❌" label="Trains Cancelled" value={kpi.trains_cancelled.toLocaleString()} color="#ef4444" />
        <MetricCard icon="🧑‍🤝‍🧑" label="Passenger-km Today" value={(kpi.passenger_km_today / 1_000_000).toFixed(1)} unit="M km" />
        <MetricCard icon="📦" label="Freight Tonne-km" value={(kpi.freight_tonne_km_today / 1_000_000).toFixed(1)} unit="M" />
        <MetricCard icon="⚡" label="Energy Consumed" value={(kpi.energy_kwh_consumed / 1_000).toFixed(0)} unit="MWh" />
        <MetricCard icon="🔄" label="Zonal Handoffs" value={kpi.zonal_handoffs_today} color="var(--text-secondary)" />
        <MetricCard icon="⚠️" label="Incidents Today" value={kpi.incidents_today} color={kpi.incidents_today > 5 ? '#ef4444' : '#eab308'} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 20 }}>
        {/* ── Zone Performance Table ── */}
        <div style={{
          background: 'var(--color-surface)', border: '1px solid var(--color-border)',
          borderRadius: 14, overflow: 'hidden', boxShadow: '0 2px 16px rgba(0,0,0,0.18)',
        }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 700, fontSize: 15 }}>Zone Performance</span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{kpi.zones_active} zones active</span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'rgba(0,0,0,0.2)' }}>
                  <th style={thStyle('zone')}>#</th>
                  <th style={thStyle('zone')} onClick={() => handleSort('zone')}>Zone</th>
                  <th style={thStyle('trains_running')} onClick={() => handleSort('trains_running')}>Running</th>
                  <th style={thStyle('punctuality_pct')} onClick={() => handleSort('punctuality_pct')}>
                    Punctuality {sortCol === 'punctuality_pct' ? (sortAsc ? '↑' : '↓') : ''}
                  </th>
                  <th style={thStyle('avg_delay_min')} onClick={() => handleSort('avg_delay_min')}>Avg Delay</th>
                  <th style={thStyle('incidents')} onClick={() => handleSort('incidents')}>Incidents</th>
                  <th style={thStyle('handoffs')} onClick={() => handleSort('handoffs')}>Handoffs</th>
                </tr>
              </thead>
              <tbody>
                {sortedZones.map((z, i) => (
                  <ZoneRow key={z.zone} zone={z} rank={i + 1} />
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Right Panel: Alerts + Fleet ── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Alerts */}
          <div style={{
            background: 'var(--color-surface)', border: '1px solid var(--color-border)',
            borderRadius: 14, boxShadow: '0 2px 16px rgba(0,0,0,0.18)', overflow: 'hidden',
          }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--color-border)', fontWeight: 700, fontSize: 14 }}>
              🚨 Active Alerts
            </div>
            <div style={{ padding: '12px 14px', maxHeight: 280, overflowY: 'auto' }}>
              {alerts.length === 0
                ? <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: 20 }}>No active alerts</div>
                : alerts.map(a => <AlertRow key={a.alert_id} alert={a} />)
              }
            </div>
          </div>

          {/* Fleet Utilisation */}
          <div style={{
            background: 'var(--color-surface)', border: '1px solid var(--color-border)',
            borderRadius: 14, boxShadow: '0 2px 16px rgba(0,0,0,0.18)', overflow: 'hidden',
            flex: 1,
          }}>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--color-border)', fontWeight: 700, fontSize: 14 }}>
              🚂 Fleet Utilisation
            </div>
            <div style={{ padding: '14px 18px' }}>
              {fleet.map(r => <FleetBar key={r.fleet_type} rec={r} />)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default NationalControlPage;
