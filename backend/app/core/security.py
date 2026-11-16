"""Security utilities: Argon2id password hashing, JWT session tokens, and Fernet encryption."""

import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
import argon2
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet
import jwt

from app.core.config import settings

# Initialize Argon2id password hasher (RFC 9106 recommended parameters)
_hasher = argon2.PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MiB
    parallelism=1,
    hash_len=32,
    type=argon2.Type.ID,
)


def hash_password(password: str) -> str:
    """Hash plaintext password using Argon2id."""
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify plaintext password against stored Argon2id hash."""
    try:
        return _hasher.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


# Credential encryption at rest
def _get_fernet() -> Fernet:
    """Obtain or derive 32-byte URL-safe base64 key for Fernet symmetric encryption."""
    raw_key = settings.CREDENTIAL_ENCRYPTION_KEY
    try:
        # Check if valid 32-byte base64
        key_bytes = base64.urlsafe_b64decode(raw_key.encode("utf-8"))
        if len(key_bytes) == 32:
            return Fernet(base64.urlsafe_b64encode(key_bytes))
    except Exception:
        pass
    # Fallback derivation: pad/hash to 32 bytes
    import hashlib
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(secret_text: str) -> str:
    """Encrypt sensitive credentials/tokens at rest."""
    if not secret_text:
        return ""
    fernet = _get_fernet()
    return fernet.encrypt(secret_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(encrypted_text: str) -> str:
    """Decrypt encrypted credential at rest."""
    if not encrypted_text:
        return ""
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
