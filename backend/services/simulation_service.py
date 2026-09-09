"""Simulation Control Service."""
from typing import Dict, Any, List
from simulation.engine.simulator import sim_engine
from simulation.scenarios.scenario_builder import ScenarioCatalog, DisruptionScenario

class SimulationService:
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        return sim_engine.get_status_summary()

    @classmethod
    def start(cls) -> Dict[str, Any]:
        sim_engine.start()
        return sim_engine.get_status_summary()

    @classmethod
    def pause(cls) -> Dict[str, Any]:
        sim_engine.pause()
        return sim_engine.get_status_summary()

    @classmethod
    def resume(cls) -> Dict[str, Any]:
        sim_engine.resume()
        return sim_engine.get_status_summary()

    @classmethod
    def stop(cls) -> Dict[str, Any]:
        sim_engine.stop()
        return sim_engine.get_status_summary()

    @classmethod
    def accelerate(cls, factor: float) -> Dict[str, Any]:
        sim_engine.set_acceleration(factor)
        return sim_engine.get_status_summary()

    @classmethod
    def step(cls, seconds: float = 1.0) -> Dict[str, Any]:
        sim_engine.step(seconds)
        return sim_engine.get_status_summary()

    @classmethod
    def reset(cls) -> Dict[str, Any]:
        sim_engine.initialize_default_traffic()
        return sim_engine.get_status_summary()

    @classmethod
    def list_scenarios(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": s.id,
                "name": s.name,
                "scenario_type": s.scenario_type,
                "description": s.description,
                "parameters": s.parameters
            }
            for s in ScenarioCatalog.get_standard_scenarios()
        ]

    @classmethod
    def create_custom_scenario(
        cls,
        name: str,
        scenario_type: str,
        description: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        import uuid
        scen_id = f"SCEN_CUSTOM_{uuid.uuid4().hex[:8].upper()}"
        scen = DisruptionScenario(
            scenario_id=scen_id,
            name=name,
            scenario_type=scenario_type,
            description=description,
            parameters=parameters
        )
        ScenarioCatalog.register_scenario(scen)
        return {
            "id": scen.id,
            "name": scen.name,
            "scenario_type": scen.scenario_type,
            "description": scen.description,
            "parameters": scen.parameters
        }

    @classmethod
    def run_scenario_comparison(cls, scenario_id: str) -> Dict[str, Any]:
        """Execute baseline vs heuristic vs AI-optimized evaluation for a scenario."""
        scen = ScenarioCatalog.get_scenario(scenario_id)
        if not scen:
            scen = ScenarioCatalog.get_standard_scenarios()[0]

        # Apply disruption onto infrastructure
        scen.apply_to_network(sim_engine.network)
        
        # Calculate dynamic multi-tier metrics
        scen.compute_evaluation_metrics()

        # Revert network to normal
        scen.rollback_network(sim_engine.network)

        return scen.compare_runs()

    @classmethod
    def evaluate_what_if(cls, intervention_type: str, parameters: Dict[str, Any], horizon_minutes: int = 30) -> Dict[str, Any]:
        """Evaluate a what-if counterfactual scenario against baseline."""
        from simulation.engine.what_if import WhatIfSimulationEngine
        return WhatIfSimulationEngine.evaluate_what_if_scenario(intervention_type, parameters, horizon_minutes)

    @classmethod
    def get_replay_timeline(cls) -> Dict[str, Any]:
        """Get summary of recorded historical replay frames."""
        from simulation.engine.replay import historical_replayer
        return historical_replayer.get_timeline_summary()

    @classmethod
    def scrub_replay(cls, index: int) -> Optional[Dict[str, Any]]:
        """Seek historical replay cursor to specified frame."""
        from simulation.engine.replay import historical_replayer
        return historical_replayer.seek_to_index(index)
