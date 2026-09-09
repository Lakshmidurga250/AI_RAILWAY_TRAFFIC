"""Optimization API Endpoints with Metaheuristics, Reinforcement Learning, and Audit Trails."""
import time
import uuid
import numpy as np
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.services.optimization_service import OptimizationService
from backend.schemas.optimization import (
    RouteOptimizationRequest, RouteOptimizationResponse,
    PlatformOptimizationRequest, PlatformOptimizationResponse,
    ReschedulingRequest, ReschedulingResponse,
    EnergyOptimizationRequest, EnergyOptimizationResponse,
    OptimizationRunResponse,
    RLTrainRequest, RLTrainResponse,
    RLDispatchRequest, RLDispatchResponse,
    RLTrainingRunResponse
)
from backend.services.ai_service import AIService
from backend.repositories.rl_repository import RLRepository
from simulation.engine.simulator import sim_engine
from ai.reinforcement_learning.environment import RailwayGymEnv
from ai.reinforcement_learning.trainer import RLTrainer
from ai.reinforcement_learning.safety_shield import InterlockingSafetyShield
from ai.reinforcement_learning.action_masking import RailwayActionMasker
from ai.reinforcement_learning.policies import DQNAgent, PPOActorCritic, RuleBasedDispatcher

router = APIRouter(prefix="/optimization", tags=["Optimization"])

@router.post("/route", response_model=RouteOptimizationResponse)
def optimize_route(req: RouteOptimizationRequest, db: Session = Depends(get_db)):
    """Compute optimal train route using Dijkstra, A*, Floyd-Warshall, Pareto, GA, PSO, or SA."""
    return OptimizationService.optimize_route(
        origin_station_id=req.origin_station_id,
        destination_station_id=req.destination_station_id,
        algorithm=req.algorithm,
        train_id=req.train_id,
        db=db
    )

@router.post("/platform", response_model=PlatformOptimizationResponse)
def optimize_platform(req: PlatformOptimizationRequest, db: Session = Depends(get_db)):
    """Assign optimal station platform avoiding contentions."""
    res = OptimizationService.optimize_platform(
        station_id=req.station_id,
        train_id=req.train_id,
        db=db
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.post("/schedule")
def optimize_schedule(db: Session = Depends(get_db)):
    """Optimize macroscopic corridor timetable with conflict-free headways."""
    return OptimizationService.optimize_schedule(db=db)

@router.post("/reschedule", response_model=ReschedulingResponse)
def dynamic_reschedule(req: ReschedulingRequest, db: Session = Depends(get_db)):
    """Dynamically reschedule active trains around a track disruption."""
    return OptimizationService.dynamic_reschedule(
        scenario_type=req.scenario_type,
        affected_resource_id=req.affected_resource_id,
        duration_minutes=req.duration_minutes,
        db=db
    )

@router.post("/energy", response_model=EnergyOptimizationResponse)
def optimize_energy_profile(req: EnergyOptimizationRequest):
    """Generate eco-driving speed profile with coasting phases."""
    return AIService.optimize_energy(req.train_id)

@router.post("/conflicts/{conflict_id}/resolve")
def resolve_conflict(conflict_id: str):
    """Execute automated conflict resolution strategy."""
    res = OptimizationService.resolve_active_conflict(conflict_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/runs", response_model=List[OptimizationRunResponse])
def list_optimization_runs(
    limit: int = Query(50, ge=1, le=200),
    optimization_type: Optional[str] = Query(None, description="Filter by ROUTING, SCHEDULING, PLATFORM, RESCHEDULING"),
    db: Session = Depends(get_db)
):
    """Retrieve historical optimization runs with execution time and savings metrics."""
    return OptimizationService.list_optimization_runs(limit=limit, optimization_type=optimization_type, db=db)

@router.post("/rl/train", response_model=RLTrainResponse)
def train_rl_agent(req: RLTrainRequest, db: Session = Depends(get_db)):
    """Trigger local Reinforcement Learning training loop with action masking and safety metrics."""
    start_t = time.perf_counter()
    train_res = RLTrainer.train_agent(
        episodes=req.episodes,
        max_steps_per_episode=req.max_steps_per_episode,
        algorithm=req.algorithm,
        use_action_masking=req.use_action_masking
    )
    elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)

    run_id = f"RL_RUN_{uuid.uuid4().hex[:8].upper()}"
    repo = RLRepository(db)
    repo.record_training_run(
        run_id=run_id,
        algorithm=train_res["algorithm"],
        episodes_trained=req.episodes,
        mean_episode_reward=train_res["mean_episode_reward"],
        shield_interventions_count=train_res.get("shield_interventions_count", 0),
        baseline_heuristic_reward=train_res.get("baseline_heuristic_eval", {}).get("mean_reward", 0.0),
        improvement_percentage=train_res.get("improvement_percentage", 0.0),
        metrics=train_res
    )

    return {
        "run_id": run_id,
        "algorithm": train_res["algorithm"],
        "episodes_trained": req.episodes,
        "mean_episode_reward": train_res["mean_episode_reward"],
        "shield_interventions_count": train_res.get("shield_interventions_count", 0),
        "improvement_percentage": train_res.get("improvement_percentage", 0.0),
        "execution_time_ms": elapsed_ms
    }

@router.post("/rl/dispatch", response_model=RLDispatchResponse)
def dispatch_rl_action(req: RLDispatchRequest, db: Session = Depends(get_db)):
    """Evaluate and dispatch an RL action protected by Interlocking Safety Shield."""
    if req.train_id not in sim_engine.trains:
        raise HTTPException(status_code=404, detail=f"Train '{req.train_id}' not found in active simulation.")

    train = sim_engine.trains[req.train_id]
    mask = RailwayActionMasker.get_action_mask(sim_engine, train)
    action_names = RailwayGymEnv.ACTION_NAMES

    # Select action
    alg_upper = req.algorithm.upper()
    if alg_upper in ("PPO", "ACTOR_CRITIC"):
        agent = PPOActorCritic()
        raw_action, _, _ = agent.select_action(np.zeros(40, dtype=np.float32), action_mask=mask, evaluate=True)
    elif alg_upper in ("DQN", "Q_LEARNING"):
        agent = DQNAgent()
        raw_action = agent.select_action(np.zeros(40, dtype=np.float32), action_mask=mask, evaluate=True)
    else:
        raw_action = RuleBasedDispatcher.select_action(np.zeros(40, dtype=np.float32), action_mask=mask)

    # Interlocking Safety Shield verification
    shield_res = InterlockingSafetyShield.verify_and_filter(sim_engine, train, raw_action)
    executed_action = shield_res["executed_action"] if req.use_safety_shield else raw_action

    # Record dispatch audit
    repo = RLRepository(db)
    repo.record_dispatch_action(
        train_id=req.train_id,
        algorithm=alg_upper,
        proposed_action=action_names[raw_action],
        executed_action=action_names[executed_action],
        shield_intervened=shield_res["shield_intervened"],
        safety_violations=shield_res["violations"],
        reward=0.0,
        explanation=shield_res["reason"]
    )

    return {
        "train_id": req.train_id,
        "algorithm": alg_upper,
        "proposed_action": action_names[raw_action],
        "executed_action": action_names[executed_action],
        "shield_intervened": shield_res["shield_intervened"],
        "violations": shield_res["violations"],
        "reason": shield_res["reason"],
        "action_mask": [bool(b) for b in mask]
    }

@router.get("/rl/runs", response_model=List[RLTrainingRunResponse])
def list_rl_training_runs(
    limit: int = Query(20, ge=1, le=100),
    algorithm: Optional[str] = Query(None, description="Filter by algorithm: DEEP_Q_NETWORK, PROXIMAL_POLICY_OPTIMIZATION"),
    db: Session = Depends(get_db)
):
    """Retrieve historical RL training run records and convergence telemetry."""
    repo = RLRepository(db)
    return repo.get_recent_training_runs(limit=limit, algorithm=algorithm)
