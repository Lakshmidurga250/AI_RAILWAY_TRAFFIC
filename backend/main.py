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
    websockets_router
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    # 1. Create database schema
    Base.metadata.create_all(bind=engine)

    # 2. Seed initial admin user if absent
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(
                username="admin",
                email="admin@railway-ai.internal",
                hashed_password=get_password_hash("AdminPass123!"),
                full_name="Lead Railway Dispatcher",
                role="admin",
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print("[INFO] Seeded default administrator user: 'admin'")
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

# Mount Prometheus Metrics
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# Include All Routers
app.include_router(auth_router)
app.include_router(trains_router)
app.include_router(stations_router)
app.include_router(network_router)
app.include_router(simulation_router)
app.include_router(ai_router)
app.include_router(optimization_router)
app.include_router(conflicts_router)
app.include_router(analytics_router)
app.include_router(reports_router)
app.include_router(models_router)
app.include_router(websockets_router)

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
def health_check():
    """Liveness and readiness health probe."""
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "simulation_running": sim_engine.is_running,
        "active_trains": len(sim_engine.trains)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
