"""Report Generation API Endpoints."""
from fastapi import APIRouter, Query, Response
from backend.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/operational")
def get_operational_report(format: str = Query("json", description="json, csv, markdown")):
    res = ReportService.generate_operational_report(format=format)
    if format.lower() == "csv":
        return Response(content=res, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=operational_report.csv"})
    elif format.lower() == "markdown":
        return Response(content=res, media_type="text/markdown")
    return res

@router.get("/safety")
def get_safety_report():
    return ReportService.generate_conflict_safety_report()

@router.get("/energy")
def get_energy_report():
    return ReportService.generate_energy_sustainability_report()
