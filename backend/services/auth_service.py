"""Authentication and User Service."""
from typing import Optional
from sqlalchemy.orm import Session
from backend.models.user import User, AuditLog
from backend.schemas.auth import UserCreate, UserLogin, Token
from backend.app.security import get_password_hash, verify_password, create_access_token

class AuthService:
    @classmethod
    def create_user(cls, db: Session, user_in: UserCreate) -> User:
        hashed_pwd = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_pwd,
            full_name=user_in.full_name,
            role=user_in.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @classmethod
    def authenticate(cls, db: Session, login_data: UserLogin) -> Optional[Token]:
        user = db.query(User).filter(User.username == login_data.username).first()
        if not user or not verify_password(login_data.password, user.hashed_password):
            return None
        if not user.is_active:
            return None
            
        token_str = create_access_token(data={"sub": user.username, "role": user.role, "uid": user.id})
        return Token(access_token=token_str, token_type="bearer", role=user.role, username=user.username)

    @classmethod
    def log_audit(cls, db: Session, user_id: Optional[int], action: str, resource_type: str, resource_id: str, details: str = None):
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details
        )
        db.add(log)
        db.commit()
