# Security Architecture & Operations Guide

The AI Railway Traffic Optimization System is engineered with defense-in-depth security principles to safeguard operational railway infrastructure, fleet telemetry, and dispatching commands.

---

## 1. Threat Model & Safety Boundaries

### Advisory vs. Safety-Critical Boundary (EN-50128)
In compliance with international railway engineering guidelines (such as CENELEC EN-50128 and IEC 62278):
- The platform functions strictly as an **Advisory Decision-Support and Simulation System**.
- The AI prediction models and mathematical optimization algorithms **do NOT directly command physical track interlocking actuators or train braking relays**.
- All route assignments, speed profile modifications, and switch alignments must pass through certified fail-safe railway interlockings (SIL-4) and certified human dispatchers.

---

## 2. Authentication, Session Security & Granular RBAC

- **Cryptographic Tokens**: Stateless JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`) for low-latency request authentication.
- **Refresh Token Lifecycle & Rotation**:
  - Long-lived refresh tokens (7-day validity) cryptographically hashed (SHA-256) prior to storage in `refresh_tokens`.
  - Automatic token rotation upon refresh: when a refresh token is presented at `POST /auth/refresh`, it is immediately revoked and a new access/refresh token pair is issued to prevent replay attacks.
  - Revocation support at `POST /auth/logout` and bulk user session termination.
- **Password Hashing**: Salted secure hashing with constant-time verification against timing attacks.
- **Layered Architecture Integration**: All authorization and identity querying is decoupled via `UserRepository`, `RoleRepository`, `RefreshTokenRepository`, and `SystemEventRepository`.
- **Granular Permissions & Role Matrix**:
  - Permissions are discrete action strings across system domains:
    - `trains:read`, `trains:write`, `trains:delete`
    - `stations:read`, `stations:write`
    - `tracks:read`, `tracks:write`
    - `simulation:control`
    - `optimization:run`
    - `ai:predict`
    - `analytics:view`
    - `reports:generate`
    - `users:manage`, `system:admin`
  - Normalized join tables `user_roles` and `role_permissions` allow dynamic role and permission assignments.
  - Built-in roles:
    - `admin`: Unrestricted administrative and system control (`*`, `system:admin`, all permissions).
    - `dispatcher`: Route authorization, train adjustments, simulation control, optimization triggers, and operational reports.
    - `operator`: Real-time fleet tracking, station monitoring, and simulation supervision.
    - `viewer`: Read-only access to maps, analytics dashboards, and system status.

---

## 3. Pure ASGI Security & Distributed Tracing Middleware

All incoming HTTP requests and WebSocket upgrade handshakes pass through `SecurityAndMetricsMiddleware` implemented as a high-performance pure ASGI wrapper in `backend/main.py`. This design guarantees uniform security headers and end-to-end distributed tracing:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
X-Request-ID: <uuid4 / distributed trace id>
```

---

## 4. Input Sanitization & SQL Injection Protection

- **Pydantic v2 Strong Typing**: Every request payload undergoes strict schema validation with boundary checks (e.g., speed limits, time formats, positive values).
- **SQLAlchemy 2.0 Parameterized Queries**: All database interactions use parameterized object-relational mapping, eliminating raw SQL string concatenation and preventing SQL injection vulnerabilities.
- **Data Quality Ingestion Arbiter**: Real-time validation checks for ingested telemetry data (range enforcement, timestamp monotonicity, orphan record prevention).

---

## 5. Audit Logging & System Security Events

- **Audit Logs (`audit_logs`)**: Records administrative actions, route overrides, conflict dismissals, custom disruption injections, and model retraining triggers with user identity, timestamp, IP address, and payload delta.
- **System Events (`system_events`)**: Structured, queryable security telemetry capturing authentication events (`AUTH_LOGIN_SUCCESS`, `AUTH_LOGIN_FAILED`, `TOKEN_REFRESHED`, `USER_REGISTERED`), severity levels (`INFO`, `WARNING`, `ERROR`), source modules, and associated Request IDs.

