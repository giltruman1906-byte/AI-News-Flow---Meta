"""RSS/Atom fetcher (feedparser + requests for SSL)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

import feedparser
import requests

from . import NewsItem

log = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "Mozilla/5.0 (compatible; SukiAINews/1.0)"


def _parse_published(entry) -> datetime:
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(tz=timezone.utc)


def _source_name(feed_url: str, feed) -> str:
    title = (feed.feed.get("title") or "").strip() if hasattr(feed, "feed") else ""
    if title:
        return title
    return urlparse(feed_url).netloc.removeprefix("www.")


def fetch(urls_by_tier: dict[str, list[str]], lookback_hours: int = 48) -> list[NewsItem]:
    since = datetime.now(tz=timezone.utc) - timedelta(hours=lookback_hours)
    items: list[NewsItem] = []
    for tier, urls in urls_by_tier.items():
        for url in urls:
            try:
                resp = _SESSION.get(url, timeout=15)
                resp.raise_for_status()
                parsed = feedparser.parse(resp.content)
            except Exception as exc:
                log.warning("rss fetch failed %s: %s", url, exc)
                continue
            if parsed.bozo and not parsed.entries:
                log.warning("rss empty/bozo %s", url)
                continue
            src_name = _source_name(url, parsed)
            for entry in parsed.entries:
                link = entry.get("link")
                title = entry.get("title")
                if not link or not title:
                    continue
                published_at = _parse_published(entry)
                pub_aware = published_at.replace(tzinfo=timezone.utc) if published_at.tzinfo is None else published_at
                if pub_aware < since:
                    continue
                summary = entry.get("summary", "") or entry.get("description", "") or ""
                items.append(
                    NewsItem(
                        url=link,
                        title=title.strip(),
                        source=src_name,
                        source_tier=tier,
                        published_at=published_at,
                        summary=summary[:2000],
                    )
                )
    return items
