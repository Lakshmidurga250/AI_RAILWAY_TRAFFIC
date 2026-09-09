"""Role and Permission repository providing RBAC management."""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from backend.models.user import Role, Permission, RolePermission
from backend.repositories.base import BaseRepository

STANDARD_PERMISSIONS = [
    # Trains
    ("trains:read", "trains", "View train telemetries, details, and schedules"),
    ("trains:write", "trains", "Create and modify train configurations and priorities"),
    ("trains:delete", "trains", "Remove or cancel train routes"),
    # Infrastructure
    ("stations:read", "network", "View stations, platforms, and track occupancy"),
    ("stations:write", "network", "Modify station configurations and platform assignments"),
    ("tracks:read", "network", "View tracks, speed limits, and signal states"),
    ("tracks:write", "network", "Set track closures, maintenance, and speed restrictions"),
    # Simulation & Operations
    ("simulation:control", "simulation", "Start, pause, step, and reset discrete-event simulation"),
    ("optimization:run", "optimization", "Trigger Pareto routing, timetable and eco-driving optimization"),
    ("ai:predict", "ai", "Invoke delay, congestion, and passenger demand models"),
    # Analytics & Reports
    ("analytics:view", "analytics", "Access throughput, punctuality, and fleet telemetry analytics"),
    ("reports:generate", "reports", "Generate system performance and incident audit reports"),
    # Administration
    ("users:manage", "security", "Manage user profiles, credentials, and RBAC assignments"),
    ("system:admin", "security", "Full unrestricted administrative access across all domains"),
]

ROLE_PERMISSION_MAP: Dict[str, List[str]] = {
    "admin": [p[0] for p in STANDARD_PERMISSIONS],
    "dispatcher": [
        "trains:read", "trains:write",
        "stations:read", "stations:write",
        "tracks:read", "tracks:write",
        "simulation:control",
        "optimization:run",
        "ai:predict",
        "analytics:view",
        "reports:generate",
    ],
    "operator": [
        "trains:read", "trains:write",
        "stations:read",
        "tracks:read",
        "simulation:control",
        "analytics:view",
    ],
    "viewer": [
        "trains:read",
        "stations:read",
        "tracks:read",
        "analytics:view",
        "reports:generate",
    ],
}

class RoleRepository(BaseRepository[Role]):
    """Role management and RBAC policy persistence."""

    def __init__(self, db: Session):
        super().__init__(Role, db)

    def get_by_name(self, name: str) -> Optional[Role]:
        """Fetch role by unique name."""
        return self.db.query(Role).filter(Role.name == name).first()

    def get_permission_by_name(self, perm_name: str) -> Optional[Permission]:
        """Fetch permission by unique name."""
        return self.db.query(Permission).filter(Permission.name == perm_name).first()

    def list_all_permissions(self) -> List[Permission]:
        """List all available system permissions."""
        return self.db.query(Permission).order_by(Permission.category, Permission.name).all()

    def assign_permission_to_role(self, role_id: int, permission_id: int) -> bool:
        """Link a permission to a role."""
        existing = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()
        if existing:
            return False
        
        rp = RolePermission(role_id=role_id, permission_id=permission_id)
        self.db.add(rp)
        self.db.commit()
        return True

    def seed_defaults(self):
        """Seed standard permissions, system roles, and default mappings."""
        # 1. Seed permissions
        perm_cache: Dict[str, Permission] = {}
        for code, category, desc in STANDARD_PERMISSIONS:
            perm = self.get_permission_by_name(code)
            if not perm:
                perm = Permission(name=code, category=category, description=desc)
                self.db.add(perm)
                self.db.commit()
                self.db.refresh(perm)
            perm_cache[code] = perm

        # 2. Seed roles and link permissions
        for role_name, perms in ROLE_PERMISSION_MAP.items():
            role_obj = self.get_by_name(role_name)
            if not role_obj:
                role_obj = Role(
                    name=role_name,
                    description=f"Standard system {role_name} role",
                    is_system=True
                )
                self.db.add(role_obj)
                self.db.commit()
                self.db.refresh(role_obj)

            # Link permissions
            for p_code in perms:
                p_obj = perm_cache.get(p_code)
                if p_obj:
                    self.assign_permission_to_role(role_obj.id, p_obj.id)
