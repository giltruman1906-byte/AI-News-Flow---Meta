"""Env + YAML config loader. Single source of truth for runtime knobs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
PROMPTS_DIR = ROOT / "prompts"


@dataclass
class Settings:
    # Meta
    meta_app_id: str
    meta_app_secret: str
    meta_page_id: str
    meta_page_access_token: str
    meta_ig_business_id: str

    # LLM
    llm_provider: str
    higgsfield_api_key: str
    higgsfield_base_url: str
    higgsfield_model: str
    anthropic_api_key: str
    anthropic_model: str

    # Storage
    google_sheets_id: str
    google_service_account_json: str

    # Image hosting
    github_repo: str
    github_published_branch: str
    github_token: str

    # Reddit
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str

    # Behavior
    min_score_auto_post: float
    min_score_floor_post: float
    min_posts_per_day: int
    timezone: str

    # YAML config
    sources: dict[str, Any]
    content_rules: dict[str, Any]


def load_settings() -> Settings:
    load_dotenv()
    sources = yaml.safe_load((CONFIG_DIR / "sources.yaml").read_text())
    content_rules = yaml.safe_load((CONFIG_DIR / "content_rules.yaml").read_text())
    return Settings(
        meta_app_id=os.getenv("META_APP_ID", ""),
        meta_app_secret=os.getenv("META_APP_SECRET", ""),
        meta_page_id=os.getenv("META_PAGE_ID", ""),
        meta_page_access_token=os.getenv("META_PAGE_ACCESS_TOKEN", ""),
        meta_ig_business_id=os.getenv("META_IG_BUSINESS_ID", ""),
        llm_provider=os.getenv("LLM_PROVIDER", "higgsfield"),
        higgsfield_api_key=os.getenv("HIGGSFIELD_API_KEY", ""),
        higgsfield_base_url=os.getenv("HIGGSFIELD_BASE_URL", ""),
        higgsfield_model=os.getenv("HIGGSFIELD_MODEL", ""),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        google_sheets_id=os.getenv("GOOGLE_SHEETS_ID", ""),
        google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", ""),
        github_repo=os.getenv("GITHUB_REPO", ""),
        github_published_branch=os.getenv("GITHUB_PUBLISHED_BRANCH", "published"),
        github_token=os.getenv("GITHUB_TOKEN", ""),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "suki-ai-news/0.1"),
        min_score_auto_post=float(os.getenv("MIN_SCORE_AUTO_POST", "8")),
        min_score_floor_post=float(os.getenv("MIN_SCORE_FLOOR_POST", "6")),
        min_posts_per_day=int(os.getenv("MIN_POSTS_PER_DAY", "2")),
        timezone=os.getenv("TIMEZONE", "America/New_York"),
        sources=sources,
        content_rules=content_rules,
    )


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text()


def parse_service_account(raw: str) -> dict[str, Any]:
    return json.loads(raw)
