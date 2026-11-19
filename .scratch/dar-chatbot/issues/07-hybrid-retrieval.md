# 07: Hybrid retrieval

**What to build:** Exact names/numbers/places and loosely worded questions both find the right sources (vector + BM25 merged with RRF).

**Blocked by:** 04 Ask about Wasalt listings (real data), 05 Ask about DarGlobal projects (real data)

**Mode:** AFK (agent can do alone)

**Status:** done on fixtures + real DarGlobal data (2026-11-19); Wasalt part pending ticket 04

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Fixed exact-term and paraphrase question set returns expected sources via the chat API
- [x] Vector-only misses at least some of them (proves value)

