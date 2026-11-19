# 16: Golden dataset

**What to build:** ~50 questions with expected answers and source ids/URLs: DarGlobal ~10, Wasalt ~8, filtered ~8, comparison ~5, follow-up ~5, unanswerable ~10, adversarial ~4. Human spot-checks a sample.

**Blocked by:** 04 Ask about Wasalt listings (real data), 05 Ask about DarGlobal projects (real data)

**Mode:** HITL (needs the human)

**Status:** built (48 questions, machine-checked against the data); human spot-check still pending

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] File validates
- [x] Every answerable question's sources exist in the data
- [ ] Human signed off a sample
