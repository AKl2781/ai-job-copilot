"""Stable fingerprints for idempotent saved-job creation."""

from __future__ import annotations

import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_WHITESPACE = re.compile(r"\s+")
_TRANSIENT_QUERY_KEYS = {
    "_",
    "access_token",
    "auth",
    "auth_token",
    "callback",
    "expires",
    "from",
    "nonce",
    "random",
    "requestid",
    "rnd",
    "securityid",
    "session",
    "sessionid",
    "sig",
    "signature",
    "timestamp",
    "token",
    "traceid",
    "trackingid",
    "ts",
}
_TRANSIENT_QUERY_PREFIXES = ("utm_",)


def _normalize_text(value: str | None) -> str:
    return _WHITESPACE.sub(" ", value.strip()).lower() if value else ""


def normalize_job_source_url(source_url: str) -> str:
    """Remove volatile URL parts while retaining a stable job-detail locator."""
    raw_url = source_url.strip()
    parts = urlsplit(raw_url)

    scheme = parts.scheme.lower()
    hostname = (parts.hostname or "").lower()
    port = parts.port
    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        hostname = f"{hostname}:{port}"
    if parts.username:
        credentials = parts.username
        if parts.password:
            credentials = f"{credentials}:{parts.password}"
        hostname = f"{credentials}@{hostname}"

    stable_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        normalized_key = key.lower()
        if normalized_key in _TRANSIENT_QUERY_KEYS:
            continue
        if any(normalized_key.startswith(prefix) for prefix in _TRANSIENT_QUERY_PREFIXES):
            continue
        stable_query.append((key, value))
    stable_query.sort(key=lambda item: (item[0].lower(), item[1]))

    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, hostname, path, urlencode(stable_query, doseq=True), ""))


def generate_job_fingerprint(
    *,
    source_url: str | None,
    title: str,
    company: str | None,
    description: str,
) -> str:
    """Build a SHA-256 fingerprint from the URL or normalized job content."""
    if source_url and source_url.strip():
        fingerprint_input = f"url\x1f{normalize_job_source_url(source_url)}"
    else:
        fields = (
            _normalize_text(title),
            _normalize_text(company),
            _normalize_text(description),
        )
        fingerprint_input = "content\x1f" + "\x1f".join(fields)
    return hashlib.sha256(fingerprint_input.encode("utf-8")).hexdigest()
