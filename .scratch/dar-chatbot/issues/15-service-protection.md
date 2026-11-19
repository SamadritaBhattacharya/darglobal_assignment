# 15: Service protection

**What to build:** Per-IP rate limit (~20 req/min) and request timeouts, with friendly UI messages.

**Blocked by:** 03 Walking skeleton goes live

**Mode:** AFK (agent can do alone)

**Status:** done (2026-11-19); live-model verification waits for the OpenRouter key

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] 21st rapid request returns the rate-limit response
- [x] Slow stubbed model times out cleanly

