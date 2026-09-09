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

## 2. Authentication & Role-Based Access Control (RBAC)

- **Cryptographic Tokens**: Stateless JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`).
- **Password Hashing**: Industry-standard **bcrypt** with salted adaptive cost factor.
- **Roles & Permissions**:
  - `admin`: Full system control, user provisioning, model retraining, safety threshold override.
  - `dispatcher`: Route authorization, conflict resolution, timetable adjustments, scenario execution.
  - `analyst`: Read-only access to analytics, reports, telemetry streams, and model metrics.

---

## 3. Pure ASGI Security Middleware

All incoming HTTP requests and WebSocket upgrade handshakes pass through `SecurityAndMetricsMiddleware` implemented as a pure ASGI wrapper in `backend/main.py`. This design avoids Starlette's `BaseHTTPMiddleware` overhead and threadpool stalls while guaranteeing uniform security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
```

---

## 4. Input Sanitization & SQL Injection Protection

- **Pydantic v2 Strong Typing**: Every request payload undergoes strict schema validation with boundary checks (e.g., speed limits, time formats, positive values).
- **SQLAlchemy 2.0 Parameterized Queries**: All database interactions use parameterized object-relational mapping, eliminating raw SQL string concatenation and preventing SQL injection vulnerabilities.
- **Data Quality Ingestion Arbiter**: Real-time validation checks for ingested telemetry data (range enforcement, timestamp monotonicity, orphan record prevention).

---

## 5. Audit Logging & Non-Repudiation

- All critical operational actions (route overrides, conflict dismissals, custom disruption injections, model retraining triggers) are permanently recorded in the `audit_logs` table with user identity, timestamp, IP address, and payload delta.
