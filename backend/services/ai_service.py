"""AI Inference and Management Service."""
from typing import Dict, Any, List, Optional
from ai.delay_prediction.predictor import delay_predictor
from ai.congestion_prediction.predictor import congestion_predictor
from ai.demand_prediction.predictor import demand_predictor
from ai.features.engineering import FeatureEngineer
from ai.reinforcement_learning.trainer import RLTrainer
from ai.energy.model import EnergyOptimizationEngine
from ai.registry.model_registry import model_registry
from simulation.engine.simulator import sim_engine

class AIService:
    @classmethod
    def predict_delay(cls, train_id: str, horizon_minutes: int = 15) -> Dict[str, Any]:
        train = sim_engine.trains.get(train_id)
        if not train:
            # Pick first available train
            train = next(iter(sim_engine.trains.values()), None)

        if not train:
            return {"error": "No active trains in simulation"}

        # Extract real-time features
        features = FeatureEngineer.extract_features_from_train(train)
        pred_res = delay_predictor.predict(features, horizon_minutes=horizon_minutes, current_delay=train.current_delay_minutes)
        pred_res["train_id"] = train.id
        pred_res["train_number"] = train.train_number
        pred_res["current_delay_minutes"] = round(train.current_delay_minutes, 1)
        return pred_res

    @classmethod
    def predict_congestion(cls, resource_type: str, resource_id: str, horizon_minutes: int = 15) -> Dict[str, Any]:
        return congestion_predictor.predict_congestion(
            resource_type=resource_type,
            resource_id=resource_id,
            network=sim_engine.network,
            horizon_minutes=horizon_minutes,
            active_trains_count=len(sim_engine.trains)
        )

    @classmethod
    def predict_demand(cls, station_id: str, horizon_hours: int = 24) -> Dict[str, Any]:
        return demand_predictor.predict_station_demand(
            station_id=station_id,
            network=sim_engine.network,
            horizon_hours=horizon_hours
        )

    @classmethod
    def run_rl_training_evaluation(cls, episodes: int = 10) -> Dict[str, Any]:
        return RLTrainer.train_agent(episodes=episodes, max_steps_per_episode=25)

    @classmethod
    def optimize_energy(cls, train_id: str) -> Dict[str, Any]:
        train = sim_engine.trains.get(train_id)
        mass = train.mass_tons if train else 450.0
        max_spd = train.max_speed_kmh if train else 160.0
        
        result = EnergyOptimizationEngine.optimize_run(
            mass_tons=mass,
            distance_km=28.0,
            scheduled_time_minutes=20.0,
            gradient_percent=0.1,
            max_speed_kmh=max_spd
        )
        result["train_id"] = train_id
        return result

    @classmethod
    def list_models(cls, task: Optional[str] = None) -> List[Dict[str, Any]]:
        return [m.model_dump() for m in model_registry.list_models(task=task)]
