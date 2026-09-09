"""Event and Audit repositories for system security and operational telemetry."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.models.user import AuditLog, SystemEvent
from backend.repositories.base import BaseRepository

class AuditLogRepository(BaseRepository[AuditLog]):
    """Audit trail repository capturing sensitive administrative and business actions."""

    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def log_action(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Record an audit trail entry."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_user_audit_history(self, user_id: int, limit: int = 50) -> List[AuditLog]:
        """Fetch audit entries performed by a given user."""
        return self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(desc(AuditLog.created_at)).limit(limit).all()

class SystemEventRepository(BaseRepository[SystemEvent]):
    """System events repository capturing auth events, warnings, alerts, and errors."""

    def __init__(self, db: Session):
        super().__init__(SystemEvent, db)

    def log_event(
        self,
        event_type: str,
        severity: str = "INFO",
        source_module: str = "system",
        details: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> SystemEvent:
        """Create and commit a structured system event entry."""
        entry = SystemEvent(
            event_type=event_type,
            severity=severity,
            source_module=source_module,
            details=details,
            user_id=user_id,
            ip_address=ip_address,
            request_id=request_id
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def query_events(
        self,
        severity: Optional[str] = None,
        source_module: Optional[str] = None,
        limit: int = 100
    ) -> List[SystemEvent]:
        """Query system events with optional severity and module filters."""
        query = self.db.query(SystemEvent)
        if severity:
            query = query.filter(SystemEvent.severity == severity.upper())
        if source_module:
            query = query.filter(SystemEvent.source_module == source_module)
        return query.order_by(desc(SystemEvent.created_at)).limit(limit).all()
