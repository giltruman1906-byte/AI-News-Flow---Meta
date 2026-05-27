"""ManyChat integration — update the latest_article_url bot field + GitHub Pages redirect."""
from __future__ import annotations

import base64
import logging

import httpx
import requests

log = logging.getLogger(__name__)

API_BASE = "https://api.manychat.com"
BOT_FIELD_NAME = "latest_article_url"
REDIRECT_PATH = "article/index.html"

REDIRECT_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="0; url={url}">
<title>Redirecting...</title>
</head>
<body>
<p>Redirecting to the article... <a href="{url}">Click here</a> if not redirected.</p>
</body>
</html>
"""


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


def update_redirect_page(repo: str, branch: str, token: str, article_url: str) -> bool:
    """Update the GitHub Pages redirect so the fixed ManyChat link points to the latest article."""
    if not token or not repo:
        log.warning("GitHub token/repo not set — skipping redirect update")
        return False

    html = REDIRECT_TEMPLATE.format(url=article_url)
    content_b64 = base64.b64encode(html.encode()).decode()
    api_url = f"https://api.github.com/repos/{repo}/contents/{REDIRECT_PATH}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    existing = httpx.get(f"{api_url}?ref={branch}", headers=headers, timeout=15)
    sha = existing.json().get("sha") if existing.status_code == 200 else None

    payload = {"message": f"update redirect → {article_url}", "content": content_b64, "branch": branch}
    if sha:
        payload["sha"] = sha

    r = httpx.put(api_url, headers=headers, json=payload, timeout=15)
    if r.status_code in (200, 201):
        log.info("Redirect page updated → %s", article_url)
        return True

    log.error("Redirect update failed %s: %s", r.status_code, r.text)
    return False
