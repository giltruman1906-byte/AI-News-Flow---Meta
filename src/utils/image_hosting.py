"""Image hosting via GitHub raw URLs.

Strategy: commit PNGs to the `published` orphan branch under
  `<yyyy>/<mm>/<dd>/<url_hash>/slide_<n>.png`
and return the raw.githubusercontent.com URL for each. Meta accepts these as
publicly-accessible image_url values for IG/FB carousel uploads.

When repo+token are not configured (smoke / dry-run), returns local file:// URLs
so the rest of the pipeline can continue.
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path

import httpx

log = logging.getLogger(__name__)


def raw_url(repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"


def _put_file(repo: str, branch: str, path: str, content_b64: str, token: str, message: str) -> None:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    # Check if exists to grab sha
    sha = None
    r = httpx.get(url, params={"ref": branch}, headers=headers, timeout=30)
    if r.status_code == 200:
        sha = r.json().get("sha")
    body = {"message": message, "content": content_b64, "branch": branch}
    if sha:
        body["sha"] = sha
    r = httpx.put(url, json=body, headers=headers, timeout=60)
    r.raise_for_status()


def upload(
    local_paths: list[Path],
    *,
    repo: str,
    branch: str,
    token: str,
    key_prefix: str,
) -> list[str]:
    """Push files to the published branch, return raw URLs in input order.

    If repo/token missing, returns file:// URLs (local-only mode)."""
    if not repo or not token:
        log.info("github image hosting not configured — returning file:// URLs")
        return [p.resolve().as_uri() for p in local_paths]

    urls: list[str] = []
    for p in local_paths:
        remote_path = f"{key_prefix}/{p.name}"
        content_b64 = base64.b64encode(p.read_bytes()).decode()
        _put_file(repo, branch, remote_path, content_b64, token, f"publish {remote_path}")
        urls.append(raw_url(repo, branch, remote_path))
    return urls
