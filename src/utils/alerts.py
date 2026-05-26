"""Failure alerts. No Telegram approval gate in v1 — this is just for crash signal.

For v1, log to stderr; GitHub Actions failure notifications cover the rest.
Stub kept so callers don't need to branch.
"""
from __future__ import annotations

import sys


def notify_failure(message: str) -> None:
    print(f"[ALERT] {message}", file=sys.stderr)
