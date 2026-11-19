# 06: Real data goes live

**What to build:** The deployed app serves the real index and shows a data-as-of badge; the health endpoint reports the same date.

**Blocked by:** 03 Walking skeleton goes live, 04 Ask about Wasalt listings (real data), 05 Ask about DarGlobal projects (real data)

**Mode:** HITL (needs the human)

**Status:** ready-for-agent

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [ ] Live: a real DarGlobal and a real Wasalt question both return cited answers
- [ ] Badge date matches the health endpoint
