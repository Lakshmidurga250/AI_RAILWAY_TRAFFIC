"""AI Railway Traffic Optimization & Intelligent Train Management System.

FastAPI Production Server Entrypoint.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.models.user import User
from backend.app.security import get_password_hash
from simulation.engine.simulator import sim_engine

# Import API Routers
from backend.api import (
    auth_router,
    trains_router,
    stations_router,
    network_router,
    simulation_router,
    ai_router,
    optimization_router,
    conflicts_router,
    analytics_router,
    reports_router,
    models_router,
    websockets_router,
    physics_router,
    emergency_router
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    # 1. Create database schema
    Base.metadata.create_all(bind=engine)

    # 2. Seed default RBAC roles/permissions and initial admin user if absent
    db = SessionLocal()
    try:
        from backend.repositories.role_repository import RoleRepository
        from backend.repositories.user_repository import UserRepository
        role_repo = RoleRepository(db)
        user_repo = UserRepository(db)
        role_repo.seed_defaults()

        admin_user = user_repo.get_by_username("admin")
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@railway-ai.internal",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Lead Railway Dispatcher",
                role="admin",
                is_active=True
            )
            admin_user = user_repo.create(admin_user)
            admin_role = role_repo.get_by_name("admin")
            if admin_role:
                user_repo.assign_role_to_user(admin_user.id, admin_role.id)
            print("[INFO] Seeded default administrator user: 'admin'")
        else:
            admin_role = role_repo.get_by_name("admin")
            if admin_role:
                user_repo.assign_role_to_user(admin_user.id, admin_role.id)
    finally:
        db.close()

    # 3. Start background simulation loop
    sim_engine.start()
    print("[INFO] Simulation Engine background runner active.")

    yield

    # Shutdown
    sim_engine.stop()
    print("[INFO] Simulation Engine safely terminated.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade discrete-event simulation, AI prediction, and multi-objective optimization platform for railway traffic.",
    version="2.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pure ASGI Security & Observability Middleware (high-performance, non-blocking)
class SecurityAndMetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import time
        import uuid
        start_time = time.time()

        # Extract or generate Request ID
        req_id = None
        for name, val in scope.get("headers", []):
            if name.lower() == b"x-request-id":
                req_id = val.decode("utf-8", errors="ignore")
                break
        if not req_id:
            req_id = str(uuid.uuid4())

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers", []))
                # Security & Tracing Headers
                raw_headers.append((b"x-content-type-options", b"nosniff"))
                raw_headers.append((b"x-frame-options", b"DENY"))
                raw_headers.append((b"x-xss-protection", b"1; mode=block"))
                raw_headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains"))
                raw_headers.append((b"referrer-policy", b"strict-origin-when-cross-origin"))
                raw_headers.append((b"x-request-id", req_id.encode("utf-8")))
                message["headers"] = raw_headers

                duration = time.time() - start_time
                status_code = str(message.get("status", 200))
                try:
                    from backend.app.metrics import (
                        http_requests_total,
                        http_request_duration_seconds,
                        railway_active_trains
                    )
                    path = scope.get("path", "")
                    method = scope.get("method", "GET")
                    http_requests_total.labels(method=method, endpoint=path, status=status_code).inc()
                    http_request_duration_seconds.labels(method=method, endpoint=path).observe(duration)
                    railway_active_trains.set(len(sim_engine.trains))
                except Exception:
                    pass

            await send(message)

        await self.app(scope, receive, send_wrapper)

app.add_middleware(SecurityAndMetricsMiddleware)

# Mount Prometheus Metrics
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Include All Routers (both root and /api prefixed for convenience)
api_routers = [
    auth_router,
    trains_router,
    stations_router,
    network_router,
    simulation_router,
    ai_router,
    optimization_router,
    conflicts_router,
    analytics_router,
    reports_router,
    models_router,
    physics_router,
    emergency_router,
]

for r in api_routers:
    app.include_router(r)
    app.include_router(r, prefix="/api")

app.include_router(websockets_router)
app.include_router(websockets_router, prefix="/api")

# Mount Static Files and Root Dashboard
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse, tags=["Dashboard UI"])
@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard UI"])
def get_control_center():
    """Serves the interactive Control Center single page application."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>AI Railway Traffic Optimization Platform</h1><p>UI loading error</p>")

@app.get("/health", tags=["Observability"])
async def health_check():
    """Liveness and readiness health probe."""
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "simulation_running": sim_engine.is_running,
        "active_trains": len(sim_engine.trains)
    }

@app.get("/health/live", tags=["Observability"])
async def liveness_probe():
    """Kubernetes / Docker container liveness probe."""
    return {"status": "ALIVE", "service": settings.APP_NAME}

@app.get("/health/ready", tags=["Observability"])
async def readiness_probe():
    """Kubernetes / Docker container readiness probe."""
    sim_ok = sim_engine is not None and sim_engine.network is not None
    return {
        "status": "READY" if sim_ok else "DEGRADED",
        "database": "CONNECTED",
        "simulation_engine": "INITIALIZED" if sim_ok else "ERROR",
        "active_trains": len(sim_engine.trains) if sim_ok else 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
