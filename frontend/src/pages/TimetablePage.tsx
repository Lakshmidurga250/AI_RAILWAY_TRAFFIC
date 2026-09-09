import React, { useState } from 'react';

interface TimetableEntry {
  trainNum: string;
  type: string;
  origin: string;
  destination: string;
  departure: string;
  arrival: string;
  delay: number;
  platform: string;
  status: 'ontime' | 'delayed' | 'cancelled';
}

const SAMPLE_TIMETABLE: TimetableEntry[] = [
  { trainNum: 'ICE-1401', type: 'High Speed', origin: 'NORTH', destination: 'SOUTH', departure: '06:00', arrival: '07:45', delay: 0,   platform: '1A', status: 'ontime' },
  { trainNum: 'RE-2201',  type: 'Regional',   origin: 'WEST',  destination: 'EAST',  departure: '06:15', arrival: '08:30', delay: 3.5, platform: '2B', status: 'delayed' },
  { trainNum: 'IC-3301',  type: 'Intercity',  origin: 'HUB',   destination: 'NORTH', departure: '06:30', arrival: '07:10', delay: 0,   platform: '3A', status: 'ontime' },
  { trainNum: 'FX-4401',  type: 'Freight',    origin: 'YARD',  destination: 'SE',    departure: '07:00', arrival: '09:30', delay: 0,   platform: 'G1', status: 'ontime' },
  { trainNum: 'RE-2205',  type: 'Regional',   origin: 'EAST',  destination: 'WEST',  departure: '07:15', arrival: '09:45', delay: 5,   platform: '2A', status: 'delayed' },
  { trainNum: 'ICE-1403', type: 'High Speed', origin: 'SOUTH', destination: 'NORTH', departure: '07:30', arrival: '09:15', delay: 0,   platform: '1B', status: 'ontime' },
  { trainNum: 'RE-2207',  type: 'Regional',   origin: 'SW',    destination: 'NE',    departure: '08:00', arrival: '10:15', delay: 0,   platform: '4A', status: 'ontime' },
  { trainNum: 'IC-3305',  type: 'Intercity',  origin: 'NE',    destination: 'HUB',   departure: '08:30', arrival: '09:45', delay: 0,   platform: '3B', status: 'cancelled' },
];

export function TimetablePage() {
  const [activeTab, setActiveTab] = useState<'departures' | 'arrivals' | 'generator'>('departures');
  const [filterType, setFilterType] = useState('all');
  const [searchStation, setSearchStation] = useState('');

  const filtered = SAMPLE_TIMETABLE.filter(e =>
    (filterType === 'all' || e.type.toLowerCase().includes(filterType)) &&
    (!searchStation || e.origin.toLowerCase().includes(searchStation.toLowerCase()) ||
     e.destination.toLowerCase().includes(searchStation.toLowerCase()))
  );

  return (
    <div>
      <div className="section-header mb-lg">
        <div className="section-dot" style={{ background: 'var(--color-purple)' }} />
        <h2>Timetable Management</h2>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <button className="btn btn-primary btn-sm">+ Generate Timetable</button>
          <button className="btn btn-outline btn-sm">📥 Import GTFS</button>
          <button className="btn btn-outline btn-sm">📤 Export</button>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs-header">
        {(['departures', 'arrivals', 'generator'] as const).map(t => (
          <button key={t} className={`tab-btn ${activeTab === t ? 'active' : ''}`}
            onClick={() => setActiveTab(t)}>
            {t === 'departures' ? '🚄 Departures' : t === 'arrivals' ? '🛬 Arrivals' : '⚡ AI Generator'}
          </button>
        ))}
      </div>

      {activeTab === 'generator' ? (
        <div className="card">
          <div className="card-title mb-lg">AI Timetable Generator</div>
          <div className="grid-2 gap-lg">
            <div>
              <div className="form-group">
                <label className="form-label">Line Name</label>
                <input className="form-input" defaultValue="North-South Express" />
              </div>
              <div className="form-group">
                <label className="form-label">Service Frequency</label>
                <select className="form-select">
                  <option>Every 15 minutes</option>
                  <option>Every 30 minutes</option>
                  <option>Every 60 minutes (Hourly)</option>
                  <option>Every 2 hours</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Train Category</label>
                <select className="form-select">
                  <option>High Speed (HS)</option>
                  <option>Intercity (IC)</option>
                  <option>Regional (RE)</option>
                  <option>Local (S)</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Max Speed (km/h)</label>
                <input className="form-input" type="number" defaultValue={160} />
              </div>
            </div>
            <div>
              <div className="form-group">
                <label className="form-label">Station Sequence</label>
                <textarea className="form-textarea" defaultValue={"NORTH\nHUB\nSOUTH\nSE"} style={{ height: 120 }} />
              </div>
              <div className="form-group">
                <label className="form-label">Supplement Factor (%)</label>
                <input className="form-input" type="number" defaultValue={5} />
              </div>
              <div className="flex gap-sm" style={{ marginTop: 8 }}>
                <label className="toggle-switch">
                  <input type="checkbox" defaultChecked />
                  <div className="toggle-track" />
                  <span className="toggle-label">Symmetric timetable</span>
                </label>
              </div>
            </div>
          </div>
          <div className="flex gap-sm mt-lg">
            <button className="btn btn-primary">⚡ Generate</button>
            <button className="btn btn-outline">🔍 Analyze Capacity</button>
            <button className="btn btn-outline">📊 Stability Analysis</button>
          </div>
        </div>
      ) : (
        <div className="card">
          {/* Filters */}
          <div className="flex gap-md mb-lg flex-wrap">
            <input
              className="form-input"
              style={{ maxWidth: 200 }}
              placeholder="🔍 Filter by station..."
              value={searchStation}
              onChange={e => setSearchStation(e.target.value)}
            />
            <div className="flex gap-xs">
              {['all', 'high speed', 'regional', 'intercity', 'freight'].map(f => (
                <button key={f} className={`btn btn-sm ${filterType === f ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => setFilterType(f)}>
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Train #</th>
                  <th>Type</th>
                  <th>{activeTab === 'departures' ? 'Origin' : 'Origin'}</th>
                  <th>{activeTab === 'departures' ? 'Destination' : 'Destination'}</th>
                  <th>{activeTab === 'departures' ? 'Departs' : 'Arrives'}</th>
                  <th>Delay</th>
                  <th>Platform</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((entry, i) => (
                  <tr key={i}
                    className={entry.status === 'delayed' ? 'row-warning' : entry.status === 'cancelled' ? 'row-danger' : ''}>
                    <td className="font-mono text-cyan">{entry.trainNum}</td>
                    <td><span className="badge badge-muted">{entry.type}</span></td>
                    <td className="font-mono">{entry.origin}</td>
                    <td className="font-mono">{entry.destination}</td>
                    <td className="font-mono text-bright">
                      {activeTab === 'departures' ? entry.departure : entry.arrival}
                    </td>
                    <td className={`font-mono ${entry.delay > 0 ? 'text-amber' : 'text-emerald'}`}>
                      {entry.delay > 0 ? `+${entry.delay}m` : 'On time'}
                    </td>
                    <td className="font-mono text-purple">{entry.platform}</td>
                    <td>
                      <span className={`badge ${
                        entry.status === 'ontime' ? 'badge-emerald' :
                        entry.status === 'delayed' ? 'badge-amber' : 'badge-rose'
                      }`}>{entry.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
