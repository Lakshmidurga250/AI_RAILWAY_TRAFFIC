# Contribution & Engineering Guidelines

Thank you for contributing to the **AI Railway Traffic Optimization System**. This document outlines our development workflows, code standards, test requirements, and Git conventions.

---

## 1. Development Workflow

1. **Fork or Branch**: Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Environment Setup**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or .venv\Scripts\Activate.ps1 on Windows
   pip install -r requirements.txt
   ```
3. **Run Existing Tests**: Verify all tests pass before making modifications:
   ```bash
   python -m pytest -v
   ```

---

## 2. Code Quality & Standards

- **Python**: Target Python 3.12+ (tested through 3.14). Follow PEP 8 style standards with strict type hints.
- **Pydantic**: Use pure **Pydantic v2** conventions with `model_config = ConfigDict(from_attributes=True)`. Avoid deprecated v1 `class Config`.
- **FastAPI / ASGI**: Avoid blocking I/O calls in `async def` endpoints. Keep middleware as pure ASGI callables to prevent event loop stalls.
- **Safety**: Maintain the advisory boundary. Never couple AI or heuristic outputs directly to hardware without human-in-the-loop and validation checks.

---

## 3. Git Commit Conventions (Phase 47 Compliance)

All commits must follow the **Conventional Commits** specification:

```
<type>(<scope>): <short description>
```

### Allowed Types:
- `feat`: New feature or capability (e.g., `feat: implement route optimization`)
- `fix`: Bug fix (e.g., `fix: resolve platform assignment conflict`)
- `perf`: Performance optimization (e.g., `perf: optimize graph routing`)
- `test`: Adding or updating test suites (e.g., `test: add simulation property tests`)
- `docs`: Documentation updates (e.g., `docs: add deployment guide`)
- `refactor`: Code reorganization without functional changes
- `ci`: CI/CD workflow modifications

---

## 4. Pull Request Checklist

Before submitting a Pull Request:
- [ ] All 62 automated tests pass cleanly (`python -m pytest -v`).
- [ ] Invariant property tests in `tests/test_properties.py` succeed.
- [ ] Performance benchmarks in `tests/test_performance.py` meet latency thresholds.
- [ ] New endpoints are documented in `docs/API_DOCUMENTATION.md`.
- [ ] No temporary files or test artifacts committed.
