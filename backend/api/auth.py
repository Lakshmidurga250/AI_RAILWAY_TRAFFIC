"""Authentication API Endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.schemas.auth import UserLogin, UserCreate, Token, UserResponse
from backend.services.auth_service import AuthService
from backend.app.dependencies import require_auth
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.username == user_in.username) | (User.email == user_in.email)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")
    user = AuthService.create_user(db, user_in)
    AuthService.log_audit(db, user.id, "USER_REGISTERED", "USER", str(user.id))
    return user

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    token = AuthService.authenticate(db, login_data)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return token

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: User = Depends(require_auth)):
    return user
