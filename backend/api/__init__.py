"""Backend API Routers Export."""
from backend.api.auth import router as auth_router
from backend.api.trains import router as trains_router
from backend.api.stations import router as stations_router
from backend.api.network import router as network_router
from backend.api.simulation import router as simulation_router
from backend.api.ai import router as ai_router
from backend.api.optimization import router as optimization_router
from backend.api.conflicts import router as conflicts_router
from backend.api.analytics import router as analytics_router
from backend.api.reports import router as reports_router
from backend.api.models import router as models_router
from backend.api.websockets import router as websockets_router
from backend.api.physics import router as physics_router

__all__ = [
    "auth_router",
    "trains_router",
    "stations_router",
    "network_router",
    "simulation_router",
    "ai_router",
    "optimization_router",
    "conflicts_router",
    "analytics_router",
    "reports_router",
    "models_router",
    "websockets_router",
    "physics_router"
]
