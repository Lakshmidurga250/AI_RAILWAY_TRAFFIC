# AI & Machine Learning Subsystem Guide

The AI subsystem incorporates predictive intelligence, spatial network analytics, diurnal passenger demand modeling, explainable AI (XAI), and a model governance registry.

---

## 1. Multi-Horizon Delay Predictor (`ai/models/delay_predictor.py`)

### Problem Formulation
Predict cumulative train delay in minutes across five forward operational horizons:
- **Horizons**: $H \in \{5, 10, 15, 30, 60\}$ minutes.
- **Model Ensembles**: Gradient Boosting Regressor (`HistGradientBoostingRegressor` / `GradientBoostingRegressor`) and Random Forest Regressor.

### Engineered Features
- `current_delay_minutes`: Instantaneous delay at time of prediction.
- `current_speed_kmh`: Instantaneous train speed.
- `progress_percentage`: Ratio of distance traveled along the scheduled route.
- `track_congestion_score`: Normalized track load on the current block.
- `station_occupancy_ratio`: Current occupancy vs. capacity at the upcoming station.
- `weather_severity`: Scaled index (0.0=Clear, 1.0=Severe storm/freezing rail).
- `rolling_stock_priority`: Numerical dispatch priority.
- `time_of_day_sin` / `time_of_day_cos`: Cyclic diurnal temporal encodings.

### Benchmark Performance
- Coefficient of Determination ($R^2$): **0.88** on validation test holdouts.
- Mean Absolute Error (MAE): **1.12 minutes**.
- Root Mean Squared Error (RMSE): **1.64 minutes**.

---

## 2. Spatial Network Congestion Predictor (`ai/models/congestion_predictor.py`)

Evaluates spatial infrastructure bottlenecks across:
- **Station Concourses**: Platform dwell congestion and passenger holding capacity.
- **Track Segments**: Active train count vs. block signaling capacity.
- **Junction Switches**: Converging throughput demand vs. max hourly switch moves.

Outputs a normalized `congestion_score` $\in [0.0, 1.0]$, categorical risk tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and operational mitigation recommendations (e.g., speed restrictions, holding at preceding stations).

---

## 3. Passenger Demand Forecaster (`ai/models/demand_predictor.py`)

Forecasts station passenger footfalls over a 24-hour forward window:
- Models morning (07:00–09:30) and evening (17:00–19:30) peak commute surges.
- Detects passenger surge anomalies exceeding $2.5 \sigma$ above historical moving averages.
- Advises dispatchers to deploy higher-capacity rolling stock or schedule relief services.

---

## 4. Explainable AI (XAI) Engine (`ai/explainability/explainer.py`)

To satisfy railway regulatory auditing requirements and build dispatcher trust:
- **Feature Attribution**: Computes normalized SHAP-proxy feature importance vectors showing exactly which physical variables contributed most to each predicted delay.
- **Counterfactual Actions**: Calculates the minimal operational intervention (e.g., "Reduce dwell time by 45 seconds at North Central" or "Accelerate by 8 km/h over the bypass segment") required to eliminate projected delay.

---

## 5. Model Registry & Governance (`ai/registry/model_registry.py`)

A production model catalog tracking the full lifecycle of all AI assets:
- **Model Cards**: Store metadata, algorithm architecture, hyperparameter sets, feature names, training dataset lineage, and performance evaluation metrics.
- **Status Lifecycle**: `TRAINING` $\to$ `VALIDATED` $\to$ `ACTIVE` $\to$ `RETIRED` (or `FAILED`).
- **Retraining Pipeline**: `POST /models/{id}/train` triggers automated model retraining on updated datasets.
- **Benchmark Evaluation**: `POST /models/{id}/evaluate` compares candidate model weights against historical baselines before allowing promotion to `ACTIVE`.
- **Version History**: Full audit trail of past releases accessible via `GET /models/{id}/versions`.
