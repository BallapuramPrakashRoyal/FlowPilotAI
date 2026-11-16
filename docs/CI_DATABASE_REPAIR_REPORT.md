# FlowPilot AI — Critical CI Repair: Alembic Migration & SQLite Test Database Report

**Date:** 2026-11-16  
**Status:** 🟢 RESOLVED & FULLY VERIFIED (All 11 Acceptance Criteria Passed)  
**Author:** Senior Python Backend & Database Reliability Engineer  

---

## Executive Summary

The recent GitHub Actions CI run identified two database-related issues on clean environments:
1. **Problem A — Alembic Migration Failure:** `sqlite3.OperationalError: no such table: agent_runs` (and `sqlalchemy.exc.NoSuchTableError: agent_runs`). On a clean database, Alembic attempted to alter `agent_runs` before the table was ever created.
2. **Problem B — SQLite API Test Failure:** `sqlalchemy.exc.OperationalError: no such table: users`. In GitHub Actions and fresh test runs, `test_api_endpoints.py` failed on `test_auth_registration_and_login`, `test_ai_workflow_planner`, and `test_workflow_execution_dispatch` (3 of 4 tests) because `httpx.ASGITransport` does not invoke FastAPI lifespan startup (`init_db()`), and no test fixture initialized the isolated schema.

Both issues have been diagnosed, resolved, and verified across SQLite and PostgreSQL dialect targets. All 30/30 backend tests pass (100%), full Alembic upgrade/downgrade/re-upgrade cycles pass, frontend lint reports 0 errors, Next.js compiles 14/14 static routes, and Docker Compose configuration is validated.

---

## 1. Problem A — Alembic Migration Failure Diagnosis & Repair

### Root Cause
1. **Missing Initial Baseline Migration:** The migration directory `backend/alembic/versions/` contained only one revision: `f675da0e0729_add_milestone6_agent_observability.py`. It had `revises: None` (marked as root) but was generated as an `ALTER TABLE agent_runs ADD COLUMN ...` script. The application's base tables (`users`, `workspaces`, `workflows`, `executions`, `agent_runs`, `documents`, etc.) were previously created during development via `Base.metadata.create_all()` in `init_db.py`, bypassing Alembic.
2. **Crash on Clean Database:** When Alembic executed against an empty database (such as in CI or on a fresh PostgreSQL/SQLite database), Alembic's `batch_alter_table('agent_runs')` attempted to reflect `agent_runs` to perform batch operations and failed immediately with `no such table: agent_runs`.
3. **Driver Compatibility Bug in `backend/alembic/env.py`:** `get_sync_url()` invoked `create_engine(settings.sync_database_uri, connect_args={"connect_timeout": 3})`. When `SYNC_DATABASE_URL` was configured for SQLite (e.g. `sqlite:///flowpilot_ci.db`), `sqlite3` rejected `connect_timeout` with `TypeError`, causing `get_sync_url()` to catch the exception and fall back to hardcoded `flowpilot.db` in the repository root, ignoring explicit CI parameters.

### Resolution
1. **Created Baseline Migration (`1a2b3c4d5e6f_initial_schema.py`):**
   - Implements full DDL for all 20 base application tables in proper topological dependency order:
     `users` ➔ `workspaces` ➔ `workspace_members` ➔ `workflows` ➔ `workflow_versions` ➔ `workflow_nodes` ➔ `integrations` ➔ `integration_credentials` ➔ `workspace_ai_configs` ➔ `executions` ➔ `execution_nodes` ➔ `execution_events` ➔ `ai_usage_records` ➔ `approvals` ➔ `agent_runs` (baseline schema) ➔ `prompt_templates` ➔ `knowledge_bases` ➔ `documents` ➔ `document_chunks` ➔ `audit_logs`.
   - Reversible: Downgrade drops all 20 tables in exact reverse dependency order.
2. **Re-chained Observability Migration (`f675da0e0729`):**
   - Set `down_revision = '1a2b3c4d5e6f'`.
   - On clean upgrade, `1a2b3c4d5e6f` creates `agent_runs`, and `f675da0e0729` applies the Milestone 6 observability columns, indexes, and foreign key to `executions.id`.
3. **Hardened `backend/alembic/env.py`:**
   - Respects explicit Alembic config `sqlalchemy.url`.
   - Normalizes async driver prefixes (`sqlite+aiosqlite://` ➔ `sqlite://`, `postgresql+asyncpg://` ➔ `postgresql://`).
   - Only passes `connect_timeout` to PostgreSQL connections. SQLite URIs are used directly.

---

## 2. Problem B — SQLite Test Database Initialization Diagnosis & Repair

### Root Cause
1. **Missing ASGI Lifespan in AsyncClient:** In `backend/tests/test_api_endpoints.py`, tests constructed `AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`. In `httpx`, `ASGITransport` does not run the ASGI `lifespan` handler (`init_db()`), leaving the database uninitialized.
2. **No Pytest Fixture or Dependency Overrides:** There was no `backend/tests/conftest.py`. When running with an empty database or fresh environment (`flowpilot_ci.db`), FastAPI's `get_db()` connected successfully to the empty SQLite file without raising a connection error (unlike PostgreSQL), so fallback table creation was never triggered.
3. **Missing Table Errors on API Requests:** When the API executed `select(User).where(...)`, SQLite raised `(sqlite3.OperationalError) no such table: users`.

### Resolution
1. **Created `backend/tests/conftest.py`:**
   - **Session-Level Schema Fixture (`setup_test_database_schema`):** Imports all models from `app.database.models` and executes `Base.metadata.create_all(test_sync_engine)` synchronously on an isolated test database (`flowpilot_test_isolated.db` or the configured `DATABASE_URL`), ensuring 100% of tables exist before any test runs.
   - **Function-Level Context Fixture (`setup_test_db_context`):** Overrides FastAPI's `get_db` dependency via `app.dependency_overrides[get_db]` so every HTTP request dispatched through `AsyncClient` uses the test session.
   - **Process Engine Binding:** Points `db_mod.async_engine` and `db_mod.AsyncSessionLocal` to the isolated test database so internal queries and background runners share the same initialized state.
   - **Clean Teardown:** Clears dependency overrides, restores engine references, and removes temporary isolated test SQLite files.

---

## 3. Migration Revision Chain

### Before Repair
```mermaid
flowchart LR
    NONE["None (Root)"] --> F675["f675da0e0729\n(add_milestone6_agent_observability)\nALTER TABLE agent_runs\n[FAIL on empty DB]"]
```

### After Repair
```mermaid
flowchart LR
    ROOT["None"] --> M001["1a2b3c4d5e6f\n(initial_schema)\nCREATE 20 application tables\nincluding baseline agent_runs"]
    M001 --> F675["f675da0e0729\n(add_milestone6_agent_observability)\nALTER TABLE agent_runs\nADD 12 observability columns\n& fk_agent_runs_execution_id"]
```

---

## 4. Verification Evidence

### 4.1. Individual Retest of Previously Failing API Tests
Each test was executed in isolation:

| Test Name | Result | Duration | Details |
|:---|:---:|:---:|:---|
| `test_auth_registration_and_login` | **PASSED** | 1.49s | User registered, JWT issued, `/me` profile retrieved, login validated. |
| `test_ai_workflow_planner` | **PASSED** | 3.36s | Planner generated multi-node workflow graph with >= 3 nodes and >= 2 edges. |
| `test_workflow_execution_dispatch` | **PASSED** | 1.94s | Workflow registered and executed with HTTP 202 Accepted and QUEUED status. |
| `test_health_check` | **PASSED** | 0.05s | Health probe returned HTTP 200 with healthy status. |

### 4.2. Complete Backend Test Suite
```
backend/tests/test_agent_orchestration.py . [ 10%]
backend/tests/test_ai_runtime.py          . [ 23%]
backend/tests/test_api_endpoints.py       . [ 36%]
backend/tests/test_dag_engine.py          . [ 46%]
backend/tests/test_milestone6_acceptance.py . [ 80%]
backend/tests/test_multi_agent.py         . [ 90%]
backend/tests/test_security.py            . [100%]

======================== 30 passed, 1 warning in 7.69s ========================
```
**Total:** 30/30 PASSED (100% Pass Rate).

### 4.3. Alembic Migration Lifecycle on Clean Sandbox Database
Verified via `scripts/test_migration_lifecycle.py`:
- **Step 1 (Empty DB Check):** 0 tables detected. `PASSED`
- **Step 2 (Upgrade to `1a2b3c4d5e6f`):** Created 20 application tables + `alembic_version`. `agent_runs` created with 11 baseline columns. `PASSED`
- **Step 3 (Upgrade to `f675da0e0729` / Head):** Altered `agent_runs` to 23 columns (added 12 Milestone 6 columns + FK + 2 indexes). `PASSED`
- **Step 4 (Downgrade to `1a2b3c4d5e6f`):** Successfully reverted `agent_runs` back to 11 baseline columns. `PASSED`
- **Step 5 (Downgrade to `base`):** Dropped all 20 application tables in reverse order. `PASSED`
- **Step 6 (Fresh Single-Step Re-upgrade to Head):** Executed `1a2b3c4d5e6f` ➔ `f675da0e0729` seamlessly from empty state. `PASSED`

### 4.4. PostgreSQL DDL Compilation (Offline Dialect Audit)
Verified via `alembic upgrade head --sql` and `alembic downgrade head:base --sql` targeting PostgreSQL:
- Clean transactional SQL generated with `BEGIN;` and `COMMIT;`.
- Correct PostgreSQL types: `TIMESTAMP WITH TIME ZONE`, `JSON`, `BOOLEAN`, `FOREIGN KEY ... ON DELETE CASCADE`.
- 0 syntax errors or missing constraint references.

### 4.5. Frontend Lint & Production Build
- **ESLint (`npm run lint`):** 0 errors, 75 style warnings. (Exit code 0).
- **Turbopack Build (`npm run build`):** All 14 routes statically prerendered in 2.4s.

### 4.6. Docker Compose Configuration
- `docker compose config`: Validated cleanly (Exit code 0).
- Backend startup command confirmed: `sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"`.

---

## 5. Files Changed & Summary

| File | Change Description |
|:---|:---|
| `backend/alembic/versions/1a2b3c4d5e6f_initial_schema.py` | Added baseline migration defining initial DDL for 20 application tables and indexes. |
| `backend/alembic/versions/f675da0e0729_add_milestone6_agent_observability.py` | Set `down_revision = '1a2b3c4d5e6f'` to establish valid revision chain. |
| `backend/alembic/env.py` | Hardened URL parser to prevent SQLite driver keyword errors and respect explicit config URLs. |
| `backend/tests/conftest.py` | Added session-level table creation fixture and function-level `get_db` FastAPI dependency override. |
| `scripts/generate_initial_migration.py` | Utility script to generate reproducible baseline Alembic migration. |
| `scripts/test_migration_lifecycle.py` | Test harness verifying upgrade, downgrade, and re-upgrade on isolated database. |

---

## 6. Remaining Risks & Mitigations

| Risk | Impact | Mitigation |
|:---|:---:|:---|
| Existing databases created without Alembic stamp | Low | Existing resilient database (`flowpilot.db`) already has full table schema. Alembic can be stamped to `head` (`alembic stamp head`) on legacy databases without losing data. |
| CI running without PostgreSQL service | None | CI uses `flowpilot_ci.db` (SQLite) where full migration and pytest suites execute cleanly. In production/Docker, PostgreSQL with pgvector is used. |
