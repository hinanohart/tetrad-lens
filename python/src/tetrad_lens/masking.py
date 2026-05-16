"""PII masking. Default ON. Opt-out is explicit and per-trace.

We piggy-back on Langfuse's mask= hook plus a small extra layer for the
tetrad.*.rationale fields, which can leak prompt content.
"""

from __future__ import annotations

import re
from typing import Any

# Patterns are deliberately conservative — false positives are preferred over
# leaking real PII through the rationale string.
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"\b\+?\d[\d\-\s().]{7,}\d\b")
_SECRET_LOOKING_RE = re.compile(
    r"\b(?:sk|pk|ghp|github_pat|xoxb|xoxp|AIza|AKIA)[A-Za-z0-9_\-]{12,}\b"
)
_BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+")


def mask_text(text: str) -> str:
    """Mask emails, phone-like numbers, secret-looking tokens, and bearer headers."""
    if not text:
        return text
    text = _EMAIL_RE.sub("[email]", text)
    text = _PHONE_RE.sub("[phone]", text)
    text = _SECRET_LOOKING_RE.sub("[secret]", text)
    text = _BEARER_RE.sub("[bearer]", text)
    return text


def mask_data(data: Any) -> Any:
    """Recursively mask strings inside nested dict/list structures.

    Used as the Langfuse `mask=` hook. Safe on circular-free trees only;
    in practice Langfuse passes JSON-ish payloads.
    """
    if isinstance(data, str):
        return mask_text(data)
    if isinstance(data, dict):
        return {k: mask_data(v) for k, v in data.items()}
    if isinstance(data, list):
        return [mask_data(v) for v in data]
    if isinstance(data, tuple):
        return tuple(mask_data(v) for v in data)
    return data
