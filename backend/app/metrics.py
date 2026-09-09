"""Prometheus Metrics Instrumentations for Railway Traffic Management Subsystems."""
from prometheus_client import Counter, Histogram, Gauge

# HTTP Metrics
http_requests_total = Counter(
    "railway_http_requests_total",
    "Total count of HTTP requests processed by the API gateway",
    ["method", "endpoint", "status"]
)

http_request_duration_seconds = Histogram(
    "railway_http_request_duration_seconds",
    "HTTP request latency in seconds across endpoints",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
)

# Simulation & Operations Metrics
railway_active_trains = Gauge(
    "railway_active_trains",
    "Number of active trains currently operating on the network"
)

railway_simulation_steps_total = Counter(
    "railway_simulation_steps_total",
    "Total discrete simulation step cycles executed"
)

railway_simulation_step_duration_seconds = Histogram(
    "railway_simulation_step_duration_seconds",
    "Time taken to execute an individual simulation step cycle",
    buckets=(0.001, 0.005, 0.01, 0.02, 0.05, 0.1)
)

# Conflicts & Safety Metrics
railway_conflicts_total = Counter(
    "railway_conflicts_total",
    "Total conflicts identified by the conflict detection arbiter",
    ["severity", "conflict_type"]
)

railway_active_conflicts = Gauge(
    "railway_active_conflicts",
    "Number of unresolved conflicts currently active"
)

# AI & Prediction Metrics
railway_ai_inferences_total = Counter(
    "railway_ai_inferences_total",
    "Total inference executions across predictive AI models",
    ["task", "model_id"]
)

railway_ai_inference_duration_seconds = Histogram(
    "railway_ai_inference_duration_seconds",
    "Latency of predictive model inference executions",
    ["task"],
    buckets=(0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.25)
)

# Optimization Metrics
railway_optimization_runs_total = Counter(
    "railway_optimization_runs_total",
    "Total mathematical and heuristic optimization solver executions",
    ["algorithm"]
)

railway_optimization_duration_seconds = Histogram(
    "railway_optimization_duration_seconds",
    "Duration of optimization algorithm runs",
    ["algorithm"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 3.0)
)

# WebSocket Real-Time Metrics
railway_websocket_connections = Gauge(
    "railway_websocket_connections",
    "Count of active WebSocket connections streaming telemetry"
)
