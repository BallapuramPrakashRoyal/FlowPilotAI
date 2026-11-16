# FlowPilot AI — Operations, Monitoring & Runbook Manual

**Document Classification**: Systems Operations Manual  
**Applies To**: FlowPilot AI Distributed Runtime (FastAPI, Celery, Redis, PostgreSQL pgvector, Next.js)  

---

## 1. Application & Worker Logging

FlowPilot AI outputs structured log streams across all services to `stdout` / `stderr`, compatible with Docker logging drivers, systemd, Datadog, Grafana Loki, and CloudWatch.

### Log Viewing Commands
```bash
# View aggregated real-time logs across all services
docker compose logs -f

# Follow FastAPI backend logs
docker compose logs -f --tail=100 backend

# Follow Celery worker task execution & state transitions
docker compose logs -f --tail=100 celery_worker

# Follow Celery Beat scheduler triggers
docker compose logs -f --tail=50 celery_scheduler

# Inspect PostgreSQL query and vector index logs
docker compose logs -f --tail=50 postgres
```

### Key Log Signatures to Monitor
- `[INFO] Initializing FlowPilot AI Backend Services...`: Service startup and DB check.
- `[WARNING] PostgreSQL connection refused... Engaging SQLite fallback`: Indicates database connection drop.
- `[INFO] Executing step ...`: Celery DAG task progression.
- `[ERROR] Node execution failed`: Workflow node runtime exception.

---

## 2. Worker Queue & State Management

### Inspecting Worker Status
```bash
# Check registered Celery workers
docker compose exec backend celery -A app.workers.celery_app inspect ping

# Inspect currently executing tasks
docker compose exec backend celery -A app.workers.celery_app inspect active

# Inspect scheduled cron jobs in Celery beat
docker compose exec backend celery -A app.workers.celery_app inspect scheduled

# Check Redis queue length (default celery queue)
docker compose exec redis redis-cli llen celery
```

### Purging Stalled or Poison Queues
> [!CAUTION]
> Purging queues deletes pending unstarted tasks. Active tasks will complete, but queued runs will be cancelled.

```bash
docker compose exec backend celery -A app.workers.celery_app purge -f
```

---

## 3. Database Maintenance & Index Health

### Vacuuming & Vector Index Optimization
pgvector indexes (`HNSW` / `IVFFlat`) benefit from routine vacuuming:
```bash
docker compose exec postgres psql -U flowpilot -d flowpilot_db -c "VACUUM ANALYZE document_chunks;"
```

### Inspecting Active Connections
```bash
docker compose exec postgres psql -U flowpilot -d flowpilot_db -c "
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
"
```

### Inspecting Table Sizes
```bash
docker compose exec postgres psql -U flowpilot -d flowpilot_db -c "
SELECT relname AS table_name, pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;
"
```

---

## 4. Health Check Probes & External Monitoring

Integrate external uptime monitoring tools (e.g., Uptime Kuma, Better Stack, Pingdom) with FlowPilot AI's dual-tier probes:

| Probe Type | URL | Expected Code | Purpose | Notification Threshold |
| :--- | :--- | :--- | :--- | :--- |
| **Liveness Probe** | `https://your-domain.com/health` | `200 OK` | Verifies FastAPI process responsiveness | Alert after 3 consecutive failures |
| **Readiness Probe**| `https://your-domain.com/ready` | `200 OK` | Verifies PostgreSQL and Redis health | Alert immediately on 503 response |
| **Frontend Health** | `https://your-domain.com/` | `200 OK` | Verifies Next.js SSR / Static serving | Alert after 2 consecutive failures |

---

## 5. Automated Backup Verification Runbook

### Running a Manual Timestamped Backup
```bash
python scripts/backup_database.py 7
```
Output:
```
[*] Backing up PostgreSQL database: flowpilot_db on localhost...
[+] Backup successfully generated: backups/flowpilot_backup_pg_20261116_113000Z.sql.gz
    Size: 84.12 KB | SHA256: 7f8a192...
```

### Verifying Backup Integrity
Each backup generates a companion `.meta.json` file. Check that:
1. File size is `> 0`.
2. SHA256 matches:
   ```bash
   python -c "import hashlib; print(hashlib.sha256(open('backups/flowpilot_backup_pg_TIMESTAMP.sql.gz', 'rb').read()).hexdigest())"
   ```

---

## 6. Incident Response & Troubleshooting Runbooks

### Incident A: Celery Worker Fails or Hangs
- **Symptoms**: Workflows stuck in `RUNNING` or `QUEUED` without progressing.
- **Diagnostic Step**:
  ```bash
  docker compose logs --tail=100 celery_worker
  ```
- **Remediation**:
  1. Restart the Celery worker container:
     ```bash
     docker compose restart celery_worker
     ```
  2. The workflow state machine will detect interrupted tasks upon restart and safely resume from the last uncommitted node.

### Incident B: High Database Connection Pool Usage
- **Symptoms**: `/ready` endpoint returns 503; logs show `TimeoutError: QueuePool limit of size 15 overflow 10 reached`.
- **Diagnostic Step**: Check connection counts via `pg_stat_activity`.
- **Remediation**:
  1. Increase `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` in `.env.production`.
  2. Verify that long-running queries have explicit timeouts (`NODE_EXECUTION_TIMEOUT_SECONDS=300`).
  3. Restart the backend service: `docker compose restart backend`.

### Incident C: OAuth Refresh Token Revocation
- **Symptoms**: Gmail operations fail with `401 Unauthorized` or status `Token Expired`.
- **Remediation**:
  1. The user must navigate to **Integration Hub** (`/integrations`).
  2. Click **Reconnect Gmail** to complete a clean OAuth 2.0 consent flow.
  3. The backend rotates and re-encrypts the fresh refresh token via Fernet AES-256.
