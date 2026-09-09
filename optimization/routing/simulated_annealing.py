"""Simulated Annealing (SA) Router for Railway Traffic."""
import math
import random
import time
from typing import List, Dict, Any, Optional
from simulation.network.graph import RailwayNetwork
from optimization.routing.genetic_algorithm import GeneticAlgorithmRouter

class SimulatedAnnealingRouter:
    """Stochastic Simulated Annealing metaheuristic for multi-objective route selection."""

    INITIAL_TEMPERATURE = 100.0
    COOLING_RATE = 0.88
    MAX_ITERATIONS = 40

    @classmethod
    def optimize_route(
        cls,
        network: RailwayNetwork,
        origin_id: str,
        destination_id: str,
        initial_temp: float = INITIAL_TEMPERATURE,
        cooling_rate: float = COOLING_RATE,
        max_iterations: int = MAX_ITERATIONS
    ) -> Dict[str, Any]:
        """Execute Simulated Annealing with Metropolis acceptance criterion."""
        start_t = time.perf_counter()

        # Seed initial solution from shortest path
        current_path = network.find_shortest_path(origin_id, destination_id)
        if not current_path:
            return {
                "error": f"No topological route found between {origin_id} and {destination_id}",
                "execution_time_ms": round((time.perf_counter() - start_t) * 1000, 2)
            }

        candidate_paths = network.find_k_shortest_paths(origin_id, destination_id, k=6, weight_type="travel_time")
        if not candidate_paths:
            candidate_paths = [current_path]

        current_metrics = GeneticAlgorithmRouter.evaluate_fitness(network, current_path)
        best_path = list(current_path)
        best_metrics = dict(current_metrics)

        temperature = initial_temp

        for it in range(max_iterations):
            # Propose neighbor by picking an alternative path from candidate pool or mutating
            neighbor = random.choice(candidate_paths)
            if random.random() < 0.3 and len(neighbor) > 3:
                # Perturb
                neighbor = GeneticAlgorithmRouter._mutate(network, neighbor, origin_id, destination_id)

            neighbor_metrics = GeneticAlgorithmRouter.evaluate_fitness(network, neighbor)
            delta_e = neighbor_metrics["score"] - current_metrics["score"]

            # Metropolis acceptance criterion
            if delta_e < 0:
                current_path = list(neighbor)
                current_metrics = dict(neighbor_metrics)
            else:
                p_accept = math.exp(-delta_e / max(0.001, temperature))
                if random.random() < p_accept:
                    current_path = list(neighbor)
                    current_metrics = dict(neighbor_metrics)

            if current_metrics["score"] < best_metrics["score"]:
                best_path = list(current_path)
                best_metrics = dict(current_metrics)

            # Cool temperature
            temperature *= cooling_rate

        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        tracks = network.path_to_tracks(best_path)
        track_ids = [t.id for t in tracks]

        return {
            "algorithm": "SIMULATED_ANNEALING",
            "iterations": max_iterations,
            "final_temperature": round(temperature, 4),
            "execution_time_ms": elapsed_ms,
            "optimal_route": {
                "route_id": "RTE_SA_OPT",
                "track_ids": track_ids,
                "station_ids": best_path,
                "total_distance_km": best_metrics["distance_km"],
                "estimated_travel_time_min": best_metrics["travel_time_min"],
                "estimated_energy_kwh": best_metrics["energy_kwh"],
                "congestion_score": best_metrics["congestion"],
                "conflicts_count": best_metrics["conflicts"],
                "composite_score": best_metrics["score"]
            },
            "explanation": f"Simulated Annealing cooled from T={initial_temp} to {round(temperature, 2)}; composite cost: {best_metrics['score']}."
        }
