import React, { useState } from 'react';
import type { Train, KPIData } from '../types';

interface FleetPageProps {
  trains: Train[];
  kpis: Partial<KPIData>;
}

type SortKey = 'train_number' | 'current_speed_kmh' | 'current_delay_minutes' | 'priority';
type FilterStatus = 'all' | 'running' | 'delayed' | 'stopped' | 'maintenance';

// ─── Train Detail Panel ─────────────────────────────────────────
function TrainDetailPanel({ train, onClose }: { train: Train; onClose: () => void }) {
  return (
    <div style={{
      position: 'fixed', right: 0, top: 64, bottom: 0, width: 380,
      background: 'var(--color-bg-surface)',
      borderLeft: '1px solid var(--color-border)',
      zIndex: 500,
      overflowY: 'auto',
      padding: 'var(--space-lg)',
    }}>
      <div className="flex items-center justify-between mb-lg">
        <div>
          <div style={{ fontFamily: 'var(--font-brand)', fontSize: 20, color: 'var(--color-cyan)', letterSpacing: 2 }}>
            {train.train_number}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{train.train_type}</div>
        </div>
        <button className="btn btn-ghost btn-icon" onClick={onClose}>✕</button>
      </div>

      {/* Live metrics */}
      <div className="grid-2 mb-lg" style={{ gap: 8 }}>
        {[
          { label: 'Speed',    value: `${train.current_speed_kmh?.toFixed(0)} km/h`, color: 'var(--color-cyan)' },
          { label: 'Delay',    value: `+${train.current_delay_minutes?.toFixed(1)} min`, color: (train.current_delay_minutes || 0) > 2 ? 'var(--color-rose)' : 'var(--color-emerald)' },
          { label: 'Priority', value: `P${train.priority}`, color: 'var(--color-purple)' },
          { label: 'Status',   value: train.status, color: 'var(--color-emerald)' },
        ].map((m, i) => (
          <div key={i} style={{
            background: 'var(--color-bg-elevated)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: '10px 12px',
          }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)', textTransform: 'uppercase' }}>{m.label}</div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700, color: m.color, marginTop: 4 }}>{m.value}</div>
          </div>
        ))}
      </div>

      {/* Route info */}
      <div className="card mb-md">
        <div className="card-title mb-md">Route Information</div>
        <div style={{ fontSize: 12 }}>
          <div className="flex justify-between mb-sm">
            <span style={{ color: 'var(--text-muted)' }}>Current Station</span>
            <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
              {train.current_station || '—'}
            </span>
          </div>
          <div className="flex justify-between mb-sm">
            <span style={{ color: 'var(--text-muted)' }}>Next Station</span>
            <span style={{ color: 'var(--color-cyan)', fontFamily: 'var(--font-mono)' }}>
              {train.next_station || '—'}
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: 'var(--text-muted)' }}>Train ID</span>
            <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
              #{train.id}
            </span>
          </div>
        </div>
      </div>

      {/* Physics data */}
      <div className="card mb-md">
        <div className="card-title mb-md">Physics Data</div>
        <div className="mb-sm">
          <div className="flex justify-between mb-xs">
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Speed</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
              {train.current_speed_kmh?.toFixed(1)} km/h
            </span>
          </div>
          <div className="progress-bar-wrapper">
            <div
              className="progress-bar-fill"
              style={{
                width: `${Math.min(100, (train.current_speed_kmh || 0) / 200 * 100)}%`,
                '--progress-color': 'var(--color-cyan)',
              } as React.CSSProperties}
            />
          </div>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'var(--text-muted)', marginTop: 8 }}>
          Traction: 25kV AC · Brakes: EDB+Pneumatic
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-sm flex-wrap">
        <button className="btn btn-outline btn-sm">📍 Track</button>
        <button className="btn btn-warning btn-sm">⏸ Hold</button>
        <button className="btn btn-outline btn-sm">🔁 Reroute</button>
        <button className="btn btn-danger btn-sm">🛑 Stop</button>
      </div>
    </div>
  );
}

// ─── Fleet Statistics Bar ───────────────────────────────────────
function FleetStats({ trains }: { trains: Train[] }) {
  const total = trains.length;
  const running = trains.filter(t => t.status === 'running').length;
  const delayed = trains.filter(t => (t.current_delay_minutes || 0) > 2).length;
  const stopped = trains.filter(t => t.status === 'stopped').length;
  const avgDelay = total > 0
    ? trains.reduce((s, t) => s + (t.current_delay_minutes || 0), 0) / total
    : 0;
  const avgSpeed = trains.filter(t => (t.current_speed_kmh || 0) > 0).length > 0
    ? trains.reduce((s, t) => s + (t.current_speed_kmh || 0), 0) / trains.filter(t => (t.current_speed_kmh || 0) > 0).length
    : 0;

  return (
    <div className="grid-5 mb-lg">
      {[
        { label: 'Total Fleet',    value: total,            color: 'var(--color-blue)',    unit: '' },
        { label: 'Running',        value: running,          color: 'var(--color-emerald)', unit: '' },
        { label: 'Delayed',        value: delayed,          color: 'var(--color-amber)',   unit: '' },
        { label: 'Avg Delay',      value: avgDelay.toFixed(1), color: 'var(--color-cyan)', unit: ' min' },
        { label: 'Avg Speed',      value: avgSpeed.toFixed(0), color: 'var(--color-purple)', unit: ' km/h' },
      ].map((s, i) => (
        <div key={i} className="kpi-card" style={{ '--kpi-color': s.color } as React.CSSProperties}>
          <div className="kpi-label">{s.label}</div>
          <div className="kpi-value">{s.value}<span className="kpi-unit">{s.unit}</span></div>
        </div>
      ))}
    </div>
  );
}

// ─── Fleet Page ─────────────────────────────────────────────────
export function FleetPage({ trains, kpis }: FleetPageProps) {
  const [selectedTrain, setSelectedTrain] = useState<Train | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('train_number');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  const filtered = trains
    .filter(t => filterStatus === 'all' || t.status === filterStatus)
    .filter(t =>
      !searchQuery ||
      t.train_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.train_type.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      const va = (a as any)[sortKey] ?? 0;
      const vb = (b as any)[sortKey] ?? 0;
      const cmp = typeof va === 'string' ? va.localeCompare(vb) : va - vb;
      return sortDir === 'asc' ? cmp : -cmp;
    });

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const sortIcon = (key: SortKey) =>
    sortKey !== key ? '↕' : sortDir === 'asc' ? '↑' : '↓';

  return (
    <div>
      <div className="section-header mb-lg">
        <div className="section-dot" />
        <h2>Fleet Manager</h2>
        <div className="ml-auto flex gap-sm">
          <button
            className={`btn btn-sm ${viewMode === 'table' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setViewMode('table')}
          >⊟ Table</button>
          <button
            className={`btn btn-sm ${viewMode === 'cards' ? 'btn-primary' : 'btn-outline'}`}
            onClick={() => setViewMode('cards')}
          >⊞ Cards</button>
        </div>
      </div>

      <FleetStats trains={trains} />

      {/* Filters */}
      <div className="card mb-lg">
        <div className="flex items-center gap-md flex-wrap">
          <input
            className="form-input"
            style={{ maxWidth: 240 }}
            placeholder="🔍 Search train..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            id="fleet-search"
          />
          <div className="flex gap-xs">
            {(['all', 'running', 'delayed', 'stopped', 'maintenance'] as FilterStatus[]).map(f => (
              <button
                key={f}
                className={`btn btn-sm ${filterStatus === f ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setFilterStatus(f)}
                id={`filter-${f}`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <div style={{ marginLeft: 'auto', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
            {filtered.length} / {trains.length} trains
          </div>
        </div>
      </div>

      {/* Table View */}
      {viewMode === 'table' && (
        <div className="card">
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Train #</th>
                  <th>Type</th>
                  <th
                    onClick={() => toggleSort('current_speed_kmh')}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                  >
                    Speed {sortIcon('current_speed_kmh')}
                  </th>
                  <th
                    onClick={() => toggleSort('current_delay_minutes')}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                  >
                    Delay {sortIcon('current_delay_minutes')}
                  </th>
                  <th>Location</th>
                  <th
                    onClick={() => toggleSort('priority')}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                  >
                    Priority {sortIcon('priority')}
                  </th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={8} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                      No trains match the current filter
                    </td>
                  </tr>
                ) : filtered.map(t => (
                  <tr
                    key={t.id}
                    className={(t.current_delay_minutes || 0) > 5 ? 'row-danger' : (t.current_delay_minutes || 0) > 2 ? 'row-warning' : ''}
                    onClick={() => setSelectedTrain(t)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td className="font-mono text-cyan">{t.train_number}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{t.train_type}</td>
                    <td className="font-mono text-bright">{t.current_speed_kmh?.toFixed(0)} km/h</td>
                    <td className={`font-mono ${(t.current_delay_minutes || 0) > 2 ? 'text-amber' : 'text-emerald'}`}>
                      {(t.current_delay_minutes || 0) > 0 ? `+${t.current_delay_minutes?.toFixed(1)}` : 'On time'}
                    </td>
                    <td style={{ fontSize: 11 }}>{t.current_station || t.next_station || '—'}</td>
                    <td><span className="badge badge-muted">P{t.priority}</span></td>
                    <td>
                      <span className={`badge ${
                        t.status === 'running' ? 'badge-emerald' :
                        t.status === 'delayed' ? 'badge-amber' :
                        t.status === 'stopped' ? 'badge-rose' : 'badge-muted'
                      }`}>{t.status}</span>
                    </td>
                    <td onClick={e => e.stopPropagation()}>
                      <div className="flex gap-xs">
                        <button className="btn btn-ghost btn-icon btn-sm" title="Track">📍</button>
                        <button className="btn btn-ghost btn-icon btn-sm" title="Hold">⏸</button>
                        <button className="btn btn-ghost btn-icon btn-sm" title="Reroute">🔁</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Card View */}
      {viewMode === 'cards' && (
        <div className="grid-auto">
          {filtered.map(t => (
            <div
              key={t.id}
              className={`train-card ${
                (t.current_delay_minutes || 0) > 2 ? 'delayed' :
                t.status === 'stopped' ? 'stopped' : 'running'
              }`}
              onClick={() => setSelectedTrain(t)}
            >
              <div className="flex items-center justify-between mb-md">
                <div className="train-id">{t.train_number}</div>
                <span className={`badge ${
                  t.status === 'running' ? 'badge-emerald' :
                  t.status === 'delayed' ? 'badge-amber' :
                  'badge-rose'
                }`}>{t.status}</span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginBottom: 8 }}>{t.train_type}</div>
              <div className="train-speed-gauge mb-md">
                <span className="train-speed-value">{t.current_speed_kmh?.toFixed(0) ?? '0'}</span>
                <span className="train-speed-unit">km/h</span>
              </div>
              <div className="progress-bar-wrapper mb-sm">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: `${Math.min(100, ((t.current_speed_kmh || 0) / 200) * 100)}%`,
                    '--progress-color': (t.current_delay_minutes || 0) > 2 ? 'var(--color-amber)' : 'var(--color-cyan)',
                  } as React.CSSProperties}
                />
              </div>
              <div className="flex justify-between" style={{ fontSize: 11 }}>
                <span style={{ color: 'var(--text-muted)' }}>
                  Delay: <span style={{ color: (t.current_delay_minutes || 0) > 2 ? 'var(--color-rose)' : 'var(--color-emerald)' }}>
                    {(t.current_delay_minutes || 0) > 0 ? `+${t.current_delay_minutes?.toFixed(1)}m` : 'On time'}
                  </span>
                </span>
                <span style={{ color: 'var(--text-muted)' }}>P{t.priority}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Train detail panel */}
      {selectedTrain && (
        <TrainDetailPanel
          train={selectedTrain}
          onClose={() => setSelectedTrain(null)}
        />
      )}
    </div>
  );
}
