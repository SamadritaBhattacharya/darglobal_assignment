# 12: I don't know gate

**What to build:** Weak retrieval means no guess. The visitor sees an I-don't-know state and the verdict is shown in the UI. Threshold is a placeholder until ticket 18.

**Blocked by:** 07 Hybrid retrieval

**Mode:** AFK (agent can do alone)

**Status:** done on real DarGlobal data (2026-11-19). Interim thresholds; recalibrate in ticket 18. Verdict label in UI already exists (ticket 01)

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Off-corpus questions return the dont-know verdict with no invented facts
- [x] In-corpus questions are still answered

