"""AI and Machine Learning API Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from backend.services.ai_service import AIService
from backend.schemas.ai import (
    DelayPredictionRequest, DelayPredictionResponse,
    CongestionPredictionRequest, CongestionPredictionResponse,
    DemandPredictionRequest, DemandPredictionResponse, AIModelCard
)

router = APIRouter(prefix="/ai", tags=["AI & Predictions"])

@router.post("/delay", response_model=DelayPredictionResponse)
def predict_delay(req: DelayPredictionRequest):
    res = AIService.predict_delay(req.train_id, horizon_minutes=req.horizon_minutes)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/congestion", response_model=CongestionPredictionResponse)
def predict_congestion(req: CongestionPredictionRequest):
    return AIService.predict_congestion(
        resource_type=req.resource_type,
        resource_id=req.resource_id,
        horizon_minutes=req.horizon_minutes
    )

@router.post("/demand", response_model=DemandPredictionResponse)
def predict_demand(req: DemandPredictionRequest):
    return AIService.predict_demand(
        station_id=req.station_id,
        horizon_hours=req.horizon_hours
    )

@router.post("/rl/train")
def train_rl_agent(episodes: int = Query(10, ge=1, le=50)):
    return AIService.run_rl_training_evaluation(episodes=episodes)

@router.post("/energy/{train_id}")
def optimize_energy(train_id: str):
    return AIService.optimize_energy(train_id=train_id)

@router.get("/models", response_model=List[AIModelCard])
def list_models(task: Optional[str] = Query(None)):
    return AIService.list_models(task=task)
