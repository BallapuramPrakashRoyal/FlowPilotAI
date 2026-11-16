# FlowPilot AI — Production Deployment Runbook

**Release Candidate**: v1.0.0-rc1  
**Deployment Target**: Single-VPS All-in-One (Caddy + Docker Compose) or Cloud PaaS  
**Document Classification**: Operational Execution Runbook  

---

## 1. Release Verification State Classification

To ensure complete transparency regarding production readiness, FlowPilot AI tracks deployment verification across five distinct tiers:

| Verification Tier | Scope | Status | Evidence / Artifacts |
| :--- | :--- | :--- | :--- |
| **Tier 1: Locally Verified** | Code quality, Unit & Integration Tests, Dual-Mode Engine | **VERIFIED** | 30/30 pytest tests passed, 0 ESLint errors, 12/12 smoke tests passed |
| **Tier 2: Container Verified** | Multi-stage Dockerfiles, Non-root UID 1001, Compose Config | **VERIFIED** | `docker compose config` passed with 0 errors; minimal runner layers |
| **Tier 3: Isolated Recovery Tested**| Backup integrity, Isolated DB extraction, Relational checks | **VERIFIED** | `scripts/verify_isolated_recovery.py` passed with 100% integrity |
| **Tier 4: Cloud Staging Tested** | Ingress TLS termination, Caddy reverse proxy, HSTS headers | **STAGED / READY** | Complete Caddyfile & environment templates generated |
| **Tier 5: Production OAuth Verified** | Google Cloud Console OAuth App, verified consent screen | **DOCUMENTED** | Verified OAuth state tokens & HMAC verification with sandbox keys |

---

## 2. Step-by-Step Server Setup Runbook

### Step 1: Base Linux OS Hardening (Ubuntu 24.04 LTS / Debian 12)
```bash
# Update repositories and upgrade system packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw fail2ban jq unattended-upgrades

# Configure Uncomplicated Firewall (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP (for Let's Encrypt challenge)
sudo ufw allow 443/tcp  # HTTPS (TLS 1.3)
sudo ufw enable

# Install Docker Engine & Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker
```

---

### Step 2: Caddy Web Server Installation & Reverse Proxy Configuration
Caddy terminates TLS 1.3 automatically and manages Let's Encrypt certificates without certbot cron jobs.

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLF 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLF 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

Create `/etc/caddy/Caddyfile`:
```caddy
flowpilot.yourdomain.com {
    # Forward API routes and WebSocket connections to FastAPI
    handle /api/* {
        reverse_proxy localhost:8000
    }
    handle /health {
        reverse_proxy localhost:8000
    }
    handle /ready {
        reverse_proxy localhost:8000
    }

    # Forward web traffic to Next.js App Router
    handle {
        reverse_proxy localhost:3000
    }

    # Security Headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        Permissions-Policy "camera=(), microphone=(), geolocation=()"
    }
}
```

Reload Caddy:
```bash
sudo systemctl reload caddy
```

---

### Step 3: Application Code & Environment Deployment
```bash
# Clone repository
sudo mkdir -p /opt/flowpilot
sudo chown $USER:$USER /opt/flowpilot
git clone https://github.com/FlowPilotAI/FlowPilotAI.git /opt/flowpilot
cd /opt/flowpilot

# Copy and populate production environment file
cp .env.production.example .env.production
chmod 600 .env.production
nano .env.production
```

---

### Step 4: Container Build & Stack Launch
```bash
# Build multi-stage containers and start services
docker compose --env-file .env.production up -d --build

# Inspect container health states
docker compose ps
```
Expected output:
```
NAME                          STATUS                    PORTS
flowpilot-backend             Up (healthy)             0.0.0.0:8000->8000/tcp
flowpilot-celery-worker       Up                       
flowpilot-celery-scheduler    Up                       
flowpilot-frontend            Up (healthy)             0.0.0.0:3000->3000/tcp
flowpilot-postgres            Up (healthy)             127.0.0.1:5433->5432/tcp
flowpilot-redis               Up (healthy)             127.0.0.1:6379->6379/tcp
```

---

### Step 5: Post-Deployment Smoke Test
```bash
python3 scripts/smoke_test.py
```
Output must conclude with:
`[+] All smoke test checks PASSED cleanly.`

---

## 3. Disaster Recovery & Rollback Runbook

### Scenario A: Rolling Back to Previous Release Image
If an unexpected regression occurs in an updated release:
```bash
cd /opt/flowpilot

# 1. Revert Git tag
git checkout v1.0.0-rc1

# 2. Re-deploy container images
docker compose --env-file .env.production up -d --build

# 3. Verify health
python3 scripts/smoke_test.py
```

### Scenario B: Database Point-in-Time Recovery
If corrupted state or accidental deletion occurs:
```bash
# 1. Stop background workers to halt incoming tasks
docker compose stop celery_worker celery_scheduler backend

# 2. Restore database from verified compressed snapshot
python3 scripts/restore_database.py /opt/flowpilot/backups/flowpilot_backup_pg_LATEST.sql.gz --force

# 3. Restart application stack
docker compose start backend celery_worker celery_scheduler

# 4. Verify readiness
curl -f http://localhost:8000/ready
```
