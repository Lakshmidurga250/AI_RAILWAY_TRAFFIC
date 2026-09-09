"""Tests for Layered Repositories, RBAC, and Refresh Token Security."""
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.database import SessionLocal, engine, Base
from backend.models.user import User, Role, Permission, UserRole, RefreshToken, SystemEvent
from backend.repositories.user_repository import UserRepository
from backend.repositories.role_repository import RoleRepository
from backend.repositories.token_repository import RefreshTokenRepository
from backend.repositories.event_repository import AuditLogRepository, SystemEventRepository
from backend.services.auth_service import AuthService
from backend.schemas.auth import UserCreate, UserLogin, RefreshTokenRequest

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_role_and_permission_seeding(db):
    """Verify default RBAC roles and permissions are properly seeded."""
    role_repo = RoleRepository(db)
    role_repo.seed_defaults()

    admin_role = role_repo.get_by_name("admin")
    dispatcher_role = role_repo.get_by_name("dispatcher")
    operator_role = role_repo.get_by_name("operator")
    viewer_role = role_repo.get_by_name("viewer")

    assert admin_role is not None
    assert dispatcher_role is not None
    assert operator_role is not None
    assert viewer_role is not None

    # Check permissions on dispatcher
    dispatcher_perms = [p.name for p in dispatcher_role.permissions]
    assert "trains:read" in dispatcher_perms
    assert "simulation:control" in dispatcher_perms
    assert "users:manage" not in dispatcher_perms

def test_user_repository_crud_and_permissions(db):
    """Test UserRepository operations, role assignment, and permission resolution."""
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    role_repo.seed_defaults()

    unique_username = f"op_test_{int(datetime.now().timestamp())}"
    user = User(
        username=unique_username,
        email=f"{unique_username}@railway-ai.internal",
        hashed_password="hashed_pass_placeholder",
        full_name="Test Operator",
        role="operator"
    )
    created_user = user_repo.create(user)
    assert created_user.id is not None

    # Assign operator role
    operator_role = role_repo.get_by_name("operator")
    assigned = user_repo.assign_role_to_user(created_user.id, operator_role.id)
    assert assigned is True

    # Check effective permissions
    perms = user_repo.get_effective_permissions(created_user)
    assert "trains:read" in perms
    assert "simulation:control" in perms
    assert created_user.has_permission("trains:read") is True
    assert created_user.has_permission("users:manage") is False

def test_refresh_token_lifecycle(db):
    """Test token repository lifecycle: creation, validation, rotation, and revocation."""
    token_repo = RefreshTokenRepository(db)
    user_repo = UserRepository(db)

    # Get or create a user
    admin = user_repo.get_by_username("admin")
    assert admin is not None

    # 1. Create token
    import uuid
    raw_hash = f"test_hash_{uuid.uuid4()}"
    future_exp = datetime.now(timezone.utc) + timedelta(days=7)
    token_repo.create_token(
        user_id=admin.id,
        token_hash=raw_hash,
        expires_at=future_exp,
        ip_address="127.0.0.1"
    )

    # 2. Validate token
    valid_entry = token_repo.get_valid_token(raw_hash)
    assert valid_entry is not None
    assert valid_entry.user_id == admin.id

    # 3. Revoke token
    revoked = token_repo.revoke_token(raw_hash)
    assert revoked is True

    # 4. Ensure no longer valid
    assert token_repo.get_valid_token(raw_hash) is None

def test_auth_login_with_refresh_token(client):
    """Test that login returns both access token and refresh token with permissions list."""
    res = client.post("/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["refresh_token"] is not None
    assert "permissions" in data
    assert "*" in data["permissions"] or "system:admin" in data["permissions"]

def test_refresh_token_rotation_endpoint(client):
    """Test token rotation flow via POST /auth/refresh."""
    # 1. Login
    login_res = client.post("/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    assert login_res.status_code == 200
    initial_refresh = login_res.json()["refresh_token"]

    # 2. Refresh token
    refresh_res = client.post("/auth/refresh", json={"refresh_token": initial_refresh})
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    new_access_token = refresh_data["access_token"]
    new_refresh_token = refresh_data["refresh_token"]

    assert new_access_token is not None
    assert new_refresh_token is not None
    assert new_refresh_token != initial_refresh  # Must rotate!

    # 3. Old refresh token should now be rejected (prevent replay)
    replay_res = client.post("/auth/refresh", json={"refresh_token": initial_refresh})
    assert replay_res.status_code == 401

def test_auth_logout_revocation(client):
    """Test logout endpoint revoking refresh token."""
    login_res = client.post("/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    assert login_res.status_code == 200
    rf_token = login_res.json()["refresh_token"]

    # Logout
    logout_res = client.post("/auth/logout", json={"refresh_token": rf_token})
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "SUCCESS"

    # Attempting to refresh with logged-out token must fail
    fail_res = client.post("/auth/refresh", json={"refresh_token": rf_token})
    assert fail_res.status_code == 401

def test_request_id_tracing_header(client):
    """Verify ASGI middleware injects X-Request-ID and security headers."""
    res = client.get("/health")
    assert res.status_code == 200
    assert "x-request-id" in res.headers
    assert "x-content-type-options" in res.headers

def test_rbac_roles_and_permissions_endpoints(client):
    """Test /auth/roles and /auth/permissions API endpoints."""
    # Login as admin
    login_res = client.post("/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query roles
    roles_res = client.get("/auth/roles", headers=headers)
    assert roles_res.status_code == 200
    roles = roles_res.json()
    role_names = [r["name"] for r in roles]
    assert "admin" in role_names
    assert "dispatcher" in role_names

    # Query permissions
    perms_res = client.get("/auth/permissions", headers=headers)
    assert perms_res.status_code == 200
    perms = perms_res.json()
    perm_codes = [p["name"] for p in perms]
    assert "trains:read" in perm_codes
    assert "simulation:control" in perm_codes
