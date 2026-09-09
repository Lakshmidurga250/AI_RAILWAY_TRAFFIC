# AI, Machine Learning & Explainability Guide

## 1. Delay Prediction Pipeline
- **Implementation**: `ai/delay_prediction/predictor.py`
- **Algorithm**: Multi-model Gradient Boosting and Random Forest regressors tuned for specific time horizons:
  - 5 minutes (tactical block headway reaction)
  - 10 minutes (station dwell and approach prediction)
  - 15 minutes (junction sequence coordination)
  - 30 minutes (corridor routing adjustments)
  - 60 minutes (strategic rescheduling)

### Feature Vector
Extracted via `ai/features/engineering.py`:
1. `historical_delay_min`
2. `train_type_encoded` (High-Speed, InterCity, Commuter, Freight)
3. `scheduled_dwell_sec`
4. `actual_dwell_sec`
5. `platform_occupancy_rate`
6. `track_congestion_index`
7. `weather_severity`
8. `passenger_load_factor`
9. `preceding_train_delay_min`
10. `time_of_day_hour`
11. `day_of_week`
12. `track_gradient_pct`
13. `infrastructure_health_score`

---

## 2. Explainable AI (XAI) Architecture
- **Implementation**: `ai/explainability/explainer.py`
- **Output Components**:
  - Exact minute attribution per contributing factor.
  - Risk classification (`LOW`, `MODERATE`, `HIGH`, `SEVERE`).
  - Natural language narrative for dispatchers.
  - Counterfactual actionable recommendations (e.g., "Harmonizing block speed saves 2.0 minutes").

---

## 3. Reinforcement Learning Environment
- **Implementation**: `ai/reinforcement_learning/`
- **Interface**: Gymnasium `RailwayGymEnv`
- **Observation Space**: 40-dimensional continuous vector representing speeds, delays, track occupancies, and network KPIs.
- **Action Space**:
  - `0`: `HOLD_TRAIN`
  - `1`: `RELEASE_TRAIN`
  - `2`: `SPEED_REDUCTION` (60 km/h)
  - `3`: `PRIORITY_BOOST`
  - `4`: `REROUTE_ALTERNATIVE`
- **Benchmark**: Trained DQN agent achieves over 25% reward improvement compared to heuristic rule dispatching.
