import React, { useState } from 'react';
import type { Conflict, Train } from '../types';

interface ConflictsPageProps {
  conflicts: Conflict[];
  trains: Train[];
}

export function ConflictsPage({ conflicts, trains }: ConflictsPageProps) {
  const [selected, setSelected] = useState<Conflict | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<'all' | 'critical' | 'high' | 'medium'>('all');

  const filtered = conflicts.filter(c =>
    filterSeverity === 'all' || (c.severity || '').toLowerCase() === filterSeverity
  );

  const stats = {
    total: conflicts.length,
    critical: conflicts.filter(c => c.severity === 'critical').length,
    high: conflicts.filter(c => c.severity === 'high').length,
    resolved: 0,
  };

  return (
    <div>
      <div className="section-header mb-lg">
        <div className="section-dot" style={{ background: 'var(--color-rose)' }} />
        <h2>Conflict Detection & Resolution</h2>
      </div>

      {/* Stats */}
      <div className="grid-4 mb-lg">
        {[
          { label: 'Total Conflicts', value: stats.total,    color: 'var(--color-rose)' },
          { label: 'Critical',        value: stats.critical, color: 'var(--color-rose)' },
          { label: 'High',            value: stats.high,     color: 'var(--color-amber)' },
          { label: 'Resolved Today',  value: stats.resolved, color: 'var(--color-emerald)' },
        ].map((s, i) => (
          <div key={i} className="kpi-card" style={{ '--kpi-color': s.color } as React.CSSProperties}>
            <div className="kpi-label">{s.label}</div>
            <div className="kpi-value">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: '1fr 380px' }}>
        {/* Conflict list */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Active Conflicts</div>
            <div className="flex gap-xs">
              {(['all', 'critical', 'high', 'medium'] as const).map(f => (
                <button
                  key={f}
                  className={`btn btn-sm ${filterSeverity === f ? 'btn-danger' : 'btn-ghost'}`}
                  onClick={() => setFilterSeverity(f)}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
              <div>No conflicts detected</div>
            </div>
          ) : (
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Type</th>
                    <th>Trains Involved</th>
                    <th>Severity</th>
                    <th>Location</th>
                    <th>Detected</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((c, i) => (
                    <tr key={i} className="row-danger" onClick={() => setSelected(c)} style={{ cursor: 'pointer' }}>
                      <td className="font-mono">{String(c.conflict_type || 'UNKNOWN').replace(/_/g, ' ')}</td>
                      <td className="text-cyan font-mono">
                        {Array.isArray(c.train_ids) ? c.train_ids.join(', ') : '—'}
                      </td>
                      <td>
                        <span className={`badge ${c.severity === 'critical' ? 'badge-rose' : c.severity === 'high' ? 'badge-amber' : 'badge-muted'}`}>
                          {c.severity || 'UNKNOWN'}
                        </span>
                      </td>
                      <td style={{ fontSize: 11 }}>{Array.isArray(c.section_ids) ? c.section_ids.join(', ') : '—'}</td>
                      <td className="font-mono" style={{ fontSize: 10 }}>
                        {c.detected_at ? new Date(c.detected_at).toLocaleTimeString() : '—'}
                      </td>
                      <td onClick={e => e.stopPropagation()}>
                        <button className="btn btn-success btn-sm">Resolve</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Detail panel */}
        <div>
          {selected ? (
            <div className="card">
              <div className="card-header">
                <div className="card-title">Conflict Detail</div>
                <button className="btn btn-ghost btn-icon btn-sm" onClick={() => setSelected(null)}>✕</button>
              </div>
              <div style={{ marginBottom: 12 }}>
                <span className={`badge ${selected.severity === 'critical' ? 'badge-rose' : 'badge-amber'}`} style={{ fontSize: 12 }}>
                  {(selected.severity || 'UNKNOWN').toUpperCase()}
                </span>
              </div>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-rose)', marginBottom: 8 }}>
                {String(selected.conflict_type || 'CONFLICT').replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16 }}>
                {selected.description || 'Conflict detected between trains on shared track sections.'}
              </div>
              <div className="card mb-md" style={{ background: 'var(--color-bg-elevated)' }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11 }}>
                  <div className="flex justify-between mb-sm">
                    <span style={{ color: 'var(--text-muted)' }}>Trains:</span>
                    <span style={{ color: 'var(--color-cyan)' }}>
                      {Array.isArray(selected.train_ids) ? selected.train_ids.join(', ') : '—'}
                    </span>
                  </div>
                  <div className="flex justify-between mb-sm">
                    <span style={{ color: 'var(--text-muted)' }}>Sections:</span>
                    <span>{Array.isArray(selected.section_ids) ? selected.section_ids.join(', ') : '—'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span style={{ color: 'var(--text-muted)' }}>Detected:</span>
                    <span>{selected.detected_at ? new Date(selected.detected_at).toLocaleString() : '—'}</span>
                  </div>
                </div>
              </div>
              <div className="card-title mb-sm">AI Resolution Options</div>
              {[
                'Delay train by 3 minutes',
                'Reroute via alternative path',
                'Speed restriction to 80 km/h',
                'Emergency stop — manual resolve',
              ].map((opt, i) => (
                <button key={i} className="btn btn-outline btn-sm w-full mb-xs" style={{ justifyContent: 'flex-start', marginBottom: 6 }}>
                  {i === 0 ? '⏱' : i === 1 ? '🔁' : i === 2 ? '🔽' : '🛑'} {opt}
                </button>
              ))}
            </div>
          ) : (
            <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
              <div style={{ fontSize: 32, marginBottom: 12 }}>👆</div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                Select a conflict to see details and resolution options
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
