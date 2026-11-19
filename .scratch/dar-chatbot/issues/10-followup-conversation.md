# 10: Follow-up conversation

**What to build:** Follow-ups like 'what about its price?' work. Browser keeps history (localStorage, clear button) and sends the last N turns trimmed by token budget for the smallest context window in the model chain.

**Blocked by:** 09 Multi-step agent and cross-source comparison

**Mode:** AFK (agent can do alone)

**Status:** done on fixtures (2026-11-19); re-verify on real Wasalt data after ticket 04

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Two-turn conversation resolves the reference to the right source
- [x] Refresh keeps history; clear empties it
- [x] Over-long history still succeeds


