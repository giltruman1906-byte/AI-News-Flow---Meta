"""Source fetchers. Each module returns a list of NewsItem dataclasses."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NewsItem:
    url: str
    title: str
    source: str            # human-readable source name (e.g. "anthropic.com")
    source_tier: str       # "vendor_blog" | "tech_press" | "hn" | "reddit"
    published_at: datetime
    summary: str = ""
    extra: dict = field(default_factory=dict)
