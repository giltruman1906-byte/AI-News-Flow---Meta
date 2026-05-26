"""Shared Meta Graph API helpers."""
from __future__ import annotations

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class MetaError(Exception):
    pass
