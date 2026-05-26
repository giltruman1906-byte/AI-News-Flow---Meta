# Deploy / Meta setup runbook

See spec §7 for the full walkthrough. Short version:

## 1. Meta app prerequisites
- A Meta developer app with the **Instagram** product added
- Suki Systems IG account = Business or Creator (not Personal)
- Suki Systems FB Page linked to that IG account

## 2. Permissions required
- FB: `pages_manage_posts`, `pages_read_engagement`
- IG: `instagram_basic`, `instagram_content_publish`, `pages_show_list`
- App review needed for `instagram_content_publish` + `pages_manage_posts` (1-2 weeks)

## 3. Get a long-lived Page Access Token
```bash
# Short-lived user token from Graph API Explorer:
# https://developers.facebook.com/tools/explorer/

# Long-lived user token:
curl "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=$META_APP_ID&client_secret=$META_APP_SECRET&fb_exchange_token=$SHORT_TOKEN"

# Page access token (the one we actually use):
curl "https://graph.facebook.com/v21.0/me/accounts?access_token=$LONG_USER_TOKEN"

# IG Business account id:
curl "https://graph.facebook.com/v21.0/$PAGE_ID?fields=instagram_business_account&access_token=$PAGE_TOKEN"
```

## 4. Google Sheets
1. Create sheet `Suki AI News — Pipeline State`
2. Two tabs:
   - `dedup` — columns: `url_hash | url | title | source | source_tier | seen_at | score | status`
   - `posts` — columns: `posted_at_utc | posted_at_ny | url | title | score | fb_post_id | ig_post_id | ig_carousel_id`
3. Create a GCP service account, download JSON, share the sheet with the service account email (Editor)
4. Store the full JSON as the `GOOGLE_SERVICE_ACCOUNT_JSON` secret

## 5. GitHub published branch
- Create an orphan branch `published`:
  ```bash
  git checkout --orphan published
  git rm -rf .
  echo "Image hosting branch for suki-ai-news." > README.md
  git add README.md && git commit -m "init published branch"
  git push -u origin published
  ```
- The workflow needs `contents: write` (already set in `publish.yml`).

## 6. GitHub Actions secrets
Set all variables from `.env.example` as repo secrets. `GITHUB_TOKEN` is provided automatically by Actions.

## 7. Higgsfield
- Confirm API endpoint, auth header, model name, JSON-mode support
- Add `HIGGSFIELD_API_KEY`, `HIGGSFIELD_BASE_URL`, `HIGGSFIELD_MODEL` to secrets
- Anthropic key is the fallback; set `ANTHROPIC_API_KEY` too
