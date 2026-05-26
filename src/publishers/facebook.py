"""Facebook Page carousel publisher.

Uses Graph API child-attachment flow on /{page_id}/feed. Each image is uploaded
unpublished to /{page_id}/photos, then referenced as `attached_media`.

When `token` is empty (Meta keys not yet approved), returns a fake post id so
the rest of the pipeline can be exercised end-to-end.
"""
from __future__ import annotations

import logging
import uuid

import httpx

from .meta_base import GRAPH_BASE, MetaError

log = logging.getLogger(__name__)


def _upload_photo(page_id: str, token: str, image_url: str) -> str:
    r = httpx.post(
        f"{GRAPH_BASE}/{page_id}/photos",
        data={"url": image_url, "published": "false", "access_token": token},
        timeout=60,
    )
    if r.status_code >= 400:
        raise MetaError(f"FB photo upload failed {r.status_code}: {r.text}")
    return r.json()["id"]


def publish(page_id: str, token: str, image_urls: list[str], caption: str) -> str:
    """Return the FB post id."""
    if not token or not page_id:
        fake = f"fb_dryrun_{uuid.uuid4().hex[:10]}"
        log.warning("FB token/page_id missing — DRY RUN, returning %s", fake)
        return fake

    photo_ids = [_upload_photo(page_id, token, u) for u in image_urls]
    data = {"message": caption, "access_token": token}
    for i, pid in enumerate(photo_ids):
        data[f"attached_media[{i}]"] = f'{{"media_fbid":"{pid}"}}'
    r = httpx.post(f"{GRAPH_BASE}/{page_id}/feed", data=data, timeout=60)
    if r.status_code >= 400:
        raise MetaError(f"FB feed publish failed {r.status_code}: {r.text}")
    return r.json()["id"]
