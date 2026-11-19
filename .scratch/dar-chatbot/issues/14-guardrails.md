# 14: Guardrails

**What to build:** Off-topic redirect; injection text treated as data; legal/financial/investment advice declined; non-English gets an English-only message; messages over ~500 chars rejected; matching UI messages.

**Blocked by:** 12 I don't know gate

**Mode:** AFK (agent can do alone)

**Status:** done (2026-11-19); live-model verification waits for the OpenRouter key

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Fixed abusive-input set gets the expected refusal/redirect verdicts
- [x] Normal questions unaffected

