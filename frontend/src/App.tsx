import React, { useState, useEffect, useCallback, useRef } from 'react';
import { api } from './services/api';
import { Train, Conflict, KPIData } from './types';

// ─── Page imports ──────────────────────────────────────────
import { DashboardPage }     from './pages/DashboardPage';
import { FleetPage }         from './pages/FleetPage';
import { NetworkMapPage }    from './pages/NetworkMapPage';
import { ConflictsPage }     from './pages/ConflictsPage';
import { TimetablePage }     from './pages/TimetablePage';
import { AIInsightsPage }    from './pages/AIInsightsPage';
import { SimulationPage }    from './pages/SimulationPage';
import { OptimizationPage }  from './pages/OptimizationPage';
import { DigitalTwinPage }   from './pages/DigitalTwinPage';
import { InterlockingPage }  from './pages/InterlockingPage';
import { AnalyticsPage }     from './pages/AnalyticsPage';
import { SettingsPage }        from './pages/SettingsPage';
import { NationalControlPage } from './pages/NationalControlPage';
import { LoginPage }         from './pages/LoginPage';
import { AlertsPanel }       from './components/AlertsPanel';
import { TopBar }            from './components/TopBar';
import { Sidebar }           from './components/Sidebar';

// ─── Types ──────────────────────────────────────────────────
export type PageId =
  | 'dashboard' | 'fleet' | 'network' | 'conflicts'
  | 'timetable' | 'ai' | 'simulation' | 'optimization'
  | 'twin' | 'interlocking' | 'analytics' | 'settings' | 'national';

export interface AppState {
  trains: Train[];
  conflicts: Conflict[];
  kpis: Partial<KPIData>;
  simRunning: boolean;
  simTime: number;          // seconds since epoch
  simSpeed: number;         // multiplier (1x, 5x, 10x …)
  lastUpdated: Date | null;
  alertCount: number;
}

// ─── Default KPIs ────────────────────────────────────────────
const DEFAULT_KPIS: Partial<KPIData> = {
  punctuality_rate: 96.8,
  average_delay_minutes: 1.4,
  active_trains: 6,
  total_conflicts_active: 0,
  network_throughput_tph: 24.5,
};

// ─── Root Application ─────────────────────────────────────────
export function App() {
  const [activePage, setActivePage] = useState<PageId>('dashboard');
  const [state, setState] = useState<AppState>({
    trains: [],
    conflicts: [],
    kpis: DEFAULT_KPIS,
    simRunning: false,
    simTime: Math.floor(Date.now() / 1000),
    simSpeed: 1,
    lastUpdated: null,
    alertCount: 0,
  });
  const [alertsPanelOpen, setAlertsPanelOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const pollIntervalRef = useRef<number | null>(null);

  const [authUser, setAuthUser] = useState<{ username: string; role: string; token: string } | null>(() => {
    try {
      const saved = localStorage.getItem('rail_user');
      return saved ? JSON.parse(saved) : { username: 'admin', role: 'Chief Dispatcher', token: 'active-token' };
    } catch {
      return { username: 'admin', role: 'Chief Dispatcher', token: 'active-token' };
    }
  });

  // ─── Data Fetching ─────────────────────────────────────────
  const fetchData = useCallback(async () => {
    try {
      const [trainData, conflictData, analyticsData] = await Promise.all([
        api.getTrains().catch(() => []),
        api.getConflicts().catch(() => []),
        api.getAnalyticsDashboard().catch(() => null),
      ]);

      setState((prev: any) => ({
        ...prev,
        trains: trainData || prev.trains,
        conflicts: conflictData || prev.conflicts,
        kpis: (analyticsData?.kpis) || prev.kpis,
        alertCount: (conflictData || []).length,
        lastUpdated: new Date(),
        simTime: prev.simTime + (prev.simRunning ? prev.simSpeed * 4 : 0),
      }));
    } catch (err) {
      console.error('Data fetch error:', err);
    }
  }, []);

  // ─── Polling ───────────────────────────────────────────────
  useEffect(() => {
    fetchData();
    pollIntervalRef.current = window.setInterval(fetchData, 4000);
    return () => {
      if (pollIntervalRef.current !== null)
        clearInterval(pollIntervalRef.current);
    };
  }, [fetchData]);

  // ─── Simulation Controls ───────────────────────────────────
  const handleSimControl = useCallback(async (action: 'start' | 'pause' | 'stop' | 'step') => {
    try {
      await api.controlSimulation(action);
      setState((prev: any) => ({
        ...prev,
        simRunning: action === 'start'
          ? true
          : action === 'stop' || action === 'pause'
          ? false
          : prev.simRunning,
      }));
    } catch (err) {
      console.error('Sim control error:', err);
    }
  }, []);

  const handleSpeedChange = useCallback((speed: number) => {
    setState((prev: any) => ({ ...prev, simSpeed: speed }));
  }, []);

  // ─── Page Renderer ─────────────────────────────────────────
  const renderPage = () => {
    const commonProps = { state, onSimControl: handleSimControl };
    switch (activePage) {
      case 'dashboard':     return <DashboardPage {...commonProps} />;
      case 'fleet':         return <FleetPage trains={state.trains} kpis={state.kpis} />;
      case 'network':       return <NetworkMapPage trains={state.trains} conflicts={state.conflicts} />;
      case 'conflicts':     return <ConflictsPage conflicts={state.conflicts} trains={state.trains} />;
      case 'timetable':     return <TimetablePage />;
      case 'ai':            return <AIInsightsPage trains={state.trains} kpis={state.kpis} />;
      case 'simulation':    return <SimulationPage state={state} onSimControl={handleSimControl} onSpeedChange={handleSpeedChange} />;
      case 'optimization':  return <OptimizationPage />;
      case 'twin':          return <DigitalTwinPage state={state} />;
      case 'interlocking':  return <InterlockingPage />;
      case 'analytics':     return <AnalyticsPage state={state} />;
      case 'settings':      return <SettingsPage />;
      case 'national':      return <NationalControlPage />;
      default:              return <DashboardPage {...commonProps} />;
    }
  };

  if (!authUser) {
    return <LoginPage onLoginSuccess={(u: any) => setAuthUser(u)} />;
  }

  return (
    <div className="app-layout">
      {/* Top navigation bar */}
      <TopBar
        state={state}
        onSimControl={handleSimControl}
        alertCount={state.alertCount}
        onAlertsToggle={() => setAlertsPanelOpen((p: boolean) => !p)}
        onMenuToggle={() => setSidebarCollapsed((p: boolean) => !p)}
      />

      <div className="main-content">
        {/* Left sidebar */}
        <Sidebar
          activePage={activePage}
          onNavigate={(page: PageId) => setActivePage(page)}
          collapsed={sidebarCollapsed}
          conflictCount={state.conflicts.length}
        />

        {/* Main content area */}
        <main className="content-area">
          <div className="page-container">
            {renderPage()}
          </div>
        </main>

        {/* Right alerts panel */}
        <AlertsPanel
          open={alertsPanelOpen}
          conflicts={state.conflicts}
          trains={state.trains}
          onClose={() => setAlertsPanelOpen(false)}
        />
      </div>
    </div>
  );
}

export default App;
