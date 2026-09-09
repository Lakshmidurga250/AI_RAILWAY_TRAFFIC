"""OptimizationRun repository providing audit trails and benchmark comparisons."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.optimization import OptimizationRun
from backend.repositories.base import BaseRepository

class OptimizationRepository(BaseRepository[OptimizationRun]):
    """Repository managing optimization runs, performance metrics, and explanations."""

    def __init__(self, db: Session):
        super().__init__(OptimizationRun, db)

    def record_run(
        self,
        run_id: str,
        optimization_type: str,
        algorithm: str,
        execution_time_ms: float = 0.0,
        baseline_delay_minutes: float = 0.0,
        optimized_delay_minutes: float = 0.0,
        delay_reduction_percentage: float = 0.0,
        baseline_energy_kwh: float = 0.0,
        optimized_energy_kwh: float = 0.0,
        energy_savings_percentage: float = 0.0,
        conflicts_resolved: int = 0,
        throughput_increase_percentage: float = 0.0,
        input_parameters: Optional[Dict[str, Any]] = None,
        result_data: Optional[Dict[str, Any]] = None,
        explanation: Optional[str] = None
    ) -> OptimizationRun:
        """Persist an optimization benchmark run."""
        run = OptimizationRun(
            id=run_id,
            optimization_type=optimization_type.upper(),
            algorithm=algorithm.upper(),
            status="COMPLETED",
            execution_time_ms=execution_time_ms,
            baseline_delay_minutes=baseline_delay_minutes,
            optimized_delay_minutes=optimized_delay_minutes,
            delay_reduction_percentage=delay_reduction_percentage,
            baseline_energy_kwh=baseline_energy_kwh,
            optimized_energy_kwh=optimized_energy_kwh,
            energy_savings_percentage=energy_savings_percentage,
            conflicts_resolved=conflicts_resolved,
            throughput_increase_percentage=throughput_increase_percentage,
            input_parameters=input_parameters,
            result_data=result_data,
            explanation=explanation,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_recent_runs(self, limit: int = 50, optimization_type: Optional[str] = None) -> List[OptimizationRun]:
        """Fetch chronologically descending optimization runs."""
        query = self.db.query(OptimizationRun)
        if optimization_type:
            query = query.filter(OptimizationRun.optimization_type == optimization_type.upper())
        return query.order_by(desc(OptimizationRun.created_at)).limit(limit).all()
