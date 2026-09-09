"""Authentication and RBAC Service utilizing the Repository Layer."""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.models.user import User, AuditLog, SystemEvent
from backend.schemas.auth import UserCreate, UserLogin, Token, RoleSchema, PermissionSchema
from backend.app.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token_value,
    hash_token_value
)
from backend.repositories.user_repository import UserRepository
from backend.repositories.role_repository import RoleRepository
from backend.repositories.token_repository import RefreshTokenRepository
from backend.repositories.event_repository import AuditLogRepository, SystemEventRepository

REFRESH_TOKEN_LIFETIME_DAYS = 7

class AuthService:
    """Service orchestrating authentication, JWT token issuance, session refresh, and RBAC."""

    @classmethod
    def create_user(cls, db: Session, user_in: UserCreate, ip_address: Optional[str] = None) -> User:
        user_repo = UserRepository(db)
        role_repo = RoleRepository(db)
        event_repo = SystemEventRepository(db)

        # 1. Ensure system roles exist
        role_repo.seed_defaults()

        # 2. Hash password & persist
        hashed_pwd = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_pwd,
            full_name=user_in.full_name,
            role=user_in.role
        )
        user = user_repo.create(db_user)

        # 3. Associate normalized role
        target_role = role_repo.get_by_name(user_in.role)
        if target_role:
            user_repo.assign_role_to_user(user.id, target_role.id)

        # 4. Log event
        event_repo.log_event(
            event_type="USER_REGISTERED",
            severity="INFO",
            source_module="auth",
            details=f"New user registered: {user.username} with role {user.role}",
            user_id=user.id,
            ip_address=ip_address
        )
        return user

    @classmethod
    def authenticate(
        cls,
        db: Session,
        login_data: UserLogin,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Token]:
        user_repo = UserRepository(db)
        token_repo = RefreshTokenRepository(db)
        event_repo = SystemEventRepository(db)

        user = user_repo.get_by_username(login_data.username)
        if not user or not verify_password(login_data.password, user.hashed_password) or not user.is_active:
            event_repo.log_event(
                event_type="AUTH_LOGIN_FAILED",
                severity="WARNING",
                source_module="auth",
                details=f"Failed login attempt for username: {login_data.username}",
                ip_address=ip_address
            )
            return None

        # Effective permissions
        permissions = user_repo.get_effective_permissions(user)

        # Generate access token
        token_data = {
            "sub": user.username,
            "role": user.role,
            "uid": user.id,
            "perms": permissions
        }
        access_token_str = create_access_token(data=token_data)

        # Generate & store refresh token
        raw_refresh_token = create_refresh_token_value()
        token_hash = hash_token_value(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)

        token_repo.create_token(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

        event_repo.log_event(
            event_type="AUTH_LOGIN_SUCCESS",
            severity="INFO",
            source_module="auth",
            details=f"User {user.username} authenticated successfully",
            user_id=user.id,
            ip_address=ip_address
        )

        return Token(
            access_token=access_token_str,
            token_type="bearer",
            role=user.role,
            username=user.username,
            refresh_token=raw_refresh_token,
            permissions=permissions
        )

    @classmethod
    def refresh_access_token(
        cls,
        db: Session,
        raw_refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Token]:
        """Rotate refresh token and issue a fresh access token."""
        token_repo = RefreshTokenRepository(db)
        user_repo = UserRepository(db)
        event_repo = SystemEventRepository(db)

        old_hash = hash_token_value(raw_refresh_token)
        valid_entry = token_repo.get_valid_token(old_hash)

        if not valid_entry:
            event_repo.log_event(
                event_type="TOKEN_REFRESH_FAILED",
                severity="WARNING",
                source_module="auth",
                details="Attempted token refresh with invalid or expired token",
                ip_address=ip_address
            )
            return None

        user = user_repo.get(valid_entry.user_id)
        if not user or not user.is_active:
            token_repo.revoke_token(old_hash)
            return None

        # Revoke old refresh token (Token rotation)
        token_repo.revoke_token(old_hash)

        # Issue new token pair
        permissions = user_repo.get_effective_permissions(user)
        access_token_str = create_access_token(data={
            "sub": user.username,
            "role": user.role,
            "uid": user.id,
            "perms": permissions
        })

        new_refresh_token = create_refresh_token_value()
        new_token_hash = hash_token_value(new_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_LIFETIME_DAYS)

        token_repo.create_token(
            user_id=user.id,
            token_hash=new_token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )

        event_repo.log_event(
            event_type="TOKEN_REFRESHED",
            severity="INFO",
            source_module="auth",
            details=f"Token rotated and refreshed for user {user.username}",
            user_id=user.id,
            ip_address=ip_address
        )

        return Token(
            access_token=access_token_str,
            token_type="bearer",
            role=user.role,
            username=user.username,
            refresh_token=new_refresh_token,
            permissions=permissions
        )

    @classmethod
    def revoke_refresh_token(cls, db: Session, raw_refresh_token: str) -> bool:
        """Revoke a refresh token on logout."""
        token_repo = RefreshTokenRepository(db)
        old_hash = hash_token_value(raw_refresh_token)
        return token_repo.revoke_token(old_hash)

    @classmethod
    def assign_user_role(cls, db: Session, user_id: int, role_name: str) -> bool:
        """Assign role to user and update primary role string."""
        user_repo = UserRepository(db)
        role_repo = RoleRepository(db)

        role_obj = role_repo.get_by_name(role_name)
        if not role_obj:
            return False

        user = user_repo.get(user_id)
        if not user:
            return False

        user.role = role_name
        db.commit()
        return user_repo.assign_role_to_user(user_id, role_obj.id)

    @classmethod
    def list_roles_and_permissions(cls, db: Session) -> List[Dict[str, Any]]:
        """List all system roles with assigned permissions."""
        role_repo = RoleRepository(db)
        roles = role_repo.list()
        result = []
        for r in roles:
            result.append({
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "is_system": r.is_system,
                "permissions": [p.name for p in r.permissions]
            })
        return result

    @classmethod
    def log_audit(
        cls,
        db: Session,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """Record an audit trail action."""
        audit_repo = AuditLogRepository(db)
        return audit_repo.log_action(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
