# 02: Wasalt terms and robots gate

**What to build:** A recorded proceed/stop decision from the raw robots.txt (incl. the anthropic-ai stanza) and the terms page. If scraping is forbidden, ticket 4 stops and the human decides.

**Blocked by:** None (can start immediately)

**Mode:** HITL (needs the human)

**Status:** done (2026-11-19): proceed with a small attributed sample; Cloudflare check means pages are saved by hand

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Raw robots.txt and terms findings recorded in a short decision note
- [x] Human has read the note and said proceed or stop

