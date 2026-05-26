# Suki AI News

Always-on AI news channel for Suki Systems' Instagram + Facebook. Every ~20 min: pull from curated sources, score for insight, publish high-signal items as a 5-slide branded carousel.

See `suki-ai-news-pipeline-spec.md` (project root, one level up) for full spec.

## Stack
- Python 3.11
- GitHub Actions cron (every 20 min)
- Google Sheets (dedup + post log) — sole storage
- LLM: Higgsfield (primary) → Anthropic Claude Haiku (fallback)
- Images: PIL composition, hosted via GitHub raw URLs on a `published/` branch
- Publishing: Meta Graph API (FB Page + IG Business)

## Local setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in
python -m src.main --dry-run
```

## Repo layout
See spec §6.

## Decisions deviating from the spec
- **Sheets-only storage** (no SQLite/Turso). Spec §4.2 dedup lives in the `dedup` tab.
- **Higgsfield** in place of Gemini as the primary LLM (existing credits).
- **GitHub raw URLs** for image hosting in place of Cloudinary.
- **No Telegram approval gate.** Score gate alone decides publishing.
- Rewriter prompt: "1 emoji max in hook, none elsewhere" (resolves spec §4.3 contradiction).
- IG publish polls container `status_code` until `FINISHED` (no fixed sleep).
