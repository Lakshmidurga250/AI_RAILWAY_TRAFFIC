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
def get_energy_report(format: str = Query("json", description="json, csv, markdown")):
    res = ReportService.generate_energy_sustainability_report(format=format)
    if format.lower() == "csv":
        return Response(content=res, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=energy_report.csv"})
    elif format.lower() == "markdown":
        return Response(content=res, media_type="text/markdown")
    return res

@router.get("/delay")
def get_delay_report(format: str = Query("json", description="json, csv")):
    res = ReportService.generate_delay_report(format=format)
    if format.lower() == "csv":
        return Response(content=res, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=delay_report.csv"})
    return res

@router.get("/congestion")
def get_congestion_report(format: str = Query("json", description="json, csv")):
    res = ReportService.generate_congestion_report(format=format)
    if format.lower() == "csv":
        return Response(content=res, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=congestion_report.csv"})
    return res

@router.get("/ai-models")
def get_ai_models_report():
    return ReportService.generate_ai_model_report()
