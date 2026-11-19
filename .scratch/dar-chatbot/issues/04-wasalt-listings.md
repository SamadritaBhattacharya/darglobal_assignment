# 04: Ask about Wasalt listings (real data)

**What to build:** A polite stratified sample (~300-500 listings) becomes raw, processed JSON and txt with personal data dropped, then one chunk per listing, so listing questions are answered with citations.

**Blocked by:** 01 Walking skeleton: ask, get a cited answer (local), 02 Wasalt terms and robots gate

**Mode:** AFK (agent can do alone)

**Status:** reader done and verified on 2 real listings; needs ~30 saved pages for a useful sample

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [ ] Data contract passes: several cities and types, sale and rent, no personal fields, every record has url and scraped_at
- [x] Five hand-picked listing questions return the right facts and URLs through the chat API
- [ ] Scraper is polite (descriptive User-Agent, ~1 req/s, backoff, no /search, no CMS API), cached and resumable

