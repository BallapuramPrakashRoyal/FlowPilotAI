"""Gmail Integration Service supporting Google OAuth 2.0, token refresh, and authorized Gmail operations."""

import base64
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
]


class GmailService:
    """Service for interacting securely with Google Gmail API."""

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token

    @classmethod
    def get_auth_url(cls, state: str) -> str:
        """Construct Google OAuth 2.0 authorization redirect URL with minimum necessary scopes."""
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise RuntimeError(
                "Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment."
            )

        base = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(GMAIL_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        from urllib.parse import urlencode
        return f"{base}?{urlencode(params)}"

    @classmethod
    async def exchange_code(cls, code: str) -> Dict[str, Any]:
        """Exchange authorization code for OAuth access and refresh tokens."""
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise RuntimeError("Google OAuth credentials are not configured in settings")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            resp.raise_for_status()
            data = resp.json()

            # Retrieve user email if userinfo scope was granted
            email = None
            if "access_token" in data:
                try:
                    user_resp = await client.get(
                        "https://www.googleapis.com/oauth2/v2/userinfo",
                        headers={"Authorization": f"Bearer {data['access_token']}"},
                    )
                    if user_resp.status_code == 200:
                        email = user_resp.json().get("email")
                except Exception as exc:
                    logger.warning(f"Could not fetch userinfo email: {exc}")

            data["email"] = email
            return data

    @classmethod
    async def refresh_access_token(cls, refresh_token: str) -> Dict[str, Any]:
        """Use refresh token to obtain a new access token from Google OAuth."""
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise RuntimeError("Google OAuth credentials are not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "refresh_token": refresh_token,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                },
            )
            resp.raise_for_status()
            return resp.json()

    @classmethod
    async def revoke_token(cls, token: str) -> bool:
        """Revoke an access or refresh token with Google OAuth server."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"https://oauth2.googleapis.com/revoke?token={token}",
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                return resp.status_code == 200
        except Exception as exc:
            logger.warning(f"Error revoking Google token: {exc}")
            return False

    def _ensure_connected(self):
        if not self.access_token:
            raise RuntimeError("Gmail connection required: no access token provided. Please connect Gmail in the Integration Hub.")

    async def fetch_unread_messages(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """Fetch unread emails from the user's Gmail inbox."""
        self._ensure_connected()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                list_res = await client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread&maxResults={max_results}",
                    headers=headers,
                )
                list_res.raise_for_status()
                messages_meta = list_res.json().get("messages", [])

                results = []
                for meta in messages_meta:
                    msg = await self.get_message_details(meta["id"])
                    results.append(msg)
                return results
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Gmail token expired; please reconnect or refresh your Gmail connection.") from e
            raise RuntimeError(f"Gmail API error: {e.response.text}") from e
        except Exception as e:
            raise RuntimeError(f"Gmail request failed: {e}") from e

    async def get_message_details(self, message_id: str) -> Dict[str, Any]:
        """Retrieve metadata, sender, subject, and snippet for a specific message."""
        self._ensure_connected()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                msg_res = await client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}",
                    headers=headers,
                )
                msg_res.raise_for_status()
                data = msg_res.json()
                headers_list = data.get("payload", {}).get("headers", [])
                subject = next((h["value"] for h in headers_list if h["name"].lower() == "subject"), "No Subject")
                sender = next((h["value"] for h in headers_list if h["name"].lower() == "from"), "Unknown")
                snippet = data.get("snippet", "")

                return {
                    "id": data.get("id", message_id),
                    "thread_id": data.get("threadId"),
                    "sender": sender,
                    "subject": subject,
                    "snippet": snippet,
                    "body": snippet,
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    "labels": data.get("labelIds", []),
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Gmail token expired; please reconnect or refresh your Gmail connection.") from e
            raise RuntimeError(f"Gmail message detail retrieval failed: {e.response.text}") from e

    async def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search emails using standard Gmail search queries."""
        self._ensure_connected()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        from urllib.parse import quote_plus
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q={quote_plus(query)}&maxResults={max_results}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(url, headers=headers)
            res.raise_for_status()
            messages_meta = res.json().get("messages", [])

            results = []
            for meta in messages_meta[:max_results]:
                msg = await self.get_message_details(meta["id"])
                results.append(msg)
            return results

    async def get_message_content(self, message_id: str) -> Dict[str, Any]:
        """Retrieve full decoded body and headers for a message."""
        self._ensure_connected()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}?format=full",
                headers=headers,
            )
            res.raise_for_status()
            data = res.json()
            payload = data.get("payload", {})
            headers_list = payload.get("headers", [])

            body_text = ""
            if "body" in payload and payload["body"].get("data"):
                body_bytes = base64.urlsafe_b64decode(payload["body"]["data"])
                body_text = body_bytes.decode("utf-8", errors="replace")
            elif "parts" in payload:
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        body_bytes = base64.urlsafe_b64decode(part["body"]["data"])
                        body_text = body_bytes.decode("utf-8", errors="replace")
                        break

            if not body_text:
                body_text = data.get("snippet", "")

            return {
                "id": message_id,
                "thread_id": data.get("threadId"),
                "headers": {h["name"]: h["value"] for h in headers_list},
                "snippet": data.get("snippet", ""),
                "body": body_text,
            }

    async def create_draft(
        self,
        recipient: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an email draft in the user's Gmail mailbox."""
        self._ensure_connected()

        message = MIMEText(body)
        message["to"] = recipient
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        msg_body: Dict[str, Any] = {"raw": raw}
        if thread_id:
            msg_body["threadId"] = thread_id

        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/drafts",
                headers=headers,
                json={"message": msg_body},
            )
            res.raise_for_status()
            return res.json()

    async def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send email directly through Gmail (Human approval required before calling)."""
        self._ensure_connected()

        message = MIMEText(body)
        message["to"] = recipient
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        payload: Dict[str, Any] = {"raw": raw}
        if thread_id:
            payload["threadId"] = thread_id

        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                headers=headers,
                json=payload,
            )
            res.raise_for_status()
            return res.json()
