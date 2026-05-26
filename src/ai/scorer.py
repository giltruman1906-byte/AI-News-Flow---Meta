"""Score a NewsItem 1-10 via LLM; apply source-tier bonus on top."""
from __future__ import annotations

from dataclasses import dataclass

from ..sources import NewsItem
from .llm_client import LLMClient


@dataclass
class ScoreResult:
    score: float           # final score, source-tier bonus applied, clamped to [1, 10]
    raw_llm_score: float
    reason: str
    category: str


def score(item: NewsItem, client: LLMClient, prompt_template: str, tier_bonus: dict[str, float]) -> ScoreResult:
    prompt = (
        prompt_template
        .replace("{title}", item.title)
        .replace("{source}", item.source)
        .replace("{source_tier}", item.source_tier)
        .replace("{published_at}", item.published_at.isoformat())
        .replace("{summary}", item.summary[:4000])
    )
    data = client.complete_json(prompt)
    raw = float(data.get("score", 0))
    bonus = float(tier_bonus.get(item.source_tier, 0.0))
    final = max(1.0, min(10.0, raw + bonus))
    return ScoreResult(
        score=final,
        raw_llm_score=raw,
        reason=str(data.get("reason", ""))[:300],
        category=str(data.get("category", "other")),
    )
