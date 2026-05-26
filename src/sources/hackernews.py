"""Hacker News via Algolia search_by_date."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from . import NewsItem

log = logging.getLogger(__name__)

ALGOLIA = "https://hn.algolia.com/api/v1/search_by_date"


def fetch(query: str, min_points: int, lookback_hours: int) -> list[NewsItem]:
    since = int(time.time()) - lookback_hours * 3600
    params = {
        "query": query,
        "tags": "story",
        "numericFilters": f"points>{min_points},created_at_i>{since}",
        "hitsPerPage": 50,
    }
    try:
        r = httpx.get(ALGOLIA, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        log.warning("hn fetch failed: %s", exc)
        return []

    items: list[NewsItem] = []
    for hit in data.get("hits", []):
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        title = hit.get("title")
        if not title:
            continue
        created = hit.get("created_at_i") or 0
        items.append(
            NewsItem(
                url=url,
                title=title,
                source="Hacker News",
                source_tier="hn",
                published_at=datetime.fromtimestamp(created, tz=timezone.utc),
                summary="",
                extra={"points": hit.get("points", 0)},
            )
        )
    return items
