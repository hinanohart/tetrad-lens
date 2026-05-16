"""PII masking. Default ON. Opt-out is explicit and per-trace.

We piggy-back on Langfuse's mask= hook plus a small extra layer for the
tetrad.*.rationale fields, which can leak prompt content.

Patterns are deliberately conservative — false positives are preferred over
leaking real PII through the rationale string. The pattern set covers:

- Emails (RFC 5322 lite)
- Phone-looking numbers (must start with + or have 10+ digits; tightened to
  avoid matching plain invoice IDs)
- Common secret prefixes (sk-, pk-, ghp_, github_pat_, xoxb-, xoxp-, AIza, AKIA)
- HTTP Bearer headers
- Credit card numbers (Luhn-validated, 13-19 digits)
- US SSN (XXX-XX-XXXX)
- JWT tokens (three base64url segments separated by dots, starts with eyJ)
- IPv4 addresses
"""

from __future__ import annotations

import re
from typing import Any

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Phone: + country code (any length 7-15 digits) OR 10+ digits with separators.
# Excludes bare digit runs without separators (those look like invoice IDs).
_PHONE_RE = re.compile(
    r"\+\d[\d\-\s().]{6,18}\d"
    r"|\b\d{3}[\-\s.()]+\d{3}[\-\s.()]+\d{4}\b"
)
_SECRET_LOOKING_RE = re.compile(
    r"\b(?:sk|pk|ghp|github_pat|xoxb|xoxp|AIza|AKIA)[A-Za-z0-9_\-]{12,}\b"
)
_BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")
_IPV4_RE = re.compile(
    r"\b(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}\b"
)
# Credit-card-looking: 13-19 digits with optional spaces/dashes between groups.
_CC_CANDIDATE_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = ord(ch) - ord("0")
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0 and len(digits) >= 13


def _mask_credit_cards(text: str) -> str:
    def _repl(match: re.Match[str]) -> str:
        digits = re.sub(r"[ -]", "", match.group(0))
        return "[card]" if _luhn_ok(digits) else match.group(0)

    return _CC_CANDIDATE_RE.sub(_repl, text)


def mask_text(text: str) -> str:
    """Mask emails, phones, secret-looking tokens, bearer headers, SSNs, JWTs, IPs, and CCs."""
    if not text:
        return text
    # Order matters: JWT before bearer, secret before phone, CC last (it scans whole runs).
    text = _JWT_RE.sub("[jwt]", text)
    text = _EMAIL_RE.sub("[email]", text)
    text = _SECRET_LOOKING_RE.sub("[secret]", text)
    text = _BEARER_RE.sub("[bearer]", text)
    text = _SSN_RE.sub("[ssn]", text)
    text = _IPV4_RE.sub("[ip]", text)
    text = _PHONE_RE.sub("[phone]", text)
    text = _mask_credit_cards(text)
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
