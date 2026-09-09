# Deployment & Infrastructure Guide

## 1. Local Development Quickstart

### Prerequisites
- Python 3.12+ (tested and verified on Python 3.14)
- Git

### Installation
```bash
# Clone and enter workspace
git clone <repo-url>
cd "AI Railway Traffic"

# Install dependencies
pip install -r requirements.txt

# Seed initial database schema and corridor network
python scripts/seed_database.py

# Launch FastAPI Server & Live Control Center Dashboard
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open browser at: **`http://localhost:8000`**
Interactive API Documentation: **`http://localhost:8000/docs`**

---

## 2. Docker Compose Deployment

Run the complete multi-container production stack (Backend + Postgres + Redis + Prometheus + Grafana):

```bash
# Build and spin up all containers
docker-compose up --build -d

# Verify container status
docker-compose ps
```

### Container Endpoints
- **Operations Control Center**: `http://localhost:8000`
- **FastAPI REST & WebSockets**: `http://localhost:8000/docs`
- **Prometheus Metrics**: `http://localhost:9090`
- **Grafana Dashboards**: `http://localhost:3001` (login: `admin` / `admin`)
- **PostgreSQL Database**: `localhost:5432`

---

## 3. Automated Test Verification

Execute all automated unit, integration, simulation, and ML tests:

```bash
pytest tests/ -v
```
All 35 tests pass with full code coverage across all subsystems.
