# Suki AI News — QA Agent

Run this document whenever something feels off, after any significant code change, or before a deploy.
Each finding lists: severity, location, what the bug is, and current status.

---

## How to use this file

1. Read through every open finding below.
2. Grep the codebase for the listed location to verify it still applies.
3. Mark `[FIXED]` when resolved, add the date.
4. Add new findings at the bottom under **New Findings**.

---

## Critical Bugs

### C-1 — Cron fired at midnight NY (posting window bypass)
**Status:** FIXED 2026-06-06
**File:** `.github/workflows/publish.yml` line 5
**Was:** `"0 4 */2 * *"` = 04:00 UTC = 00:00 AM EDT — posts went out at midnight, terrible for engagement.
**Fix:** Changed to `"0 14 */2 * *"` = 14:00 UTC = 10:00 AM EDT / 17:00 IDT.
**Verify:** `grep "cron:" .github/workflows/publish.yml` should show `0 14`.

---

### C-2 — Scheduler time-window logic is dead code when running every 2 days
**Status:** OPEN (accepted / low-harm)
**File:** `src/posting/scheduler.py`, `config/content_rules.yaml`
**What:** The scheduler has a `floor window` (18:00–22:00 NY) and `min_posts_per_day: 1` concept. These only make sense if the pipeline runs many times a day. With one run every 2 days, `posts_today` will always be 0 at run time, the floor window logic never activates, and the pipeline always auto-posts if score >= 8.
**Impact:** No posts are incorrectly blocked — the auto-post branch runs correctly. But `auto_post_cutoff_hour`, `stop_hour`, and `min_posts_per_day` in `content_rules.yaml` are misleading.
**Recommendation:** Either accept as-is (harmless) or remove the floor/cutoff logic and simplify to "if score >= 8, post; else skip."

---

## Medium Bugs

### M-1 — `booking_url` used wrong config key
**Status:** FIXED 2026-06-06
**File:** `src/main.py` line 208
**Was:** `cta.get("fb_signoff_url", ...)` — pulled the FB URL instead of the IG booking URL key.
**Fix:** Changed to `cta.get("booking_url", "https://cal.com/suki-systems/30min")`.
**Verify:** `grep "booking_url" src/main.py` should show `cta.get("booking_url"`.

---

### M-2 — `booking_url` in content_rules.yaml was missing `https://`
**Status:** FIXED 2026-06-06
**File:** `config/content_rules.yaml` under `cta:`
**Was:** `booking_url: "cal.com/suki-systems/30min"` — would produce a broken link in IG caption.
**Fix:** Added `https://` prefix.
**Verify:** `grep "booking_url" config/content_rules.yaml` should show `https://`.

---

### M-3 — Dead Settings fields: `min_score_auto_post`, `min_score_floor_post`, `min_posts_per_day`
**Status:** OPEN
**File:** `src/config.py` lines 88–90 vs `src/main.py` lines 132–134
**What:** `config.py` loads `MIN_SCORE_AUTO_POST`, `MIN_SCORE_FLOOR_POST`, `MIN_POSTS_PER_DAY` env vars into the `Settings` dataclass. But `main.py` reads these values from `content_rules.yaml` directly (`rules["scoring"]["min_auto_post"]` etc.), never touching `settings.min_score_auto_post`. So env var overrides have zero effect.
**Impact:** If you set `MIN_SCORE_AUTO_POST=7` in GitHub Secrets to lower the bar, nothing changes.
**Fix options:** Either (a) have `main.py` read from `settings.*` instead of the YAML, or (b) remove the dead fields from `Settings`.
**Also:** `.env.example` says `MIN_POSTS_PER_DAY=2` but `content_rules.yaml` has `min_posts_per_day: 1` — they diverged silently.

---

### M-4 — Emoji policy is contradicted in three places
**Status:** OPEN
**Files:** `prompts/rewriter.md`, `config/content_rules.yaml`, `src/main.py` line 209
**What:**
- `prompts/rewriter.md` tells the LLM: "zero emojis everywhere."
- `content_rules.yaml` `voice.emoji_policy` says: "max 1 emoji in slide 1 hook; zero elsewhere; zero in fb_caption."
- `src/main.py` hardcodes a 👇 emoji in the IG caption.
**Impact:** The LLM-generated content has no emojis, but the IG caption always has one. Probably intentional for the CTA arrow, but the policies should be consistent to avoid confusion.
**Recommendation:** Pick one policy and document it in one place. If 👇 is intentional, update rewriter.md to say "zero emojis in generated content; CTA arrow is added by the pipeline."

---

### M-5 — `StubClient` returned stale rewriter field names (smoke tests were silently broken)
**Status:** FIXED 2026-06-06
**File:** `src/ai/llm_client.py` `StubClient.complete_json`
**Was:** Returned `slide_2_what`, `slide_3_why`, `slide_4_take` — none of which exist in `CarouselContent`. Smoke test ran but rendered blank slide bodies.
**Fix:** Updated to match the actual 7-slide schema (`slide_2_play`, `slide_2_accent`, `slide_3_headline`, `slide_3_body`, etc.).
**Verify:** `python -m src.main --smoke` should show non-empty slide content in the rendered PNGs.

---

### M-6 — `seen_at` timezone handling is inconsistent
**Status:** OPEN (low practical risk)
**File:** `src/storage/sheets.py` line 137, `src/main.py` line 120
**What:** `load_dedup()` parses `seen_at` with `datetime.fromisoformat()`. If the stored string includes `+00:00` (which it will from `utcnow()`), the result is a timezone-aware datetime. Then `main.py` calls `.replace(tzinfo=timezone.utc)` which replaces the tzinfo rather than converting — harmless when already UTC, but could silently corrupt data if any row has a non-UTC timezone attached (e.g. manual edit with a local timestamp).
**Fix:** Use `dt.astimezone(timezone.utc)` instead of `.replace(tzinfo=timezone.utc)` in the dedup filter, and add a `try/except` for rows where `seen_at` is naive (fallback: treat as UTC).

---

## Low / Info Findings

### L-1 — No retry logic despite `tenacity` being installed
**Status:** OPEN
**Files:** `src/utils/image_hosting.py`, `src/publishers/instagram.py`, `src/publishers/facebook.py`
**What:** `pyproject.toml` declares `tenacity>=8.3` but no HTTP call uses it. A single transient failure in image upload or Meta API kills the publish for that item.
**Impact:** Items that fail due to a flaky network call are written to dedup as `queued` but never published — lost forever since dedup blocks them for 30 days.
**Recommendation:** Wrap `_put_file()`, `_create_child()`, `_upload_photo()` with `@retry(stop=stop_after_attempt(3), wait=wait_exponential())`.

---

### L-2 — `manychat.py` is dead code
**Status:** OPEN (cosmetic)
**Files:** `src/posting/manychat.py`, `src/main.py` line 265, `.github/workflows/publish.yml` line 50
**What:** ManyChat was removed from the publish flow (`pass  # ManyChat removed`), but the module file, the `MANYCHAT_API_KEY` env var in the workflow, and the import in `__init__` all remain.
**Recommendation:** Delete `src/posting/manychat.py`, remove `MANYCHAT_API_KEY` from the workflow.

---

### L-3 — `_date_label()` uses naive local time
**Status:** OPEN (cosmetic)
**File:** `src/ai/rewriter.py` line 37
**What:** `datetime.datetime.now()` with no timezone — on GitHub Actions (Ubuntu) this is UTC. The label is only "AI NEWS · JUNE 2026" so impact is cosmetic, but the month could theoretically be wrong by a day at UTC midnight.
**Fix:** `datetime.datetime.now(tz=datetime.timezone.utc)`.

---

### L-4 — `alerts.py` stub never sends real alerts
**Status:** OPEN (known gap)
**File:** `src/utils/alerts.py`
**What:** `notify_failure()` only prints to stderr. Pipeline failures are silent unless you check GitHub Actions logs manually.
**Impact:** You won't know a run failed until you notice missing posts.
**Recommendation:** Wire up email or a Slack/Discord webhook here.

---

### L-5 — `.env.example` contains real credentials
**Status:** OPEN (security)
**File:** `.env.example`
**What:** The file contains actual values for `META_APP_ID`, `META_APP_SECRET`, `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN`, `META_IG_BUSINESS_ID`, `GOOGLE_SHEETS_ID`.
**Impact:** If this repo is or ever becomes public, those keys are exposed.
**Recommendation:** Replace all real values with placeholder strings like `your_meta_app_id_here`.

---

### L-6 — `--limit` truncates before scoring (order-dependent)
**Status:** OPEN (design trade-off)
**File:** `src/main.py` line 139
**What:** `fresh = fresh[:args.limit]` takes the first N articles by fetch order (RSS feed order), not by quality. High-quality articles later in the feed never get scored.
**Impact:** With `--limit 100` and typically fewer than 100 fresh articles per 48-hour window, this rarely matters. But if sources return many items, you might miss good ones.
**Recommendation:** Either score all and then limit, or document that `--limit` is for cost control only and set it high enough to cover all expected fresh items.

---

## QA Checklist — Run Before Each Deploy

- [ ] `python -m src.main --smoke` completes with exit 0 and renders 7 non-empty slides
- [ ] `python -m pytest tests/` passes
- [ ] `grep "cron:" .github/workflows/publish.yml` shows a reasonable posting hour (not midnight)
- [ ] `grep "booking_url" src/main.py` shows `cta.get("booking_url"`
- [ ] `grep "booking_url" config/content_rules.yaml` shows `https://`
- [ ] GitHub Secrets include: `META_PAGE_ACCESS_TOKEN`, `META_IG_BUSINESS_ID`, `META_PAGE_ID`, `ANTHROPIC_API_KEY`, `GOOGLE_SHEETS_ID`, `GOOGLE_SERVICE_ACCOUNT_JSON`, `GITHUB_TOKEN`
- [ ] Google Sheets has both `dedup` and `posts` tabs with correct headers
- [ ] Meta Page Access Token expiration date checked (long-lived tokens expire ~60 days)

---

## New Findings

_Add new bugs here as they are discovered._

| Date | ID | Severity | File | Description | Status |
|------|----|----------|------|-------------|--------|
|      |    |          |      |             |        |
