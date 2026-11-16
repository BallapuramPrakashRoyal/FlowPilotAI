# FlowPilot AI — Production Environment Checklist

**Release Candidate**: v1.0.0-rc1  
**Target Environment**: Production Deployment Gate  
**Security Classification**: Critical Operator Configuration  

---

## 1. Environment Variable Verification Matrix

Every variable listed below must be set prior to launching production containers. Never commit production values to version control.

| Environment Variable | Required | Sensitive | Verification Method | Safe Example / Format |
| :--- | :--- | :--- | :--- | :--- |
| **`ENVIRONMENT`** | **YES** | No | Check that value is `"production"` | `production` |
| **`DATABASE_URL`** | **YES** | **YES** | Verify connection via `pg_isready` | `postgresql+asyncpg://user:pass@host:5432/flowpilot_db` |
| **`SYNC_DATABASE_URL`** | **YES** | **YES** | Alembic migration engine connectivity | `postgresql://user:pass@host:5432/flowpilot_db` |
| **`REDIS_URL`** | **YES** | **YES** | Verify `redis-cli ping` returns PONG | `redis://:authpass@host:6379/0` |
| **`SECRET_KEY`** | **YES** | **CRITICAL** | Minimum 32-byte high-entropy string | Generated via `openssl rand -hex 32` |
| **`CREDENTIAL_ENCRYPTION_KEY`** | **YES** | **CRITICAL** | 32-byte URL-safe base64 Fernet key | Generated via `Fernet.generate_key()` |
| **`ALLOWED_ORIGINS`** | **YES** | No | Must NOT be wildcard `*` | `https://yourdomain.com,https://app.yourdomain.com` |
| **`GOOGLE_CLIENT_ID`** | Optional | No | Google Cloud Console OAuth 2.0 Web ID | `xxxxx.apps.googleusercontent.com` |
| **`GOOGLE_CLIENT_SECRET`** | Optional | **CRITICAL** | Google Cloud Console OAuth Client Secret | Minimum 24 chars |
| **`GOOGLE_REDIRECT_URI`** | Optional | No | Must match Google Cloud Console URI | `https://api.yourdomain.com/api/v1/integrations/gmail/callback` |
| **`GEMINI_API_KEY`** | Optional | **CRITICAL** | Google AI Studio API token | `AIzaSy...` (39 chars) |
| **`OPENAI_API_KEY`** | Optional | **CRITICAL** | OpenAI Platform secret key | `sk-proj-...` |
| **`DEFAULT_AI_PROVIDER`** | **YES** | No | Active provider selection | `"gemini"` or `"openai"` or `"mock"` |
| **`DB_POOL_SIZE`** | **YES** | No | PostgreSQL persistent connection pool | `15` |
| **`DB_MAX_OVERFLOW`** | **YES** | No | Burst connection headroom | `10` |
| **`DB_POOL_RECYCLE`** | **YES** | No | Connection recycling timeout | `1800` (30 minutes) |
| **`RATE_LIMIT_PER_MINUTE`** | **YES** | No | Rate limit threshold per IP | `120` |
| **`NEXT_PUBLIC_API_URL`** | **YES** | No | Public backend API domain | `https://api.yourdomain.com` |

---

## 2. Secrets Generation Procedures

Run these commands in a secure terminal to generate production cryptographic secrets:

```bash
# 1. Generate JWT SECRET_KEY (256-bit entropy)
openssl rand -hex 32

# 2. Generate Fernet CREDENTIAL_ENCRYPTION_KEY (AES-256 Symmetric Key)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 3. Generate PostgreSQL Admin Password
openssl rand -hex 24

# 4. Generate Redis Authentication Password
openssl rand -hex 24
```

---

## 3. Production Readiness Verifications

- [ ] **No Default Dev Keys**: Ensure `SECRET_KEY` does NOT equal `dev_insecure_jwt_secret_key_minimum_32_characters` and `CREDENTIAL_ENCRYPTION_KEY` does NOT equal the development key.
- [ ] **Strict CORS Restrictions**: Ensure `ALLOWED_ORIGINS` does not contain `*` and points exclusively to your production frontend domains.
- [ ] **OAuth Callback Registration**: The exact URL configured in `GOOGLE_REDIRECT_URI` is whitelisted in Google Cloud Console $\rightarrow$ Credentials $\rightarrow$ Authorized redirect URIs.
- [ ] **Frontend Environment Boundary**: Verify that `grep -rn "CREDENTIAL_ENCRYPTION_KEY" frontend/src` returns zero matches in client runtime code.
- [ ] **Database Connection Pooling**: `DB_POOL_SIZE` set between 10 and 25 depending on VPS RAM.
- [ ] **Health Probes Active**: Test that both `curl -f https://api.yourdomain.com/health` and `curl -f https://api.yourdomain.com/ready` return HTTP 200.
