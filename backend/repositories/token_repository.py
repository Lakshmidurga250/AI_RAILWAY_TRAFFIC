"""Refresh token repository for session security and revocation tracking."""
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.models.user import RefreshToken
from backend.repositories.base import BaseRepository

class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository managing active refresh tokens, expiration, and blacklisting."""

    def __init__(self, db: Session):
        super().__init__(RefreshToken, db)

    def create_token(
        self,
        user_id: int,
        token_hash: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> RefreshToken:
        """Store a new cryptographically hashed refresh token."""
        token_entry = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            is_revoked=False
        )
        self.db.add(token_entry)
        self.db.commit()
        self.db.refresh(token_entry)
        return token_entry

    def get_valid_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Fetch token if it exists, is not revoked, and is not expired."""
        now = datetime.now(timezone.utc)
        token_entry = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False
        ).first()

        if not token_entry:
            return None

        # Compare timezone-aware or naive datetimes safely
        exp = token_entry.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

        if exp < now:
            return None

        return token_entry

    def revoke_token(self, token_hash: str) -> bool:
        """Revoke a refresh token (mark invalid)."""
        token_entry = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        if token_entry and not token_entry.is_revoked:
            token_entry.is_revoked = True
            token_entry.revoked_at = datetime.now(timezone.utc)
            self.db.commit()
            return True
        return False

    def revoke_all_for_user(self, user_id: int) -> int:
        """Revoke all active refresh tokens for a specific user."""
        tokens = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).all()
        count = 0
        for t in tokens:
            t.is_revoked = True
            t.revoked_at = datetime.now(timezone.utc)
            count += 1
        if count > 0:
            self.db.commit()
        return count
