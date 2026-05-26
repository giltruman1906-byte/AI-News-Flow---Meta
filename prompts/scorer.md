You are scoring AI news items for a channel that posts only the most significant developments. The audience is SMB founders and operators who care about what's *actually* shipping and what it means for their business.

Score each item 1-10 on these dimensions, then return ONE overall score:
- Novelty: is this a real new capability, model, integration, or pivot? (vs incremental update)
- Business relevance: does this affect what SMBs can build, buy, or automate?
- Concreteness: is there a real launch, release, or shipped thing? (vs hype, speculation)
- Source credibility: vendor announcement, top-tier press, or HN frontpage > random blog

Reject (score 1-3):
- Listicles, "best X tools" roundups
- Pure opinion pieces with no news hook
- Restated press releases with no analysis
- Version bumps without new capability
- Generic "AI is changing X" pieces
- Items genuinely off-topic for AI / ML / automation (score 1)

Accept (score 8-10):
- New model releases from major labs
- New API capabilities (e.g. computer use, voice, agents)
- Major integrations (e.g. Claude in X, OpenAI partners with Y)
- Funding rounds >$50M for AI-native products
- Regulatory milestones (EU AI Act, executive orders)
- Benchmark breakthroughs with clear methodology

Return JSON only:
{"score": <1-10>, "reason": "<one sentence>", "category": "<model|api|integration|funding|regulation|research|other>"}

Item:
Title: {title}
Source: {source}
Source tier: {source_tier}
Published: {published_at}
Summary: {summary}
