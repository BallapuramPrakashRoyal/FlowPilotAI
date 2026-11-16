# FlowPilot AI — Integration Hub Architecture & Management

## 📊 Overview

The **Integration Hub** (`/integrations`) is FlowPilot AI's central control plane for managing third-party platform connections, OAuth authorizations, token lifecycles, and security scopes.

FlowPilot AI operates with strict workspace isolation: each workspace manages its own external platform credentials, encrypted at rest and isolated from other tenants.

---

## 🔌 Supported & Planned Integrations

| Provider | Status | Capabilities | Auth Protocol | Security Requirements |
| :--- | :--- | :--- | :--- | :--- |
| **Google Gmail** | **Available (Live)** | List unread, read metadata & full body, search, create drafts, approval-gated send | OAuth 2.0 (offline access) | Fernet AES-256 token encryption, state validation, human approval for sending |
| **GitHub** | **Planned (Milestone 7)** | Webhook ingestion, issue triage, pull request summaries | GitHub OAuth / App | Read-only repository access by default |
| **Slack** | **Planned (Milestone 7)** | Channel alerts, interactive approval decision cards | Slack OAuth 2.0 | Scoped bot permissions |

---

## 🔒 Security Architecture

### 1. Cryptographic OAuth State Validation
Before redirecting users to Google's consent screen, FlowPilot AI issues a cryptographically signed, short-lived JWT state token:
- Claims: `purpose="gmail_oauth"`, `workspace_id`, `exp=now + 10m`
- Validated upon callback to prevent CSRF and session fixation attacks.
- Expired or forged states immediately return HTTP 400.

### 2. Encryption at Rest
Integration credentials (`IntegrationCredential`) are symmetrically encrypted before persistence:
- Cipher: Fernet AES-128 in CBC mode with HMAC-SHA256 authentication.
- Access tokens and refresh tokens are decrypted in-memory only during authorized execution.
- Tokens are excluded from all serialization schemas and never transmitted to the frontend.

### 3. Automatic Token Refresh
- Access tokens include an expiry timestamp (`token_expiry`).
- When a task requires Gmail access, the backend checks if the token is within 2 minutes of expiration.
- If expired, `_get_valid_access_token` automatically requests a new access token from Google's token endpoint using the stored refresh token and updates the database.

### 4. Credential Revocation & Disconnection
When an integration is disconnected:
1. An asynchronous HTTP call is issued to `https://oauth2.googleapis.com/revoke?token={token}` to revoke Google tokens.
2. The `IntegrationCredential` row is deleted from the database.
3. The `Integration` record is marked `is_connected=False`, `account_email=None`, `status_message="Disconnected"`.
4. An immutable `AuditLog` entry is written with timestamp and actor details.

---

## 📋 Authorized Gmail Agent Tools

Agents operate under strict role-based permission boundaries and cannot invoke unregistered or unauthorized capabilities.

| Tool Name | Input Schema | Permissions Required | Approval Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| `gmail.list_unread` | `{ max_results: int }` | `gmail:read` | No | Fetches unread email list from authorized inbox. |
| `gmail.get_message` | `{ message_id: str }` | `gmail:read` | No | Retrieves sender, subject, labels, and snippet. |
| `gmail.search` | `{ query: str, max_results: int }` | `gmail:read` | No | Searches emails via Gmail search query syntax. |
| `gmail.get_content` | `{ message_id: str }` | `gmail:read` | No | Decodes full MIME text parts and headers. |
| `gmail.create_draft` | `{ recipient, subject, body, thread_id }` | `gmail:draft` | No | Prepares an email draft in the mailbox. |
| `gmail.send_email` | `{ recipient, subject, body, thread_id }` | `gmail:send` | **Yes (Enforced)** | Dispatches email. Blocked without operator approval. |
