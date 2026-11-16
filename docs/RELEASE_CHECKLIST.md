# FlowPilot AI — Production Release Checklist

Use this checklist prior to every staging and production release.

---

## 1. Code Quality & Test Verification

- [ ] **Backend Test Suite**: All 30 unit, integration, and security tests pass cleanly:
  ```bash
  $env:PYTHONPATH='backend'; backend\.venv\Scripts\pytest.exe backend/tests -v
  ```
- [ ] **Frontend Linting**: ESLint completes with 0 errors:
  ```bash
  npm --prefix frontend run lint
  ```
- [ ] **Production Next.js Build**: All routes compile and statically prerender cleanly:
  ```bash
  npm --prefix frontend run build
  ```
- [ ] **Database Migrations**: Alembic head migration matches schema:
  ```bash
  $env:PYTHONPATH='backend'; backend\.venv\Scripts\alembic.exe current
  ```
- [ ] **Smoke Tests**: Smoke test suite passes with 100% green checks:
  ```bash
  backend\.venv\Scripts\python.exe scripts\smoke_test.py
  ```

---

## 2. Security & Environment Configuration

- [ ] **Secrets Generation**:
  - `POSTGRES_PASSWORD` is unique and high-entropy (`openssl rand -hex 24`).
  - `SECRET_KEY` is at least 32 characters long (`openssl rand -hex 32`).
  - `CREDENTIAL_ENCRYPTION_KEY` is a valid 32-byte URL-safe base64 Fernet key.
- [ ] **No Secrets in Frontend Artifacts**:
  - Only variables prefixed with `NEXT_PUBLIC_` exist in the frontend.
  - Zero database URLs, API secrets, or Fernet keys are bundled into frontend assets.
- [ ] **CORS Allowlists**:
  - `ALLOWED_ORIGINS` in `.env.production` contains only authorized production domains (no wildcard `*`).
- [ ] **OAuth 2.0 Credentials**:
  - Google Client ID & Secret configured in `.env.production`.
  - Authorized Redirect URI in Google Cloud Console matches `https://your-domain.com/api/v1/integrations/gmail/callback`.
- [ ] **Security Headers**:
  - HSTS enabled with 1-year duration (`max-age=31536000`).
  - CSP and nosniff headers active.

---

## 3. Infrastructure & Container Verification

- [ ] **Docker Compose Syntax**:
  ```bash
  docker compose config
  ```
- [ ] **Non-Root Execution**:
  - Backend runs as `appuser` (UID 1001).
  - Frontend runs as `nextjs` (UID 1001).
- [ ] **Port Isolation**:
  - PostgreSQL (`5432`) and Redis (`6379`) are NOT exposed to public interfaces.
- [ ] **Health Checks**:
  - `/health` responds with HTTP 200.
  - `/ready` responds with HTTP 200 confirming operational DB and cache connectivity.
- [ ] **Persistent Storage**:
  - Named Docker volumes (`postgres_data`, `redis_data`) configured with host persistence.
- [ ] **Celery Graceful Drain**:
  - Worker configured with `stop_grace_period: 60s`.

---

## 4. Post-Deployment Verification

- [ ] **Health Probe Check**:
  ```bash
  curl -f https://api.yourdomain.com/health
  curl -f https://api.yourdomain.com/ready
  ```
- [ ] **Public Landing Experience**: Landing page renders cleanly with responsive navigation.
- [ ] **Authentication Flow**: Login and registration verified with Argon2id session creation.
- [ ] **Visual Studio**: Infinite canvas opens with node library and parameter inspector.
- [ ] **Sample Execution**: One-click instantiate a production template and verify execution timeline.
- [ ] **Database Backup Generated**:
  ```bash
  python scripts/backup_database.py 14
  ```

---

## 5. Release Sign-Off

| Milestone | Gate | Status | Signed Off By |
| :--- | :--- | :--- | :--- |
| **Milestone 8** | Production Deployment & Release Engineering | **PASSED** | Antigravity Release Engine |
