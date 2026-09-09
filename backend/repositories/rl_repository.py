"""Reinforcement Learning Database Repository."""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.repositories.base import BaseRepository
from backend.models.ai import RLTrainingRun, RLDispatchActionLog


class RLRepository(BaseRepository[RLTrainingRun]):
    """Repository for managing Reinforcement Learning training records and dispatch telemetry."""

    def __init__(self, db: Session):
        super().__init__(RLTrainingRun, db)

    def record_training_run(
        self,
        run_id: str,
        algorithm: str,
        episodes_trained: int,
        mean_episode_reward: float,
        shield_interventions_count: int,
        baseline_heuristic_reward: float,
        improvement_percentage: float,
        metrics: Optional[Dict[str, Any]] = None
    ) -> RLTrainingRun:
        """Create and persist an RL training episode loop audit record."""
        run = RLTrainingRun(
            id=run_id,
            algorithm=algorithm,
            episodes_trained=episodes_trained,
            mean_episode_reward=mean_episode_reward,
            shield_interventions_count=shield_interventions_count,
            baseline_heuristic_reward=baseline_heuristic_reward,
            improvement_percentage=improvement_percentage,
            metrics=metrics or {},
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def record_dispatch_action(
        self,
        train_id: str,
        proposed_action: str,
        executed_action: str,
        algorithm: str = "DQN",
        shield_intervened: bool = False,
        safety_violations: Optional[List[str]] = None,
        reward: float = 0.0,
        explanation: Optional[str] = None
    ) -> RLDispatchActionLog:
        """Record an individual RL-driven dispatch decision."""
        log = RLDispatchActionLog(
            train_id=train_id,
            algorithm=algorithm,
            proposed_action=proposed_action,
            executed_action=executed_action,
            shield_intervened=shield_intervened,
            safety_violations=safety_violations or [],
            reward=reward,
            explanation=explanation,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_recent_training_runs(
        self,
        limit: int = 20,
        algorithm: Optional[str] = None
    ) -> List[RLTrainingRun]:
        """Fetch latest RL training runs ordered by creation timestamp."""
        query = self.db.query(RLTrainingRun)
        if algorithm:
            query = query.filter(RLTrainingRun.algorithm == algorithm)
        return query.order_by(RLTrainingRun.created_at.desc()).limit(limit).all()

    def get_recent_dispatch_logs(
        self,
        limit: int = 50,
        train_id: Optional[str] = None
    ) -> List[RLDispatchActionLog]:
        """Fetch recent dispatch action logs with shield verification history."""
        query = self.db.query(RLDispatchActionLog)
        if train_id:
            query = query.filter(RLDispatchActionLog.train_id == train_id)
        return query.order_by(RLDispatchActionLog.timestamp.desc()).limit(limit).all()
