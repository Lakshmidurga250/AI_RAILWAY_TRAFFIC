"""Analytics API Endpoints."""
from fastapi import APIRouter
from backend.services.analytics_service import AnalyticsService
from backend.schemas.analytics import AnalyticsDashboardData

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/dashboard", response_model=AnalyticsDashboardData)
def get_dashboard_analytics():
    return AnalyticsService.get_dashboard_data()
