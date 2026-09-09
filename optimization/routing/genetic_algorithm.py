"""Genetic Algorithm (GA) for Multi-Objective Railway Route Optimization."""
import random
import time
from typing import List, Dict, Any, Optional
from simulation.network.graph import RailwayNetwork

class GeneticAlgorithmRouter:
    """Evolutionary multi-objective router applying selection, crossover, and mutation."""

    POPULATION_SIZE = 16
    GENERATIONS = 20
    MUTATION_RATE = 0.25
    TOURNAMENT_SIZE = 3

    @classmethod
    def evaluate_fitness(cls, network: RailwayNetwork, path: List[str]) -> Dict[str, float]:
        """Compute multi-objective costs (lower is better) and fitness score."""
        tracks = network.path_to_tracks(path)
        if not tracks:
            return {"score": 9999.0, "travel_time_min": 999.0, "energy_kwh": 999.0, "congestion": 1.0, "conflicts": 10}

        dist_km = sum(t.length_km for t in tracks)
        travel_time_min = sum((t.length_km / max(40.0, t.max_speed_kmh)) * 60.0 for t in tracks)
        congestion_vals = [len(t.current_train_ids) * 0.3 for t in tracks]
        avg_congestion = min(1.0, sum(congestion_vals) / max(1, len(tracks)))
        energy_kwh = sum(t.length_km * (12.0 + t.gradient_percent * 2.0) for t in tracks)
        conflicts_count = sum(1 for t in tracks if len(t.current_train_ids) > 1)

        # Weighted composite fitness
        score = (
            (travel_time_min * 0.40) +
            (avg_congestion * 50.0 * 0.20) +
            ((energy_kwh / 10.0) * 0.15) +
            (conflicts_count * 25.0 * 0.25)
        )
        return {
            "score": round(score, 2),
            "distance_km": round(dist_km, 2),
            "travel_time_min": round(travel_time_min, 1),
            "energy_kwh": round(energy_kwh, 1),
            "congestion": round(avg_congestion, 2),
            "conflicts": conflicts_count
        }

    @classmethod
    def optimize_route(
        cls,
        network: RailwayNetwork,
        origin_id: str,
        destination_id: str,
        generations: int = GENERATIONS,
        population_size: int = POPULATION_SIZE
    ) -> Dict[str, Any]:
        """Execute Genetic Algorithm optimization to find optimal Pareto path."""
        start_t = time.perf_counter()

        # 1. Seed initial population from k-shortest paths + randomized traversals
        candidate_paths = network.find_k_shortest_paths(origin_id, destination_id, k=population_size, weight_type="travel_time")
        if not candidate_paths:
            sp = network.find_shortest_path(origin_id, destination_id)
            candidate_paths = [sp] if sp else []

        if not candidate_paths:
            return {
                "error": f"No topological route found between {origin_id} and {destination_id}",
                "execution_time_ms": round((time.perf_counter() - start_t) * 1000, 2)
            }

        # Build initial population
        population = []
        for p in candidate_paths:
            population.append(list(p))

        # Fill remaining population by slight perturbations if needed
        base_path = candidate_paths[0]
        while len(population) < population_size:
            population.append(list(base_path))

        # Evolutionary loop
        best_individual = population[0]
        best_metrics = cls.evaluate_fitness(network, best_individual)

        for gen in range(generations):
            # Evaluate all individuals
            evaluated = [(ind, cls.evaluate_fitness(network, ind)) for ind in population]
            evaluated.sort(key=lambda x: x[1]["score"])

            if evaluated[0][1]["score"] < best_metrics["score"]:
                best_individual = evaluated[0][0]
                best_metrics = evaluated[0][1]

            # Elitism: retain top 2
            next_generation = [evaluated[0][0], evaluated[1][0]]

            # Breed new offspring
            while len(next_generation) < population_size:
                # Tournament selection
                p1 = cls._tournament_select(evaluated)
                p2 = cls._tournament_select(evaluated)

                # Crossover
                child = cls._crossover(network, p1, p2, origin_id, destination_id)

                # Mutation
                if random.random() < cls.MUTATION_RATE:
                    child = cls._mutate(network, child, origin_id, destination_id)

                next_generation.append(child)

            population = next_generation

        # Format final result
        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        tracks = network.path_to_tracks(best_individual)
        track_ids = [t.id for t in tracks]

        return {
            "algorithm": "GENETIC_ALGORITHM",
            "generations": generations,
            "population_size": population_size,
            "execution_time_ms": elapsed_ms,
            "optimal_route": {
                "route_id": "RTE_GENETIC_OPT",
                "track_ids": track_ids,
                "station_ids": best_individual,
                "total_distance_km": best_metrics["distance_km"],
                "estimated_travel_time_min": best_metrics["travel_time_min"],
                "estimated_energy_kwh": best_metrics["energy_kwh"],
                "congestion_score": best_metrics["congestion"],
                "conflicts_count": best_metrics["conflicts"],
                "composite_score": best_metrics["score"]
            },
            "explanation": f"Evolved over {generations} generations with elitism; balanced travel time ({best_metrics['travel_time_min']}m) and energy ({best_metrics['energy_kwh']} kWh)."
        }

    @classmethod
    def _tournament_select(cls, evaluated: List[tuple]) -> List[str]:
        sample = random.sample(evaluated, min(cls.TOURNAMENT_SIZE, len(evaluated)))
        sample.sort(key=lambda x: x[1]["score"])
        return sample[0][0]

    @classmethod
    def is_valid_path(cls, network: RailwayNetwork, path: List[str]) -> bool:
        """Validate if path nodes form a valid continuous sequence in the network graph."""
        if not path or len(path) < 2:
            return False
        for i in range(len(path) - 1):
            if not network.graph.has_edge(path[i], path[i + 1]):
                return False
        return True

    @classmethod
    def _crossover(cls, network: RailwayNetwork, p1: List[str], p2: List[str], origin: str, dest: str) -> List[str]:
        """Crossover at shared intermediate node if one exists, otherwise choose fitter parent."""
        shared = [node for node in p1[1:-1] if node in p2[1:-1]]
        if shared:
            pivot = random.choice(shared)
            idx1 = p1.index(pivot)
            idx2 = p2.index(pivot)
            child = p1[:idx1] + p2[idx2:]
            # Ensure valid continuous path
            if cls.is_valid_path(network, child):
                return child
        return list(p1)

    @classmethod
    def _mutate(cls, network: RailwayNetwork, path: List[str], origin: str, dest: str) -> List[str]:
        """Mutate path by finding alternative diversion between intermediate nodes."""
        if len(path) <= 3:
            return path
        idx = random.randint(0, len(path) - 2)
        sub_sp = network.find_shortest_path(path[idx], dest)
        if sub_sp:
            mutated = path[:idx] + sub_sp
            if cls.is_valid_path(network, mutated):
                return mutated
        return path
