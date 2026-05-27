"""ManyChat integration — update the latest_article_url bot field after each IG publish."""
from __future__ import annotations

import logging

import requests

log = logging.getLogger(__name__)

API_BASE = "https://api.manychat.com"
BOT_FIELD_NAME = "latest_article_url"


def update_article_url(api_key: str, article_url: str) -> bool:
    """Set the latest_article_url bot field so ManyChat DMs the correct link."""
    if not api_key:
        log.warning("MANYCHAT_API_KEY not set — skipping bot field update")
        return False

    resp = requests.post(
        f"{API_BASE}/fb/page/setBotFieldByName",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "field_name": BOT_FIELD_NAME,
            "field_value": article_url,
        },
        timeout=15,
    )

    if resp.status_code == 200 and resp.json().get("status") == "success":
        log.info("ManyChat bot field updated: %s", article_url)
        return True

    log.error("ManyChat API error %s: %s", resp.status_code, resp.text)
    return False
