"""AI Model Registry API Endpoints."""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from backend.services.ai_service import AIService
from backend.schemas.ai import AIModelCard, ModelTrainingRequest, ModelEvaluationResponse
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
def update_model_status(model_id: str, status: str = Query(..., description="ACTIVE, RETIRED, VALIDATED, TRAINING, FAILED")):
    success = model_registry.update_status(model_id, status.upper())
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to update model {model_id} to {status}. Ensure valid model ID and status.")
    return {"message": f"Updated model {model_id} status to {status.upper()}", "status": "SUCCESS"}

@router.post("/{model_id}/train", response_model=AIModelCard)
def train_model(model_id: str, req: ModelTrainingRequest = Body(default_factory=ModelTrainingRequest)):
    """Trigger model retraining cycle, bump version, and evaluate metrics."""
    updated_model = model_registry.train_model(
        model_id=model_id,
        hyperparameters=req.hyperparameters,
        dataset=req.dataset
    )
    if not updated_model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    return updated_model.model_dump()

@router.post("/{model_id}/evaluate", response_model=ModelEvaluationResponse)
def evaluate_model(model_id: str):
    """Run validation benchmark evaluation for a model."""
    eval_result = model_registry.evaluate_model(model_id)
    if not eval_result:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    return eval_result

@router.get("/{model_id}/versions")
def get_model_versions(model_id: str):
    """Retrieve version and retraining iteration history for a model."""
    history = model_registry.get_version_history(model_id)
    if history is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    return {"model_id": model_id, "versions": history}
