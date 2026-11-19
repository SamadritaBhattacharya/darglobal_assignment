# 08: Filtered and ranked questions

**What to build:** 'Cheapest 3-bedroom in Riyadh' style questions are filtered and sorted in code, capped at ~10 results, and the answer states it covers sampled listings only.

**Blocked by:** 04 Ask about Wasalt listings (real data), 07 Hybrid retrieval

**Mode:** AFK (agent can do alone)

**Status:** done on fixtures (2026-11-19); re-verify on real Wasalt data after ticket 04

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Hand-checkable cases return the correct listing
- [x] Every such answer includes the sample caveat


