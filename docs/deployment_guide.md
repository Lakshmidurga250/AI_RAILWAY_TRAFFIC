# Deployment, Infrastructure & Monitoring Guide

## 1. Local Development Environment

```bash
# Clone & enter directory
git clone https://github.com/railway-ai/railway-optimization.git
cd railway-optimization

# Install Python requirements
pip install -r requirements.txt

# Run migrations and seed data
python scripts/seed_database.py

# Run unit and integration tests
python -m pytest tests/ -v

# Start FastAPI application
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## 2. Docker & Container Orchestration

The project includes production-ready Dockerfiles and a `docker-compose.yml` defining:
* `backend`: FastAPI API server & discrete-event simulation engine on port 8000.
* `frontend`: Production Nginx serving the compiled React/TypeScript single-page app on port 3000.
* `worker`: Background task worker for batch ML training.
* `postgres`: PostgreSQL 16 database storing trains, schedules, telemetry, and audit logs on port 5432.
* `redis`: Redis 7 in-memory cache and message broker on port 6379.
* `prometheus`: Scrapes `/metrics` from backend on port 9090.
* `grafana`: Visualizes operational KPIs and server health on port 3001.

### Launching with Docker Compose
```bash
docker compose up --build -d
```

### Stopping Containers
```bash
docker compose down
```

## 3. Observability & Monitoring

* **Health Check**: `GET /health` returns application health, environment status, and active train count.
* **Prometheus Metrics**: `GET /metrics` exposes standard ASGI and custom railway telemetry metrics (active trains, conflicts, throughput, request latency).
* **Grafana Dashboards**: Pre-configured JSON dashboards located in `monitoring/grafana/dashboards/`.
