# 13: Verifier: reject unsupported claims

**What to build:** Mandatory final check. A price/area/name not present in retrieved text turns the reply into a hedged partial answer or I-don't-know, and says what is missing.

**Blocked by:** 09 Multi-step agent and cross-source comparison, 12 I don't know gate

**Mode:** AFK (agent can do alone)

**Status:** done on fixtures (2026-11-19); re-verify on real Wasalt data after ticket 04

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Stub that fabricates a price is caught; the user never sees it
- [x] Grounded answer passes unchanged


