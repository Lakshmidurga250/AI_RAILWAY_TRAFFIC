"""Particle Swarm Optimization (PSO) for Railway Route and Congestion Optimization."""
import random
import time
from typing import List, Dict, Any, Optional
from simulation.network.graph import RailwayNetwork
from optimization.routing.genetic_algorithm import GeneticAlgorithmRouter

class ParticleSwarmRouter:
    """PSO swarm intelligence router finding minimum-cost multi-objective paths."""

    SWARM_SIZE = 12
    MAX_ITERATIONS = 15
    C1_COGNITIVE = 1.5
    C2_SOCIAL = 1.5

    @classmethod
    def optimize_route(
        cls,
        network: RailwayNetwork,
        origin_id: str,
        destination_id: str,
        iterations: int = MAX_ITERATIONS,
        swarm_size: int = SWARM_SIZE
    ) -> Dict[str, Any]:
        """Execute Particle Swarm Optimization over candidate path topologies."""
        start_t = time.perf_counter()

        # Seed candidate paths from network topology
        candidates = network.find_k_shortest_paths(origin_id, destination_id, k=swarm_size, weight_type="travel_time")
        if not candidates:
            sp = network.find_shortest_path(origin_id, destination_id)
            candidates = [sp] if sp else []

        if not candidates:
            return {
                "error": f"No topological route found between {origin_id} and {destination_id}",
                "execution_time_ms": round((time.perf_counter() - start_t) * 1000, 2)
            }

        # Initialize particles with position, velocity, and personal best
        particles = []
        for i in range(swarm_size):
            path = list(candidates[i % len(candidates)])
            fit = GeneticAlgorithmRouter.evaluate_fitness(network, path)
            particles.append({
                "position": path,
                "velocity": random.uniform(0.1, 0.9),
                "pbest_position": list(path),
                "pbest_score": fit["score"],
                "metrics": fit
            })

        # Determine initial gbest (global best)
        particles.sort(key=lambda p: p["pbest_score"])
        gbest_position = list(particles[0]["pbest_position"])
        gbest_metrics = dict(particles[0]["metrics"])

        # Swarm iteration loop
        for it in range(iterations):
            for p in particles:
                # Update velocity: v = w*v + c1*r1*(pbest - pos) + c2*r2*(gbest - pos)
                r1 = random.random()
                r2 = random.random()
                inertia = 0.7 - (0.3 * (it / max(1, iterations)))
                new_v = (inertia * p["velocity"]) + (cls.C1_COGNITIVE * r1 * 0.5) + (cls.C2_SOCIAL * r2 * 0.5)
                p["velocity"] = max(0.1, min(1.0, new_v))

                # Perturb position towards gbest or alternative bypass
                if random.random() < p["velocity"] and len(gbest_position) > 2:
                    # Attempt guided crossover towards gbest
                    shared = [n for n in p["position"][1:-1] if n in gbest_position[1:-1]]
                    if shared:
                        pivot = random.choice(shared)
                        i1 = p["position"].index(pivot)
                        i2 = gbest_position.index(pivot)
                        candidate_pos = p["position"][:i1] + gbest_position[i2:]
                        if GeneticAlgorithmRouter.is_valid_path(network, candidate_pos):
                            p["position"] = candidate_pos

                # Evaluate new position
                current_fit = GeneticAlgorithmRouter.evaluate_fitness(network, p["position"])
                if current_fit["score"] < p["pbest_score"]:
                    p["pbest_position"] = list(p["position"])
                    p["pbest_score"] = current_fit["score"]
                    p["metrics"] = current_fit

                    if current_fit["score"] < gbest_metrics["score"]:
                        gbest_position = list(p["position"])
                        gbest_metrics = dict(current_fit)

        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        tracks = network.path_to_tracks(gbest_position)
        track_ids = [t.id for t in tracks]

        return {
            "algorithm": "PARTICLE_SWARM",
            "iterations": iterations,
            "swarm_size": swarm_size,
            "execution_time_ms": elapsed_ms,
            "optimal_route": {
                "route_id": "RTE_PSO_OPT",
                "track_ids": track_ids,
                "station_ids": gbest_position,
                "total_distance_km": gbest_metrics["distance_km"],
                "estimated_travel_time_min": gbest_metrics["travel_time_min"],
                "estimated_energy_kwh": gbest_metrics["energy_kwh"],
                "congestion_score": gbest_metrics["congestion"],
                "conflicts_count": gbest_metrics["conflicts"],
                "composite_score": gbest_metrics["score"]
            },
            "explanation": f"Particle Swarm converged over {iterations} iterations with swarm size {swarm_size}; composite score: {gbest_metrics['score']}."
        }
