from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    refresh_token: Optional[str] = None
    permissions: Optional[List[str]] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "dispatcher"

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    permissions: Optional[List[str]] = []

    model_config = ConfigDict(from_attributes=True)

class PermissionSchema(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RoleSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_system: bool
    permissions: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class UserRoleAssignRequest(BaseModel):
    user_id: int
    role_name: str

class SystemEventResponse(BaseModel):
    id: int
    event_type: str
    severity: str
    source_module: str
    details: Optional[str] = None
    user_id: Optional[int] = None
    request_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
