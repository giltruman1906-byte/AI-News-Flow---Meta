# Engagement automation — can we auto-like 100/day + comment ~50/day?

**TL;DR — No, not safely.** Meta's official API does not permit it, and unofficial methods will get the accounts you just set up banned. Below is the why, and what's actually viable.

## What the Meta Graph API allows

For Instagram **Business** accounts (which is what `@suki_systems` is), the API is **read-only on third-party content** and **write-only on your own**:

| Action | API allows? |
|---|---|
| Like another user's IG post | ❌ No endpoint exists |
| Follow another user | ❌ No endpoint exists |
| Comment on another user's post | ❌ No endpoint exists |
| Like a comment on your own IG post | ✅ Yes (`instagram_manage_comments`) |
| Reply to a comment on your own IG post | ✅ Yes |
| Send a DM reply (only if user messaged you first, within 24h) | ✅ Yes (`instagram_manage_messages`) |
| Publish your own carousel / reel / story | ✅ Yes (what this pipeline already does) |

This is intentional. Meta removed third-party engagement endpoints years ago precisely to block automated growth tools.

Facebook Pages API is the same — you can post and reply on your own page, you cannot programmatically like or comment on other people's pages.

## What "automation" tools you see in the market actually do

Things like Jarvee, Combin, Inflact, Path Social, etc. work one of two ways — both prohibited by Meta:

1. **Browser automation** — Selenium / Puppeteer driving a headless Chrome logged into the IG web UI, clicking like/comment buttons. Detected by Meta's behavioral fingerprinting (mouse paths, timing, IP fingerprint, navigation patterns). Detection → action limit → temporary ban → permanent ban. Cycle takes anywhere from days to months depending on how cautious the tool is.

2. **Reverse-engineered private API** — calling IG's internal mobile-app endpoints directly using session tokens scraped from a logged-in app. Used to work well; Meta cracked down hard 2021–2023. Same eventual ban outcome, often faster.

Both also violate the Meta Platform Terms, Section 3 ("Don't use automated means … to access, scrape or collect data from our products"). Getting caught means the **entire Business Portfolio** can be flagged — that's the Page + IG + ad account + every other Page Yali manages.

## Why this is especially risky for *this* project

You just got the Meta app reviewed for `instagram_content_publish`. That review is per-app and per-business. If the account or business portfolio gets flagged for automation:
- The app gets restricted → the news pipeline stops posting.
- The IG/FB account itself can be shadowbanned (your posts stop showing in feeds) or banned outright.
- You'd be back to square one with no clear appeals path, and Meta is famously unresponsive once a business is flagged.

The pipeline we just built is the asset. Risking its host account for ~100 likes/day is a bad trade.

## What actually moves the needle on growth (and is allowed)

Pick from these, all official, all sustainable:

1. **Meta Ads** — even $5/day on a well-targeted ad set will beat 100 likes/day for follower growth on a brand new account. Set up via Ads Manager with the Suki Page + IG. The Graph API supports programmatic ad creation if you want to auto-generate creative from the news posts.
2. **Reply automation on incoming engagement** — when someone comments on a Suki post, the API lets you auto-reply. We could add a step: every cron cycle, fetch new comments on your last N posts, run them through Claude for an on-brand reply, post it. This builds reciprocal engagement without touching anyone else's account.
3. **DM auto-reply** — same idea for DMs (24h window after they message you first). Useful for "Book a call" intent capture.
4. **Cross-posting to LinkedIn / Twitter / Threads** — those platforms' APIs are more permissive. Threads in particular still allows third-party likes via the Threads API as of late 2025; worth checking if a unified posting layer is interesting later.
5. **Content quality + frequency** — what you're already doing. 6–8 high-signal posts/day from this pipeline will outperform any like-bot strategy for SMB-targeted reach. Algorithm rewards consistent posting + saves + shares far more than reciprocal likes.
6. **Manual seeding (the boring answer)** — 15 minutes/day of Yali or you genuinely engaging with 10–15 target SMB accounts (read their stuff, leave one substantive comment). Doesn't scale, but moves real attention in the first 90 days.

## If you still want to explore the bot path anyway

Don't do it from the Suki accounts. The pattern that minimises blast radius:

1. Create a separate "growth" IG account, not linked to the Suki business portfolio at all.
2. Use that account with a tool like [InstaPy](https://github.com/InstaPy/InstaPy) or similar, on a residential proxy, at very conservative limits (≤30 likes/day, no comments). It will *still* eventually get banned, but it won't take the main account with it.
3. The growth account points back to `@suki_systems` in its bio.

I'd advise against even this — the EV is poor and the ethics are sketchy (you're spamming SMBs from a sockpuppet on a project whose pitch is "AI that ships"). But if you're going to do it, isolate.

## Recommendation

Skip the like/comment automation entirely. The two things in this list that *would* be high-leverage and we *can* build with the existing stack:

- **Auto-reply to comments on Suki posts** using Claude in the brand voice (~30 min of work in this codebase, would extend the existing cron cycle).
- **Auto-generated Meta Ad creative** from each high-scoring news item, posted as a $3–5/day boost (~2 hours of work, requires Ads API permissions on top of what we have).

Want either of these on the roadmap for next week?
