"""Centralized redaction for persisted traces, logs, and API payloads."""

import re
from typing import Any, Iterable

SENSITIVE_KEY_RE = re.compile(
    r"(api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|secret|credential)",
    re.IGNORECASE,
)


def redact(value: Any, sensitive_fields: Iterable[str] = ()) -> Any:
    fields = {field.lower() for field in sensitive_fields}
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key.lower() in fields or SENSITIVE_KEY_RE.search(key):
                result[key] = "[REDACTED]"
            else:
                result[key] = redact(item, fields)
        return result
    if isinstance(value, list):
        return [redact(item, fields) for item in value]
    if isinstance(value, str):
        return re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer [REDACTED]", value, flags=re.IGNORECASE)
    return value
