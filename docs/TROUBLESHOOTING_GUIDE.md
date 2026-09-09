# Operations & Troubleshooting Guide

This guide provides diagnostic procedures and resolution steps for common operational issues encountered during local development or production deployment.

---

## 1. Common Diagnostics & Health Verification

### Check General Health & Kubernetes Probes
```bash
# General health
curl -s http://localhost:8000/health | jq .

# Liveness probe (verifies process responsiveness)
curl -s http://localhost:8000/health/live | jq .

# Readiness probe (verifies DB, memory, models)
curl -s http://localhost:8000/health/ready | jq .
```

### Inspect Prometheus Metrics Exposition
```bash
curl -s http://localhost:8000/metrics | grep railway_
```

---

## 2. Frequent Issues & Solutions

### Issue A: Port 8000 Already in Use
**Symptom**: `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`
**Resolution**:
- Windows PowerShell:
  ```powershell
  Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
  Stop-Process -Id <PID> -Force
  ```
- Or run Uvicorn on an alternative port:
  ```bash
  python -m uvicorn backend.main:app --port 8080
  ```

### Issue B: WebSocket `/ws/live` Disconnecting Immediately
**Symptom**: Frontend displays `WebSocket Status: Disconnected` and falls back.
**Resolution**:
1. Verify backend is running without uncaught exceptions in the background tick loop.
2. Ensure reverse proxies (Nginx/Traefik) include WebSocket upgrade headers:
   ```nginx
   proxy_set_header Upgrade $http_upgrade;
   proxy_set_header Connection "upgrade";
   ```
3. Test WebSocket connection directly using a CLI utility:
   ```bash
   python -c "import asyncio, websockets; asyncio.run(websockets.connect('ws://localhost:8000/ws/live'))"
   ```

### Issue C: Database Corrupted or Stale Migration State
**Symptom**: `OperationalError: no such table: trains` or schema mismatch.
**Resolution**:
Delete the local SQLite database file and re-seed the standard network:
```bash
rm railway_traffic.db
python scripts/seed_database.py
```

### Issue D: Simulation Runs Too Slowly or Drops Steps
**Symptom**: Kinematic simulation step throughput drops under heavy load.
**Resolution**:
1. Check acceleration factor: Set `acceleration_factor: 1.0` for real-time operation or up to `60.0` for accelerated runs.
2. In production, run the headless simulation worker in a dedicated container:
   ```bash
   docker-compose up -d worker
   ```

---

## 3. Container & Docker Diagnostics

```bash
# View aggregated service logs
docker-compose logs -f backend

# View simulation worker logs
docker-compose logs -f worker

# Restart containers cleanly
docker-compose down
docker-compose up --build -d
```
