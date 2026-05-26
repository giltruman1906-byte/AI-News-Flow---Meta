"""URL canonicalization + stable hashing for dedup."""
from __future__ import annotations

import hashlib
from urllib.parse import urlparse, urlunparse

_TRACKING_PREFIXES = ("utm_", "ref_", "fbclid", "gclid", "mc_")


def canonicalize(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = "https"
    netloc = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/") or "/"
    kept = []
    for kv in parsed.query.split("&"):
        if not kv:
            continue
        k = kv.split("=", 1)[0]
        if not any(k.startswith(p) for p in _TRACKING_PREFIXES):
            kept.append(kv)
    query = "&".join(sorted(kept))
    return urlunparse((scheme, netloc, path, "", query, ""))


def url_hash(url: str) -> str:
    return hashlib.sha256(canonicalize(url).encode()).hexdigest()[:16]
