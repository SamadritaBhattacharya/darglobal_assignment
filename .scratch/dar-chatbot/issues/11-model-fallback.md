# 11: Model fallback and resilience

**What to build:** If the primary free model is rate-limited or fails, the next in the chain answers; if all fail the visitor sees a friendly error. Probe of live free models with tool-calling support is recorded.

**Blocked by:** 03 Walking skeleton goes live

**Mode:** AFK (agent can do alone)

**Status:** done (2026-11-19); live-model verification waits for the OpenRouter key

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Stubbed primary failure still yields an answer
- [x] Stubbed total failure yields the friendly error shape and the UI renders it

