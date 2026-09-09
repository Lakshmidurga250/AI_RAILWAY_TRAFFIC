import React, { useRef, useEffect, useState } from 'react';
import type { Train, Conflict } from '../types';

interface NetworkMapPageProps {
  trains: Train[];
  conflicts: Conflict[];
}

// ─── Network topology (static demo) ─────────────────────────────
const STATIONS = [
  { id: 'HUB',  name: 'Central Hub',  x: 400, y: 200, type: 'major' },
  { id: 'NORTH',name: 'North Term.',  x: 400, y:  60, type: 'terminal' },
  { id: 'EAST', name: 'East Jct.',    x: 580, y: 200, type: 'junction' },
  { id: 'WEST', name: 'West Term.',   x: 220, y: 200, type: 'terminal' },
  { id: 'SOUTH',name: 'South Gate',   x: 400, y: 350, type: 'major' },
  { id: 'NE',   name: 'NE Branch',    x: 520, y:  80, type: 'minor' },
  { id: 'SE',   name: 'SE Depot',     x: 520, y: 340, type: 'depot' },
  { id: 'SW',   name: 'SW Halt',      x: 280, y: 330, type: 'minor' },
  { id: 'YARD', name: 'West Yard',    x: 100, y: 200, type: 'yard' },
];

const LINKS = [
  { from: 'NORTH', to: 'HUB',   id: 'L1', capacity: 4 },
  { from: 'HUB',   to: 'EAST',  id: 'L2', capacity: 4 },
  { from: 'HUB',   to: 'WEST',  id: 'L3', capacity: 2 },
  { from: 'HUB',   to: 'SOUTH', id: 'L4', capacity: 4 },
  { from: 'EAST',  to: 'NE',    id: 'L5', capacity: 2 },
  { from: 'EAST',  to: 'SE',    id: 'L6', capacity: 2 },
  { from: 'SOUTH', to: 'SW',    id: 'L7', capacity: 2 },
  { from: 'WEST',  to: 'YARD',  id: 'L8', capacity: 2 },
];

const STATION_COLORS: Record<string, string> = {
  major:    '#00e5ff',
  terminal: '#a855f7',
  junction: '#f97316',
  minor:    '#4b5563',
  depot:    '#fbbf24',
  yard:     '#6b7280',
};

// ─── SVG Network Map ─────────────────────────────────────────────
function NetworkSvgMap({ trains, conflicts }: { trains: Train[]; conflicts: Conflict[] }) {
  const [hoveredStation, setHoveredStation] = useState<string | null>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);

  const conflictSections = new Set(
    conflicts.flatMap(c => c.section_ids || [])
  );

  // Derive train positions (distribute across stations for demo)
  const trainPositions = trains.map((t, i) => {
    const station = STATIONS[i % STATIONS.length];
    return { ...t, cx: station.x + (Math.random() - 0.5) * 20, cy: station.y + (Math.random() - 0.5) * 20 };
  });

  return (
    <svg
      viewBox="0 0 700 430"
      className="network-map-canvas"
      style={{ background: 'transparent' }}
    >
      <defs>
        <filter id="glow-cyan">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        <filter id="glow-rose">
          <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
        <marker id="arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
          <path d="M0,0 L0,6 L6,3 z" fill="#2d4466" />
        </marker>
      </defs>

      {/* Grid lines */}
      {[100, 200, 300, 400, 500, 600].map(x => (
        <line key={`vg${x}`} x1={x} y1={0} x2={x} y2={430} stroke="rgba(30,45,68,0.3)" strokeWidth="1" />
      ))}
      {[100, 200, 300, 400].map(y => (
        <line key={`hg${y}`} x1={0} y1={y} x2={700} y2={y} stroke="rgba(30,45,68,0.3)" strokeWidth="1" />
      ))}

      {/* Track links */}
      {LINKS.map(link => {
        const from = STATIONS.find(s => s.id === link.from)!;
        const to = STATIONS.find(s => s.id === link.to)!;
        const isConflict = conflictSections.has(link.id);
        return (
          <g key={link.id}>
            {/* Double track */}
            <line
              x1={from.x} y1={from.y} x2={to.x} y2={to.y}
              stroke={isConflict ? 'rgba(255,77,109,0.15)' : 'rgba(30,45,68,0.6)'}
              strokeWidth={link.capacity > 2 ? 8 : 5}
            />
            <line
              x1={from.x} y1={from.y} x2={to.x} y2={to.y}
              stroke={isConflict ? '#ff4d6d' : '#2d4466'}
              strokeWidth={link.capacity > 2 ? 3 : 2}
              strokeDasharray={isConflict ? '6,4' : undefined}
              filter={isConflict ? 'url(#glow-rose)' : undefined}
            />
          </g>
        );
      })}

      {/* Stations */}
      {STATIONS.map(stn => {
        const color = STATION_COLORS[stn.type];
        const isHovered = hoveredStation === stn.id;
        const r = stn.type === 'major' ? 14 : stn.type === 'terminal' ? 12 : 8;
        return (
          <g
            key={stn.id}
            className="map-station-node"
            onMouseEnter={e => {
              setHoveredStation(stn.id);
              setTooltip({ x: stn.x, y: stn.y - 30, text: stn.name });
            }}
            onMouseLeave={() => { setHoveredStation(null); setTooltip(null); }}
          >
            {/* Glow ring */}
            {isHovered && (
              <circle cx={stn.x} cy={stn.y} r={r + 8} fill="none" stroke={color} strokeWidth="1" opacity={0.4} />
            )}
            {/* Outer ring */}
            <circle cx={stn.x} cy={stn.y} r={r + 3} fill="none" stroke={color} strokeWidth="0.5" opacity={0.3} />
            {/* Main circle */}
            <circle
              cx={stn.x} cy={stn.y} r={r}
              fill={`${color}22`}
              stroke={color}
              strokeWidth="1.5"
              filter={isHovered ? 'url(#glow-cyan)' : undefined}
            />
            {/* Center dot */}
            <circle cx={stn.x} cy={stn.y} r={3} fill={color} />
            {/* Label */}
            <text
              x={stn.x} y={stn.y + r + 14}
              textAnchor="middle"
              fill={color}
              fontSize="9"
              fontFamily="var(--font-mono)"
              fontWeight="600"
              opacity={0.9}
            >
              {stn.id}
            </text>
          </g>
        );
      })}

      {/* Train markers */}
      {trainPositions.map((t, i) => (
        <g key={t.id}>
          <circle
            cx={t.cx} cy={t.cy} r={5}
            fill="#00e5ff"
            stroke="#fff"
            strokeWidth="1"
            opacity={0.9}
          >
            <animate attributeName="r" values="5;7;5" dur="2s" repeatCount="indefinite" />
          </circle>
          <text
            x={t.cx + 8} y={t.cy + 4}
            fontSize="8"
            fontFamily="var(--font-mono)"
            fill="rgba(0,229,255,0.8)"
          >
            {t.train_number}
          </text>
        </g>
      ))}

      {/* Tooltip */}
      {tooltip && (
        <g>
          <rect
            x={tooltip.x - 40} y={tooltip.y - 16}
            width={80} height={22}
            rx="4" fill="rgba(8,13,26,0.95)"
            stroke="var(--color-border)"
            strokeWidth="0.5"
          />
          <text
            x={tooltip.x} y={tooltip.y - 1}
            textAnchor="middle"
            fill="#f0f6ff"
            fontSize="9"
            fontFamily="var(--font-mono)"
          >
            {tooltip.text}
          </text>
        </g>
      )}
    </svg>
  );
}

// ─── Network Map Page ─────────────────────────────────────────────
export function NetworkMapPage({ trains, conflicts }: NetworkMapPageProps) {
  const [selectedLayer, setSelectedLayer] = useState<'trains' | 'capacity' | 'conflicts'>('trains');

  return (
    <div>
      <div className="section-header mb-lg">
        <div className="section-dot" />
        <h2>Network Map</h2>
        <div className="tabs-header ml-auto" style={{ marginBottom: 0, width: 'auto', gap: 4 }}>
          {(['trains', 'capacity', 'conflicts'] as const).map(layer => (
            <button
              key={layer}
              className={`tab-btn ${selectedLayer === layer ? 'active' : ''}`}
              onClick={() => setSelectedLayer(layer)}
              id={`map-layer-${layer}`}
              style={{ flex: 'unset', padding: '6px 14px' }}
            >
              {layer.charAt(0).toUpperCase() + layer.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Stats row */}
      <div className="grid-4 mb-lg">
        <div className="kpi-card" style={{ '--kpi-color': 'var(--color-cyan)' } as React.CSSProperties}>
          <div className="kpi-label">Stations</div>
          <div className="kpi-value">{STATIONS.length}</div>
        </div>
        <div className="kpi-card" style={{ '--kpi-color': 'var(--color-blue)' } as React.CSSProperties}>
          <div className="kpi-label">Track Links</div>
          <div className="kpi-value">{LINKS.length}</div>
        </div>
        <div className="kpi-card" style={{ '--kpi-color': 'var(--color-emerald)' } as React.CSSProperties}>
          <div className="kpi-label">Active Trains</div>
          <div className="kpi-value">{trains.length}</div>
        </div>
        <div className="kpi-card" style={{ '--kpi-color': conflicts.length > 0 ? 'var(--color-rose)' : 'var(--color-emerald)' } as React.CSSProperties}>
          <div className="kpi-label">Conflicts</div>
          <div className="kpi-value">{conflicts.length}</div>
        </div>
      </div>

      {/* Map */}
      <div className="grid-2 gap-lg" style={{ gridTemplateColumns: '2fr 1fr' }}>
        <div className="network-map-container">
          <NetworkSvgMap trains={trains} conflicts={conflicts} />
          {/* Legend */}
          <div className="map-legend">
            <div className="flex gap-md flex-wrap">
              {Object.entries(STATION_COLORS).map(([type, color]) => (
                <div key={type} className="flex items-center gap-xs">
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
                  <span>{type}</span>
                </div>
              ))}
              <div className="flex items-center gap-xs">
                <div style={{ width: 12, height: 3, background: '#ff4d6d' }} />
                <span>conflict</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right info panel */}
        <div className="flex flex-col gap-lg">
          {/* Station list */}
          <div className="card flex-1">
            <div className="card-title mb-md">Stations ({STATIONS.length})</div>
            {STATIONS.map(s => (
              <div key={s.id} className="flex items-center justify-between mb-sm" style={{
                padding: '6px 10px',
                background: 'var(--color-bg-elevated)',
                borderRadius: 'var(--radius-sm)',
                fontSize: 11,
              }}>
                <div className="flex items-center gap-sm">
                  <div style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: STATION_COLORS[s.type],
                  }} />
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-cyan)' }}>{s.id}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{s.name}</span>
                </div>
                <span className="badge badge-muted">{s.type}</span>
              </div>
            ))}
          </div>

          {/* Active conflicts on map */}
          <div className="card">
            <div className="card-title mb-md">Active Conflicts</div>
            {conflicts.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: 12, textAlign: 'center', padding: 16 }}>
                ✅ No conflicts
              </div>
            ) : conflicts.slice(0, 4).map((c, i) => (
              <div key={i} className="alert-item critical mb-xs">
                <span className="alert-icon">⚠️</span>
                <div className="alert-content">
                  <div className="alert-title" style={{ fontSize: 11 }}>
                    {String(c.conflict_type || 'CONFLICT').replace(/_/g, ' ')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
