"""Instagram Business carousel publisher (2-step container flow).

Polls each child container's status_code until FINISHED before publishing.
When token is empty (Meta keys not yet approved), returns fake ids so the
pipeline can be smoke-tested end-to-end.
"""
from __future__ import annotations

import logging
import time
import uuid

import httpx

from .meta_base import GRAPH_BASE, MetaError

log = logging.getLogger(__name__)

POLL_INTERVAL_S = 3
POLL_TIMEOUT_S = 180


def _create_child(ig_business_id: str, token: str, image_url: str) -> str:
    r = httpx.post(
        f"{GRAPH_BASE}/{ig_business_id}/media",
        data={
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": token,
        },
        timeout=60,
    )
    if r.status_code >= 400:
        raise MetaError(f"IG child create failed {r.status_code}: {r.text}")
    return r.json()["id"]


def _wait_finished(container_id: str, token: str) -> None:
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        r = httpx.get(
            f"{GRAPH_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        if r.status_code >= 400:
            raise MetaError(f"IG status poll failed {r.status_code}: {r.text}")
        status = r.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise MetaError(f"IG container {container_id} ERRORed")
        time.sleep(POLL_INTERVAL_S)
    raise MetaError(f"IG container {container_id} did not finish in {POLL_TIMEOUT_S}s")


def publish(ig_business_id: str, token: str, image_urls: list[str], caption: str) -> tuple[str, str]:
    """Return (ig_post_id, ig_carousel_container_id)."""
    if not token or not ig_business_id:
        fake_post = f"ig_dryrun_{uuid.uuid4().hex[:10]}"
        fake_container = f"ig_container_dryrun_{uuid.uuid4().hex[:10]}"
        log.warning("IG token/business_id missing — DRY RUN, returning %s", fake_post)
        return fake_post, fake_container

    child_ids: list[str] = []
    for u in image_urls:
        cid = _create_child(ig_business_id, token, u)
        _wait_finished(cid, token)
        child_ids.append(cid)

    r = httpx.post(
        f"{GRAPH_BASE}/{ig_business_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(child_ids),
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )
    if r.status_code >= 400:
        raise MetaError(f"IG carousel create failed {r.status_code}: {r.text}")
    carousel_id = r.json()["id"]
    _wait_finished(carousel_id, token)

    r = httpx.post(
        f"{GRAPH_BASE}/{ig_business_id}/media_publish",
        data={"creation_id": carousel_id, "access_token": token},
        timeout=60,
    )
    if r.status_code >= 400:
        raise MetaError(f"IG publish failed {r.status_code}: {r.text}")
    return r.json()["id"], carousel_id
