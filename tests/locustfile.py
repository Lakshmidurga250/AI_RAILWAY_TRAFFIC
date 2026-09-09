"""Locust Performance Load Testing Suite for AI Railway Traffic Platform.

Simulates concurrent dispatchers querying network topology, live telemetry,
requesting multi-horizon delay predictions, and triggering route optimizations.
"""
from locust import HttpUser, task, between
import random

class RailwayDispatcherUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task(5)
    def check_health(self):
        self.client.get("/health")

    @task(10)
    def fetch_live_trains(self):
        self.client.get("/trains")

    @task(5)
    def fetch_stations(self):
        self.client.get("/stations")

    @task(5)
    def fetch_simulation_status(self):
        self.client.get("/simulation/status")

    @task(3)
    def fetch_network_graph(self):
        self.client.get("/network/graph")

    @task(4)
    def query_delay_prediction(self):
        horizons = [5, 10, 15, 30, 60]
        self.client.post("/ai/delay", json={
            "train_id": "TR_101",
            "horizon_minutes": random.choice(horizons)
        })

    @task(3)
    def optimize_route(self):
        self.client.post("/optimization/route", json={
            "origin_station_id": "ST_SOUTH",
            "destination_station_id": "ST_NORTH",
            "algorithm": random.choice(["DIJKSTRA", "A_STAR", "FLOYD_WARSHALL"])
        })

    @task(2)
    def fetch_analytics(self):
        self.client.get("/analytics/dashboard")

    @task(1)
    def fetch_operational_report(self):
        self.client.get("/reports/operational?format=json")
