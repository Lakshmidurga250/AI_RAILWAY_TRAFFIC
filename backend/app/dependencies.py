"""FastAPI request dependencies."""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.security import decode_access_token
from backend.models.user import User

security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get authenticated user or None if anonymous (for public endpoints)."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_auth(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """Ensure endpoint requires authenticated user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

def require_role(allowed_roles: list[str]):
    """Role-based authorization dependency checking single or normalized roles."""
    def role_checker(user: User = Depends(require_auth)) -> User:
        if user.role in allowed_roles:
            return user
        # Also check multi-role association
        user_role_names = [r.name for r in user.roles]
        if any(r in allowed_roles for r in user_role_names):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation not permitted. Required role in: {allowed_roles}"
        )
    return role_checker

def require_permission(required_permission: str):
    """Fine-grained RBAC permission dependency."""
    def permission_checker(user: User = Depends(require_auth)) -> User:
        if user.has_permission(required_permission):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Missing required permission '{required_permission}'"
        )
    return permission_checker

def require_any_permission(permissions: list[str]):
    """Allow access if user holds at least one of the specified permissions."""
    def multi_permission_checker(user: User = Depends(require_auth)) -> User:
        if any(user.has_permission(p) for p in permissions):
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Requires at least one permission in {permissions}"
        )
    return multi_permission_checker

