# Suki AI News — Next steps (resume tomorrow)

Last worked: 2026-05-18 evening.

## Where we are

**Wired and verified end-to-end:**
- Google Sheets storage — service account `suki-news-bot@suki-ai-news.iam.gserviceaccount.com`, sheet `1VtwvAHl6Q5Pi7_LQpz2_Z5TudpDgQH5s4qPp5AesydE`, `dedup` and `posts` tabs auto-created, reads + writes confirmed.
- Meta Graph API — Page Access Token (permanent, 203 chars) live in `.env`, all required scopes present (`pages_manage_posts`, `instagram_content_publish`, etc.), FB Page `1093709560496597` and IG business `17841449173466622` confirmed linked.
- Pipeline code — sources, scorer, rewriter, scheduler, carousel renderer, image hosting, publishers, orchestrator. `python -m src.main --smoke` runs green.

**Still empty in `.env`:**
- `HIGGSFIELD_API_KEY` (+ `HIGGSFIELD_BASE_URL`, `HIGGSFIELD_MODEL`) **or** `ANTHROPIC_API_KEY` — pipeline falls back to StubClient without one.
- `GITHUB_REPO`, `GITHUB_TOKEN` — needed for hosting carousel PNGs at raw.githubusercontent URLs so Meta can fetch them.
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` — optional, reddit source no-ops without them.

## Tomorrow — in this order

1. **Pick one LLM and add its key to `.env`.** Higgsfield if Yali has credits there; otherwise grab an Anthropic key. Run `python -m src.main --dry-run` (no `--smoke`) and confirm the scorer pulls + scores real RSS items. This is the first end-to-end with real fetch + real LLM.
2. **Set up GitHub image hosting.**
   - Create a public GitHub repo (or reuse this one if it ends up on GitHub) with an orphan branch named `published`:
     ```
     git checkout --orphan published
     git rm -rf .
     echo "Suki AI News — published carousel images" > README.md
     git add README.md && git commit -m "init published branch"
     git push origin published
     git checkout main
     ```
   - Generate a fine-grained PAT with `Contents: read+write` on that one repo. Paste into `.env` as `GITHUB_TOKEN`, set `GITHUB_REPO=<owner>/<repo>`.
   - Re-run `--dry-run` and confirm `image urls:` log now shows `https://raw.githubusercontent.com/...` instead of `file://`.
3. **First real post.** Drop both `--smoke` and `--dry-run`. The pipeline will publish a single live carousel to the Suki Systems FB Page + IG. Watch the post in the Meta apps; delete it if it looks off, then iterate on prompt/template.
4. **Set GitHub Actions secrets** mirroring `.env`, then enable the `*/20 * * * *` cron. Pipeline goes hands-off.
5. **Carousel polish** — verify brand fonts (commit `Inter` + `JetBrains Mono` TTFs into `assets/fonts/`), pull true brand colors from suki-systems.com CSS, replace the placeholder palette in `src/carousel/theme.py`.
6. **Smoke row cleanup** — delete the row with `url_hash=smoketest01` from the dedup tab in the Google Sheet (left over from initial connectivity test).

## Open questions / parking lot
- Engagement automation (likes + comments on third-party accounts) — see [growth-automation question](engagement_automation_analysis.md). Short version: not doable via Meta's official API; doing it via unofficial means risks the accounts we just set up.
- **Campaign measurement dashboard** (Supabase + Vercel) — spec'd in `suki-ai-news-pipeline-spec.md` §15. Pulls every paid campaign + organic post via Meta Marketing API / Graph Insights API into Supabase, surfaces via a Vercel Next.js dashboard. Unique value vs Ads Manager: news-attribution view that pivots organic engagement by news score / category. Slots in post-MVP, after the comment auto-reply work.
