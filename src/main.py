"""Pipeline orchestrator. Entry point for `python -m src.main`.

Flow:
  1. Load settings + caches (Sheets dedup, posts).
  2. Fetch from RSS, HN, Reddit. Tag each item with its source_tier.
  3. Drop items already in dedup.
  4. Score each new item (LLM + source-tier bonus).
  5. Record dedup row for every scored item (status: skipped|queued).
  6. Run scheduler to decide what publishes this cycle.
  7. For each chosen item: rewrite -> build carousel -> upload images
     -> publish to FB + IG -> append post row.
  8. Soft-fail per item — one bad item doesn't kill the run.

Modes:
  --smoke    : zero network. Uses stub sources + stub LLM + in-memory store +
               local file:// image URLs + dry-run publishers. Verifies plumbing.
  --dry-run  : real sources + LLM if configured, no real publishing (token-gated).
  (default)  : full production run.
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .ai import rewriter, scorer
from .ai.llm_client import StubClient, build_client
from .carousel import builder as carousel_builder
from .config import load_prompt, load_settings, parse_service_account
from .posting.scheduler import Candidate, decide
from .posting.manychat import update_article_url, update_redirect_page
from .publishers import facebook, instagram
from .sources import NewsItem, hackernews, reddit, rss
from .storage.sheets import DedupRow, InMemoryStore, PostRow, build_store, utcnow
from .utils.hashing import url_hash
from .utils.image_hosting import upload as upload_images

log = logging.getLogger("suki-ai-news")

NY = ZoneInfo("America/New_York")


def _stub_fixture_items() -> list[NewsItem]:
    fixture = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample_news.json"
    raw = json.loads(fixture.read_text())
    out: list[NewsItem] = []
    for r in raw:
        out.append(NewsItem(
            url=r["url"],
            title=r["title"],
            source=r["source"],
            source_tier=r["source_tier"],
            published_at=datetime.fromisoformat(r["published_at"].replace("Z", "+00:00")),
            summary=r.get("summary", ""),
        ))
    return out


def fetch_all(settings, smoke: bool) -> list[NewsItem]:
    if smoke:
        log.info("smoke mode — using fixture items")
        return _stub_fixture_items()

    items: list[NewsItem] = []
    items.extend(rss.fetch(settings.sources["rss"]))
    hn = settings.sources["hackernews"]
    items.extend(hackernews.fetch(hn["query"], hn["min_points"], hn["lookback_hours"]))
    rd = settings.sources.get("reddit")
    if rd:
        items.extend(reddit.fetch(rd["subreddits"], rd["min_upvotes"], rd["lookback_hours"]))
    log.info("fetched %d raw items", len(items))
    return items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Score+render, skip publishing")
    parser.add_argument("--smoke", action="store_true", help="Stub sources/LLM/storage; no network")
    parser.add_argument("--limit", type=int, default=0, help="Max fresh items to score (0=unlimited)")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    settings = load_settings()
    rules = settings.content_rules
    smoke = args.smoke

    log.info("loaded settings; provider=%s smoke=%s dry_run=%s",
             settings.llm_provider, smoke, args.dry_run)

    # LLM client
    if smoke:
        llm = StubClient()
    else:
        llm = build_client(settings.llm_provider, settings)

    # Storage
    if smoke:
        store = InMemoryStore()
    else:
        sa = parse_service_account(settings.google_service_account_json) if settings.google_service_account_json else None
        store = build_store(settings.google_sheets_id, sa)

    # 1. Load dedup — only block articles seen in the last 30 days.
    # Without this window the cache grows unboundedly and eventually covers the
    # entire RSS corpus, producing 0 fresh items on every run.
    dedup_rows = store.load_dedup()
    dedup_cutoff = datetime.now(tz=timezone.utc) - timedelta(days=30)
    seen_hashes = {
        r.url_hash for r in dedup_rows
        if r.seen_at.replace(tzinfo=timezone.utc) >= dedup_cutoff
    }
    log.info("dedup cache: %d entries (%d total rows, 30-day window)", len(seen_hashes), len(dedup_rows))

    # 2-3. Fetch + filter
    items = fetch_all(settings, smoke)
    fresh = [it for it in items if url_hash(it.url) not in seen_hashes]
    log.info("fresh items: %d / %d", len(fresh), len(items))

    # 4-5. Score
    scorer_prompt = load_prompt("scorer")
    tier_bonus = rules["scoring"]["source_tier_bonus"]
    min_auto = rules["scoring"]["min_auto_post"]
    min_floor = rules["scoring"]["min_floor_post"]
    discard_below = rules["scoring"]["discard_below"]

    new_dedup_rows: list[DedupRow] = []
    candidates: list[tuple[NewsItem, float]] = []
    if args.limit:
        fresh = fresh[:args.limit]
    for item in fresh:
        try:
            result = scorer.score(item, llm, scorer_prompt, tier_bonus)
        except Exception as exc:
            log.warning("scorer failed on %s: %s", item.url, exc)
            continue
        status = "skipped" if result.score < discard_below else "queued"
        new_dedup_rows.append(DedupRow(
            url_hash=url_hash(item.url),
            url=item.url,
            title=item.title,
            source=item.source,
            source_tier=item.source_tier,
            seen_at=utcnow(),
            score=result.score,
            status=status,
        ))
        log.info("scored %.1f %s — %s", result.score, item.source_tier, item.title[:80])
        if status == "queued":
            candidates.append((item, result.score))

    store.append_dedup(new_dedup_rows)

    # 6. Schedule
    posting = rules["posting"]
    now_ny = datetime.now(tz=NY)
    decision = decide(
        now_ny=now_ny,
        posts_today=store.posts_today_ny(),
        candidates=[Candidate(url=it.url, score=sc) for it, sc in candidates],
        min_auto_post=min_auto,
        min_floor_post=min_floor,
        min_posts_per_day=posting["min_posts_per_day"],
        auto_post_cutoff_hour=posting["auto_post_cutoff_hour"],
        stop_hour=posting["stop_hour"],
    )
    log.info("schedule decision: %s — %d to publish",
             decision.reason, len(decision.publish))

    chosen_urls = {c.url for c in decision.publish}
    score_by_url = {it.url: sc for it, sc in candidates}
    chosen_items = [it for it, _ in candidates if it.url in chosen_urls]

    # 7. Publish each
    rewriter_prompt = load_prompt("rewriter")
    cta = rules["cta"]
    for item in chosen_items:
        try:
            _publish_one(item, score_by_url[item.url], settings, rules, llm,
                         rewriter_prompt, cta, store,
                         dry_run=args.dry_run or smoke)
        except Exception as exc:
            log.exception("publish failed for %s: %s", item.url, exc)

    log.info("cycle complete")
    return 0


def _publish_one(item: NewsItem, score: float, settings, rules, llm, rewriter_prompt, cta, store,
                 *, dry_run: bool) -> None:
    content = rewriter.rewrite(item, llm, rewriter_prompt)
    # Enforce fixed hashtags + cap
    fixed = rules["hashtags"]["fixed"]
    llm_max = rules["hashtags"]["llm_max"]
    extra = [t for t in content.hashtags if t not in fixed][:llm_max]
    hashtags = fixed + extra
    fb_signoff = cta.get("fb_signoff_url", "")
    fb_caption = f"{content.fb_caption}\n\n→ Read the full article: {item.url}\n\n→ Book a free audit: {fb_signoff}\n\n{' '.join(hashtags)}"
    keyword = cta.get("keyword", "ARTICLE")
    ig_caption = f"{content.slide_1_hook}\n\n{content.slide_3_body}\n\n{content.slide_4_body}\n\n{content.slide_5_body}\n\nComment \"{keyword}\" and we'll DM you the full article.\n\n{' '.join(hashtags)}"

    published_root = Path(__file__).resolve().parent.parent / "published"
    key_prefix_date = item.published_at.strftime("%Y/%m/%d")
    key_prefix = f"{key_prefix_date}/{url_hash(item.url)}"
    local_dir = published_root / key_prefix
    local_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        ig_dir = Path(td) / "ig"
        fb_dir = Path(td) / "fb"
        ig_paths = carousel_builder.build(content, cta, ig_dir, platform="ig")
        fb_paths = carousel_builder.build(content, cta, fb_dir, platform="fb")
        log.info("rendered %d IG + %d FB slides for %s", len(ig_paths), len(fb_paths), item.url)

        # Save IG slides locally to published/
        saved_paths = []
        for p in ig_paths:
            dest = local_dir / p.name
            shutil.copy2(p, dest)
            saved_paths.append(dest)
        log.info("saved slides to %s", local_dir)

        if dry_run:
            ig_image_urls = [p.resolve().as_uri() for p in saved_paths]
            fb_image_urls = [p.resolve().as_uri() for p in fb_paths]
        else:
            ig_image_urls = upload_images(
                ig_paths,
                repo=settings.github_repo,
                branch=settings.github_published_branch,
                token=settings.github_token,
                key_prefix=f"{key_prefix}/ig",
            )
            fb_image_urls = upload_images(
                fb_paths,
                repo=settings.github_repo,
                branch=settings.github_published_branch,
                token=settings.github_token,
                key_prefix=f"{key_prefix}/fb",
            )
        log.info("ig image urls: %s", ig_image_urls)
        log.info("fb image urls: %s", fb_image_urls)

        # Publish — dry-run skips Meta calls
        if dry_run:
            log.info("DRY RUN — skipping FB+IG publish for %s", item.url)
            fb_id = f"fb_dryrun_{url_hash(item.url)}"
            ig_id, carousel_id = f"ig_dryrun_{url_hash(item.url)}", f"ig_container_dryrun_{url_hash(item.url)}"
        else:
            fb_id = facebook.publish(settings.meta_page_id, settings.meta_page_access_token,
                                      fb_image_urls, fb_caption)
            ig_id, carousel_id = instagram.publish(
                settings.meta_ig_business_id, settings.meta_page_access_token,
                ig_image_urls, ig_caption,
            )
            update_article_url(settings.manychat_api_key, item.url)
            update_redirect_page(settings.github_repo, settings.github_published_branch,
                                 settings.github_token, item.url)

    now_utc = datetime.now(tz=timezone.utc)
    store.append_post(PostRow(
        posted_at_utc=now_utc,
        posted_at_ny=now_utc.astimezone(NY),
        url=item.url,
        title=item.title,
        score=score,
        fb_post_id=fb_id,
        ig_post_id=ig_id,
        ig_carousel_id=carousel_id,
    ))
    log.info("published %s: fb=%s ig=%s", item.url, fb_id, ig_id)


if __name__ == "__main__":
    raise SystemExit(main())
