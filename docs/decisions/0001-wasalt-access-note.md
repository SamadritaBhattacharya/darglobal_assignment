# 0001: Wasalt access note (ticket 02 gate)

Status: **DECIDED 2026-11-19: proceed.** Small attributed non-commercial sample; repo stays **private** (shared with DarGlobal at submission); free OpenRouter models only. Checked 2026-11-19 with a few single, polite requests.

## What Wasalt says
**robots.txt (wasalt.sa/robots.txt):** all bots may crawl `/` except `/search` and `/cdn-cgi/rum`. A separate stanza for `ChatGPT-User`, `anthropic-ai` and `PerplexityBot` only adds `Allow: /search`. Sitemaps are listed. Nothing blocks listing pages.

**AI policy (wasalt.sa/llms.txt, last updated 2025-07-06):**
- Allowed: LLM use, summarisation, recommending properties, answering questions using Wasalt content, and "data extraction only for public listing content".
- Limits: crawl rate "moderate, avoid high-frequency crawling"; **no commercial use**; **no resale, redistribution or commercial republishing**; no contact details/phone/WhatsApp extraction; no scraping of internal search results or maps; no gated content.
- Requires attribution ("Source: Wasalt.sa") and says LLMs "should not rely on cached or stored content" and must send users to the live site for real-time prices and availability.

**Terms and conditions page:** not found at the three URLs tried (404). Unverified; a human should check the site footer.

## What this means for the plan
| Plan item | Fit | Action |
|---|---|---|
| Public listing pages, ~1 req/s, small stratified sample (~300-500) | Fits "moderate" crawl and "public listing content" | Proceed, keep delay >= 1s, cache pages |
| No `/search`, no CMS API, no contact data | Matches policy | Already in plan |
| Drop owner/agent personal data | Matches policy | Already in plan (+ PII redaction) |
| Attribution | Required | Every Wasalt answer and source card shows "Source: Wasalt.sa" with the listing link |
| Stored snapshot instead of live data | **Tension** with "should not rely on cached content" | Keep it a small, clearly labelled snapshot with a "data as of" date, and tell users to check wasalt.sa for live prices |
| Committing scraped data to a public repo | **Tension** with "no redistribution" | Do not publish raw Wasalt pages. Decide: (a) keep the repo private and share it with DarGlobal, or (b) commit only the small processed sample with attribution, or (c) commit the scraper and a few sample records only |
| Non-commercial | Fits | A job assessment demo, not a product; state this in the README |

## Decision needed from you
1. Proceed with the small, attributed, non-commercial sample? (recommended: yes)
2. Repo visibility: private, or public with only a minimal sample? (recommended: private, shared with DarGlobal at submission)
3. Check the live site footer for a terms page I could not find.

Until you answer, ticket 04 (Wasalt scraper) stays blocked and nothing is scraped from Wasalt.
