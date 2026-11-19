# 01: Walking skeleton: ask, get a cited answer (local)

**What to build:** A visitor types a question in a minimal chat page, the API retrieves from a tiny fixture data set (data -> API -> UI), and the answer streams back with a citation. The LLM is a scripted stub at the network boundary.

**Blocked by:** None (can start immediately)

**Mode:** AFK (agent can do alone)

**Status:** done (2026-11-19)

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Known fixture question returns the expected fact and the right source URL through the chat API
- [x] Unknown question returns a non-empty reply without crashing
- [x] Minimal UI shows the streamed answer and source link
- [x] Architecture test and PII-redaction tests are green

