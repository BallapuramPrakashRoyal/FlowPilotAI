# FlowPilot AI — Production Deployment Guide

This guide details the production deployment architecture, hosting provider comparisons, environment setup, database provisioning, and operational workflows for FlowPilot AI.

---

## 1. Cloud Provider Comparison & Cost Analysis

Deploying an autonomous automation platform requires 5 distinct services:
1. **Frontend**: Next.js 16 (Node.js runtime or standalone container).
2. **Backend**: FastAPI (Python ASGI server).
3. **Workers & Scheduler**: Celery Worker and Celery Beat (persistent long-running background processes).
4. **Database**: PostgreSQL 17 with `pgvector` extension.
5. **Cache/Broker**: Redis 7.

### Provider Comparison Matrix

| Provider | Supported Services | Free-Tier Limitations | Production Cost / Month | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Hetzner Cloud VPS** (CPX21 / CAX21) | All 5 services via Docker Compose | No permanent free tier (7-day trial) | **~$7.50 / mo** (€6.90/mo for 3 vCPU, 4GB RAM) | **Top Recommendation for Solo Dev** |
| **DigitalOcean Droplet** | All 5 services via Docker Compose | $200 60-day credit for new accounts | **$12 - $18 / mo** (Basic 2 vCPU, 2-4GB RAM) | Standard VPS with simple backups |
| **Railway** | Web + Worker + Redis + Postgres | $5 one-time credit, no permanent free tier | **$15 - $25 / mo** (Usage-based pricing) | Easiest Git-push managed containers |
| **Render** | Web (FastAPI/Next.js), Worker, Postgres, Redis | Free Web services **sleep after 15 min inactivity**. Celery workers **not supported on free tier**. | **$25 - $35 / mo** ($7/web + $7/worker + $7/postgres + $7/redis) | Traditional PaaS |
| **Fly.io** | Web, Celery Worker, Redis | Free tier requires credit card, limited shared CPU | **$10 - $20 / mo** | Edge container hosting |
| **Supabase** | Managed PostgreSQL + pgvector | Free tier **pauses after 7 days inactivity**. Limited to 500MB storage. | **$0 / mo** (Free tier for dev) or **$25/mo** (Pro) | Dedicated managed vector DB |
| **Neon** | Serverless Postgres + pgvector | Free tier auto-suspends on idle | **$0 / mo** (Free dev) or **$19/mo** | Serverless Postgres |
| **Upstash** | Serverless Redis Broker | 10,000 commands/day free limit | **$0 - $5 / mo** | Serverless Celery Broker |

> [!WARNING]
> **Free-Tier Trap Warning**: Do not attempt to run Celery Workers on serverless functions or sleeping free-tier web instances (such as Render Free Web Services or Vercel). Celery workers must remain continuously running in memory to listen on Redis queue events and resume durable multi-agent DAG executions.

---

## 2. Recommended Architectures for Solo Developers

### Architecture A: Single-VPS All-In-One (Highest Value — ~$7.50/mo)
- **Host**: Hetzner Cloud CPX21 (3 vCPU AMD, 4GB RAM, 80GB NVMe) or DigitalOcean $12 Droplet.
- **Reverse Proxy**: Caddy (automatic Let's Encrypt TLS 1.3 certificates).
- **Execution**: `docker compose -f docker-compose.prod.yml up -d`.
- **Advantages**: Internal network latency between Postgres, Redis, and Celery is `< 0.2ms`. Zero data transfer charges. Fixed, predictable monthly billing.

### Architecture B: Managed PaaS Hybrid (~$20/mo)
- **Frontend**: Vercel ($0 Free Hobby tier).
- **Backend & Celery**: Railway ($10 - $15/mo for web + persistent worker).
- **Database**: Supabase Free Tier or Neon ($0 - $10/mo with `pgvector`).
- **Redis**: Upstash Serverless Redis ($0 - $5/mo).
- **Advantages**: Zero server maintenance, automated git deployments.

---

## 3. Step-by-Step VPS Deployment (Docker Compose)

### Step 1: Provision Server & Install Docker
```bash
# Update server packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw fail2ban

# Configure Firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Install Docker Engine & Compose plugin
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Step 2: Clone Repository & Configure Environment
```bash
git clone https://github.com/FlowPilotAI/FlowPilotAI.git /opt/flowpilot
cd /opt/flowpilot

cp .env.production.example .env.production
chmod 600 .env.production
nano .env.production
```

Generate secure production secrets:
```bash
# Generate POSTGRES_PASSWORD
openssl rand -hex 24

# Generate SECRET_KEY
openssl rand -hex 32

# Generate Fernet CREDENTIAL_ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Step 3: Run Database Migrations & Launch Services
```bash
# Build and start all 6 production services in the background
docker compose --env-file .env.production up -d --build

# Verify all services are healthy
docker compose ps
```

### Step 4: Configure Caddy Reverse Proxy & SSL
Create `/etc/caddy/Caddyfile`:
```caddy
flowpilot.yourdomain.com {
    # Route API and WebSocket requests to FastAPI backend
    handle /api/* {
        reverse_proxy localhost:8000
    }
    handle /health {
        reverse_proxy localhost:8000
    }
    handle /ready {
        reverse_proxy localhost:8000
    }

    # Route all other traffic to Next.js frontend
    handle {
        reverse_proxy localhost:3000
    }

    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
}
```

Restart Caddy:
```bash
sudo systemctl reload caddy
```

---

## 4. Zero-Downtime Rolling Update Procedure

When releasing updates:
```bash
cd /opt/flowpilot

# 1. Pull latest code
git pull origin main

# 2. Run automated smoke tests and migration verification
python3 scripts/backup_database.py

# 3. Build updated images
docker compose --env-file .env.production build

# 4. Roll updated containers with zero downtime
docker compose --env-file .env.production up -d --no-deps backend frontend celery_worker

# 5. Run post-deployment smoke test
python3 scripts/smoke_test.py
```

---

## 5. Automated Backups & Disaster Recovery

Configure a daily cron job to back up the database:
```bash
sudo crontab -e
```
Add the daily backup task at 02:00 UTC:
```cron
0 2 * * * cd /opt/flowpilot && /opt/flowpilot/backend/.venv/bin/python scripts/backup_database.py 14 >> /var/log/flowpilot_backup.log 2>&1
```

To restore from a backup:
```bash
python3 scripts/restore_database.py /opt/flowpilot/backups/flowpilot_backup_pg_20261116_020000Z.sql.gz --force
```
