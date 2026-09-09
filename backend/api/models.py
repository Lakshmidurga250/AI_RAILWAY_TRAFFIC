"""AI Model Registry API Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.services.ai_service import AIService
from backend.schemas.ai import AIModelCard
from ai.registry.model_registry import model_registry

router = APIRouter(prefix="/models", tags=["Model Registry"])

@router.get("", response_model=List[AIModelCard])
def list_models(task: Optional[str] = Query(None)):
    return AIService.list_models(task=task)

@router.get("/{model_id}", response_model=AIModelCard)
def get_model(model_id: str):
    m = model_registry.get_model(model_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    return m.model_dump()

@router.put("/{model_id}/status")
def update_model_status(model_id: str, status: str = Query(..., description="ACTIVE, RETIRED, VALIDATED, TRAINING")):
    success = model_registry.update_status(model_id, status.upper())
    if not success:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    return {"message": f"Updated model {model_id} status to {status.upper()}", "status": "SUCCESS"}
