import React from 'react';
import type { PageId } from '../App';

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  collapsed: boolean;
  conflictCount: number;
}

interface NavItem {
  id: PageId;
  icon: string;
  label: string;
  group: string;
  badge?: number | string;
  badgeColor?: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: 'dashboard',    icon: '⚡', label: 'Dashboard',       group: 'Overview' },
  { id: 'network',      icon: '🗺', label: 'Network Map',     group: 'Overview' },
  { id: 'analytics',    icon: '📊', label: 'Analytics',       group: 'Overview' },
  { id: 'fleet',        icon: '🚄', label: 'Fleet Manager',   group: 'Operations' },
  { id: 'timetable',    icon: '📅', label: 'Timetable',       group: 'Operations' },
  { id: 'simulation',   icon: '🔬', label: 'Simulation',      group: 'Operations' },
  { id: 'conflicts',    icon: '⚠️', label: 'Conflicts',       group: 'Safety', badgeColor: 'var(--color-rose)' },
  { id: 'interlocking', icon: '🔐', label: 'Interlocking',    group: 'Safety' },
  { id: 'optimization', icon: '🧬', label: 'Optimization',    group: 'AI Modules' },
  { id: 'ai',           icon: '🤖', label: 'AI Insights',     group: 'AI Modules' },
  { id: 'twin',         icon: '🌐', label: 'Digital Twin',    group: 'AI Modules' },
  { id: 'settings',     icon: '⚙️', label: 'Settings',        group: 'System' },
];

export function Sidebar({ activePage, onNavigate, collapsed, conflictCount }: SidebarProps) {
  const groups = [...new Set(NAV_ITEMS.map(n => n.group))];

  if (collapsed) {
    return (
      <nav className="sidebar" style={{ width: 56 }}>
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            id={`nav-${item.id}`}
            className={`sidebar-nav-item ${activePage === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
            title={item.label}
            style={{ justifyContent: 'center', padding: '10px 0' }}
          >
            <span className="sidebar-nav-icon">{item.icon}</span>
          </button>
        ))}
      </nav>
    );
  }

  return (
    <nav className="sidebar">
      {groups.map(group => (
        <div key={group} className="sidebar-section">
          <div className="sidebar-section-label">{group}</div>
          {NAV_ITEMS.filter(n => n.group === group).map(item => {
            const badge = item.id === 'conflicts' ? conflictCount : item.badge;
            return (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                className={`sidebar-nav-item ${activePage === item.id ? 'active' : ''}`}
                onClick={() => onNavigate(item.id)}
              >
                <span className="sidebar-nav-icon">{item.icon}</span>
                <span>{item.label}</span>
                {badge !== undefined && Number(badge) > 0 && (
                  <span
                    className="sidebar-nav-badge"
                    style={item.badgeColor ? { background: item.badgeColor } : {}}
                  >
                    {badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      ))}

      {/* Version info */}
      <div style={{
        padding: '12px 16px',
        marginTop: 'auto',
        borderTop: '1px solid var(--color-border)',
        fontFamily: 'var(--font-mono)',
        fontSize: '9px',
        color: 'var(--text-muted)',
      }}>
        <div>RAILOPT AI v2.0</div>
        <div>M1+M2+M3+M4</div>
      </div>
    </nav>
  );
}
