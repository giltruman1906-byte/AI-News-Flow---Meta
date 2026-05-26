"""Reddit via praw. Returns [] silently if creds are missing."""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from . import NewsItem

log = logging.getLogger(__name__)


def fetch(subreddits: list[str], min_upvotes: int, lookback_hours: int) -> list[NewsItem]:
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT", "suki-ai-news/0.1")
    if not client_id or not client_secret:
        log.info("reddit creds missing — skipping")
        return []

    try:
        import praw  # type: ignore
    except ImportError:
        log.warning("praw not installed")
        return []

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        reddit.read_only = True
    except Exception as exc:
        log.warning("reddit init failed: %s", exc)
        return []

    cutoff = time.time() - lookback_hours * 3600
    items: list[NewsItem] = []
    for sub in subreddits:
        try:
            for post in reddit.subreddit(sub).new(limit=50):
                if post.created_utc < cutoff:
                    continue
                if post.score < min_upvotes:
                    continue
                url = post.url if not post.is_self else f"https://reddit.com{post.permalink}"
                items.append(
                    NewsItem(
                        url=url,
                        title=post.title,
                        source=f"r/{sub}",
                        source_tier="reddit",
                        published_at=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                        summary=(post.selftext or "")[:1000],
                        extra={"upvotes": post.score},
                    )
                )
        except Exception as exc:
            log.warning("reddit fetch failed for r/%s: %s", sub, exc)
    return items
