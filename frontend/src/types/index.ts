export interface Train {
  id: string;
  train_number: string;
  name: string;
  train_type: string;
  origin_station_id: string;
  destination_station_id: string;
  length_m: number;
  weight_tons: number;
  max_speed_kmh: number;
  status: string;
  current_speed_kmh: number;
  current_delay_minutes: number;
  priority: number;
  current_lat?: number;
  current_lng?: number;
  cumulative_energy_kwh: number;
}

export interface Conflict {
  id: string;
  conflict_type: string;
  severity: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: string;
  location_type: string;
  location_id: string;
  primary_train_id: string;
  secondary_train_id?: string;
  cause: string;
  recommendation: string;
  detected_at: string;
}

export interface KPIData {
  active_trains: number;
  punctuality_rate: number;
  average_delay_minutes: number;
  max_delay_minutes: number;
  total_conflicts_active: number;
  total_conflicts_resolved_today: number;
  network_throughput_tph: number;
  total_energy_kwh: number;
  co2_saved_kg: number;
}

export interface SimulationStatus {
  id: string;
  name: string;
  status: 'RUNNING' | 'PAUSED' | 'STOPPED';
  time_acceleration: number;
  current_sim_time: string;
  total_trains: number;
  active_conflicts: number;
}
