"""User repository providing domain access for users and their credentials."""
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.models.user import User, Role, UserRole, Permission
from backend.repositories.base import BaseRepository

class UserRepository(BaseRepository[User]):
    """User repository handling user profiles, auth data, and role assignments."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> Optional[User]:
        """Lookup user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Lookup user by email address."""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Find user by either username or email."""
        return self.db.query(User).filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

    def assign_role_to_user(self, user_id: int, role_id: int) -> bool:
        """Assign role to user via UserRole join table."""
        existing = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        if existing:
            return False
        
        user_role = UserRole(user_id=user_id, role_id=role_id)
        self.db.add(user_role)
        self.db.commit()
        return True

    def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """Remove a specific role from user."""
        user_role = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        if user_role:
            self.db.delete(user_role)
            self.db.commit()
            return True
        return False

    def get_effective_permissions(self, user: User) -> List[str]:
        """Compute complete flattened set of permission names granted to user."""
        if user.role == "admin":
            all_perms = self.db.query(Permission.name).all()
            return [p[0] for p in all_perms] + ["*"]
        
        perm_names = set()
        for role_obj in user.roles:
            if role_obj.name == "admin":
                all_perms = self.db.query(Permission.name).all()
                return [p[0] for p in all_perms] + ["*"]
            for perm in role_obj.permissions:
                perm_names.add(perm.name)
                
        # Also map legacy single-role string if no relation records exist
        if not perm_names:
            role_obj = self.db.query(Role).filter(Role.name == user.role).first()
            if role_obj:
                for perm in role_obj.permissions:
                    perm_names.add(perm.name)
        return sorted(list(perm_names))
