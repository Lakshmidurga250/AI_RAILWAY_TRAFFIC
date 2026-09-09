# Deployment & Production Operations Guide

This guide details the deployment architecture for the **AI Railway Traffic Optimization System**, covering local development, multi-container Docker Compose orchestration, and Kubernetes production readiness.

---

## 1. System Deployment Architecture

```
                                  [ Ingress / Reverse Proxy (Nginx) ]
                                             :80 / :443
                                                 │
                     ┌───────────────────────────┼───────────────────────────┐
                     ▼                           ▼                           ▼
        [ Frontend Web OCC ]          [ FastAPI Backend ]             [ Grafana OCC ]
            (:80 / :3000)                   (:8000)                       (:3001)
                                                 │                           ▲
                                    ┌────────────┼────────────┐              │
                                    ▼            ▼            ▼              │
                               [PostgreSQL]   [Redis]   [Prometheus] ────────┘
                                 (:5432)      (:6379)     (:9090)
                                                 │
                                                 ▼
                                     [ Simulation Worker ]
                                       (Headless Daemon)
```

---

## 2. Docker Compose Orchestration

The complete platform can be provisioned using `docker-compose.yml`:

```bash
# Build and start all 7 services in background
docker-compose up --build -d

# Verify running service status
docker-compose ps
```

### Services & Port Mappings

| Service | Container Name | Port | Description |
|---|---|---|---|
| `backend` | `railway_backend` | `8000` | FastAPI application serving REST APIs, WebSockets `/ws/live`, and static OCC UI |
| `frontend` | `railway_frontend` | `3000` | React / Vite web application |
| `worker` | `railway_worker` | — | Headless simulation daemon running continuous physics steps |
| `postgres` | `railway_postgres` | `5432` | PostgreSQL 16 relational database |
| `redis` | `railway_redis` | `6379` | In-memory cache and pub/sub message broker |
| `prometheus` | `railway_prometheus` | `9090` | Prometheus time-series scraper collecting metrics every 5s |
| `grafana` | `railway_grafana` | `3001` | Grafana analytics dashboard with pre-provisioned railway panels |

---

## 3. Environment Variables Configuration

Copy `.env.example` to `.env` and configure appropriate variables:

```ini
ENVIRONMENT=production
DATABASE_URL=postgresql://railway_admin:railway_secure_pass_2026@postgres:5432/railway_db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=production_cryptographic_secret_key_change_me
ACCESS_TOKEN_EXPIRE_MINUTES=1440
PROMETHEUS_METRICS_ENABLED=true
SIMULATION_DEFAULT_ACCELERATION=1.0
```

---

## 4. Kubernetes Probes & Observability Integration

The backend provides native Kubernetes probes:
- **Liveness Probe**:
  ```yaml
  livenessProbe:
    httpGet:
      path: /health/live
      port: 8000
    initialDelaySeconds: 5
    periodSeconds: 10
  ```
- **Readiness Probe**:
  ```yaml
  readinessProbe:
    httpGet:
      path: /health/ready
      port: 8000
    initialDelaySeconds: 10
    periodSeconds: 15
  ```

---

## 5. Monitoring & Dashboards

- **Prometheus Metrics Endpoint**: `http://localhost:8000/metrics`
  - Scrapes 12 custom metrics (`railway_http_requests_total`, `railway_active_trains`, `railway_conflicts_total`, `railway_simulation_steps_total`, etc.).
- **Grafana Dashboard**: Open `http://localhost:3001` (admin / admin).
  - The dashboard at `monitoring/grafana/dashboards/railway_operations.json` provides live telemetry graphs for request volume, active conflicts, simulation step throughput, fleet energy consumption, and API latency percentiles.
