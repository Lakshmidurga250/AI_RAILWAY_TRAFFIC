"""Security utilities: password hashing, JWT tokens, RBAC."""
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from backend.app.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using salted SHA-256 with constant-time comparison."""
    try:
        if "$" in hashed_password:
            parts = hashed_password.split("$")
            if len(parts) == 3 and parts[0] == "sha256":
                salt = parts[1]
                expected_hash = parts[2]
                computed = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
                return hmac.compare_digest(computed, expected_hash)
        # Fallback for plain hex or older hashes
        return hmac.compare_digest(hashlib.sha256(plain_password.encode("utf-8")).hexdigest(), hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Generate salted hash for password."""
    import secrets
    salt = secrets.token_hex(8)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"sha256${salt}${h}"

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Encode JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
