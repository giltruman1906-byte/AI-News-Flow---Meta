"""2-per-day floor logic, NY-timezone aware. Pure function — easy to unit test.

Rules:
- NY hour < auto_post_cutoff_hour (18): publish only score >= min_auto_post.
- auto_post_cutoff_hour <= hour < stop_hour (22): also pull from floor pool
  (score in [min_floor_post, min_auto_post)) until posts_today >= min_posts_per_day.
- hour >= stop_hour: do nothing — avoid graveyard slot.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass
class Candidate:
    url: str
    score: float


@dataclass
class Decision:
    publish: list[Candidate]   # ordered, highest-score first
    reason: str


def decide(
    *,
    now_ny: datetime,
    posts_today: int,
    candidates: Iterable[Candidate],
    min_auto_post: float,
    min_floor_post: float,
    min_posts_per_day: int,
    auto_post_cutoff_hour: int = 18,
    stop_hour: int = 22,
) -> Decision:
    hour = now_ny.hour
    if hour >= stop_hour:
        return Decision(publish=[], reason=f"after stop_hour {stop_hour} NY — skip")

    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
    auto = [c for c in ranked if c.score >= min_auto_post]
    floor = [c for c in ranked if min_floor_post <= c.score < min_auto_post]

    if hour < auto_post_cutoff_hour:
        if not auto:
            return Decision(publish=[], reason="pre-cutoff, no auto-post candidates")
        return Decision(publish=[auto[0]], reason="auto-post (score>=min_auto_post)")

    # In floor window [cutoff, stop). Always publish best auto if present; top up with floor.
    to_publish: list[Candidate] = []
    if auto:
        to_publish.append(auto[0])
    deficit = max(0, min_posts_per_day - posts_today - len(to_publish))
    if deficit > 0:
        to_publish.extend(floor[:deficit])
    if not to_publish:
        return Decision(publish=[], reason="floor window, but daily quota met and no auto-post")
    return Decision(publish=to_publish, reason=f"floor window: auto={len(auto[:1])} floor_used={len(to_publish)-len(auto[:1])}")
