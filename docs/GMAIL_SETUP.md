# FlowPilot AI — Gmail OAuth 2.0 Setup & Integration Guide

## 📌 Overview

FlowPilot AI integrates with Google Gmail via official OAuth 2.0 protocols to enable autonomous email triaging, metadata extraction, draft generation, and human-in-the-loop approved email dispatch.

All tokens are symmetrically encrypted at rest using AES-256 (Fernet) and are never exposed to frontend clients. Direct email transmission strictly requires human authorization in the Approval Center.

---

## 🛠️ Step 1: Google Cloud Project Setup

1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `FlowPilot-Automation`).
3. Enable the **Gmail API**:
   - Go to **APIs & Services > Library**.
   - Search for **Gmail API** and click **Enable**.

---

## 🔑 Step 2: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**.
2. Select User Type:
   - **Internal**: If deploying within a Google Workspace organization.
   - **External**: For general accounts (requires adding test users during development).
3. Fill in mandatory application information:
   - **App name**: `FlowPilot AI`
   - **User support email**: Your support or admin email.
   - **Developer contact information**: Your contact email.
4. Configure Scopes:
   Click **Add or Remove Scopes** and select the minimum necessary scopes:
   - `https://www.googleapis.com/auth/gmail.readonly` — Read emails and thread metadata.
   - `https://www.googleapis.com/auth/gmail.compose` — Create draft replies.
   - `https://www.googleapis.com/auth/gmail.send` — Dispatch authorized emails after human approval.
   - `https://www.googleapis.com/auth/userinfo.email` — Identify authenticated workspace email address.
5. In **Test Users**, add the Google email accounts you will use for testing.

---

## 🔐 Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**.
2. Click **Create Credentials > OAuth client ID**.
3. Select Application type: **Web application**.
4. Set **Authorized redirect URIs**:
   - Development: `http://localhost:8000/api/v1/integrations/gmail/callback`
   - Production: `https://<YOUR_API_DOMAIN>/api/v1/integrations/gmail/callback`
5. Save and copy your **Client ID** and **Client Secret**.

---

## ⚙️ Step 4: Configure FlowPilot Environment Variables

Update your `.env` or `backend/.env` file with your credentials:

```bash
# Google OAuth 2.0 Settings
GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-client-secret"
GOOGLE_REDIRECT_URI="http://localhost:8000/api/v1/integrations/gmail/callback"

# Symmetric Credential Encryption Key (Base64-encoded 32-byte key)
CREDENTIAL_ENCRYPTION_KEY="your-fernet-encryption-key"
```

> [!IMPORTANT]
> If `GOOGLE_CLIENT_ID` or `GOOGLE_CLIENT_SECRET` are not set, FlowPilot AI displays a **Real Connection Required** state and prevents unauthorized or simulated Gmail interactions.

---

## 🚀 Step 5: Authorize in the Integration Hub

1. Navigate to `/integrations` in the FlowPilot AI web application.
2. Under the **Google Gmail** card, click **Connect with Google OAuth**.
3. Sign in to your Google Account and grant the requested permissions.
4. You will be redirected back to FlowPilot AI with a confirmed **Connected (OAuth Active)** status.

---

## 🛡️ Security Guarantees & Best Practices

- **Zero Client Token Exposure**: Raw access and refresh tokens are decrypted server-side only when executing authorized operations. API responses return only connection status and account email.
- **Automatic Token Refresh**: Expired tokens are refreshed dynamically in background tasks without user interruption.
- **Revocation on Disconnect**: Disconnecting from the Integration Hub issues an immediate revocation request to Google's OAuth servers and removes stored database credentials.
- **Mandatory Approval Gate**: AI agents can list, read, and draft emails autonomously, but cannot call `gmail.send_email` without an `APPROVED` record from a workspace operator.
