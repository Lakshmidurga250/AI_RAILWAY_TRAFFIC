"""Authentication, Token Management, and RBAC API Endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.schemas.auth import (
    UserLogin,
    UserCreate,
    Token,
    UserResponse,
    RefreshTokenRequest,
    RoleSchema,
    PermissionSchema,
    UserRoleAssignRequest,
    SystemEventResponse
)
from backend.services.auth_service import AuthService
from backend.app.dependencies import require_auth, require_role, require_permission
from backend.models.user import User
from backend.repositories.user_repository import UserRepository
from backend.repositories.role_repository import RoleRepository
from backend.repositories.event_repository import SystemEventRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    """Register a new user account."""
    user_repo = UserRepository(db)
    existing = user_repo.get_by_username_or_email(user_in.username) or user_repo.get_by_email(user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    client_ip = request.client.host if request.client else None
    user = AuthService.create_user(db, user_in, ip_address=client_ip)
    
    perms = user_repo.get_effective_permissions(user)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        permissions=perms
    )

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Authenticate with username and password, receiving JWT and Refresh tokens."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    token = AuthService.authenticate(db, login_data, ip_address=client_ip, user_agent=user_agent)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    return token

@router.post("/refresh", response_model=Token)
def refresh_token(payload: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """Rotate refresh token and issue a fresh access token."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    token = AuthService.refresh_access_token(
        db,
        raw_refresh_token=payload.refresh_token,
        ip_address=client_ip,
        user_agent=user_agent
    )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked refresh token"
        )
    return token

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Revoke active refresh token on logout."""
    revoked = AuthService.revoke_refresh_token(db, payload.refresh_token)
    return {"status": "SUCCESS", "message": "Token revoked successfully" if revoked else "Token already inactive"}

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    """Get profile of authenticated user including effective permissions."""
    user_repo = UserRepository(db)
    perms = user_repo.get_effective_permissions(user)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        permissions=perms
    )

@router.get("/roles", response_model=List[RoleSchema])
def list_system_roles(
    current_user: User = Depends(require_role(["admin", "dispatcher"])),
    db: Session = Depends(get_db)
):
    """List system roles and their assigned permission matrix."""
    return AuthService.list_roles_and_permissions(db)

@router.get("/permissions", response_model=List[PermissionSchema])
def list_system_permissions(
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """List all available system permissions."""
    role_repo = RoleRepository(db)
    perms = role_repo.list_all_permissions()
    return perms

@router.post("/roles/assign", status_code=status.HTTP_200_OK)
def assign_role_to_user(
    payload: UserRoleAssignRequest,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Assign a role to a user (Admin only)."""
    success = AuthService.assign_user_role(db, user_id=payload.user_id, role_name=payload.role_name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not assign role '{payload.role_name}' to user {payload.user_id}"
        )
    return {"status": "SUCCESS", "message": f"Role '{payload.role_name}' assigned to user {payload.user_id}"}

@router.get("/events", response_model=List[SystemEventResponse])
def get_security_events(
    severity: Optional[str] = None,
    source_module: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Query audit and security system events (Admin only)."""
    event_repo = SystemEventRepository(db)
    return event_repo.query_events(severity=severity, source_module=source_module, limit=limit)
