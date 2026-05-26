"""Generate the 7-slide carousel content + FB caption."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field

from ..sources import NewsItem
from .llm_client import LLMClient


@dataclass
class CarouselContent:
    # Slide 1 — Cover
    slide_1_hook: str
    slide_1_subtitle: str
    date_label: str = ""
    # Slide 2 — The Play (big statement)
    slide_2_play: str = ""
    slide_2_accent: str = ""
    # Slides 3-5 — Numbered content cards
    slide_3_headline: str = ""
    slide_3_body: str = ""
    slide_4_headline: str = ""
    slide_4_body: str = ""
    slide_5_headline: str = ""
    slide_5_body: str = ""
    # Slide 6 — Leverage / stat comparison
    slide_6_stat_top: str = ""
    slide_6_stat_bottom: str = ""
    slide_6_body: str = ""
    # Caption
    fb_caption: str = ""
    hashtags: list[str] = field(default_factory=list)


def _date_label() -> str:
    now = datetime.datetime.now()
    return f"AI NEWS · {now.strftime('%B %Y').upper()}"


def rewrite(item: NewsItem, client: LLMClient, prompt_template: str) -> CarouselContent:
    prompt = (
        prompt_template
        .replace("{title}", item.title)
        .replace("{url}", item.url)
        .replace("{source}", item.source)
        .replace("{summary}", item.summary[:4000])
    )
    data = client.complete_json(prompt)
    tags = data.get("hashtags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split() if t.strip()]
    return CarouselContent(
        slide_1_hook=str(data.get("slide_1_hook", item.title))[:120],
        slide_1_subtitle=str(data.get("slide_1_subtitle", ""))[:300],
        date_label=_date_label(),
        slide_2_play=str(data.get("slide_2_play", ""))[:200],
        slide_2_accent=str(data.get("slide_2_accent", ""))[:60],
        slide_3_headline=str(data.get("slide_3_headline", ""))[:80],
        slide_3_body=str(data.get("slide_3_body", ""))[:300],
        slide_4_headline=str(data.get("slide_4_headline", ""))[:80],
        slide_4_body=str(data.get("slide_4_body", ""))[:300],
        slide_5_headline=str(data.get("slide_5_headline", ""))[:80],
        slide_5_body=str(data.get("slide_5_body", ""))[:300],
        slide_6_stat_top=str(data.get("slide_6_stat_top", ""))[:20],
        slide_6_stat_bottom=str(data.get("slide_6_stat_bottom", ""))[:20],
        slide_6_body=str(data.get("slide_6_body", ""))[:300],
        fb_caption=str(data.get("fb_caption", "")),
        hashtags=[str(t) for t in tags][:8],
    )
