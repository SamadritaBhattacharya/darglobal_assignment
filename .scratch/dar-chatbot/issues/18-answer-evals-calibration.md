# 18: Answer evals and threshold calibration

**What to build:** Faithfulness, correctness, abstention precision/recall, injection resistance (rules first, free-model judge second). Dont-know threshold chosen from score distributions.

**Blocked by:** 13 Verifier: reject unsupported claims, 14 Guardrails, 17 Retrieval evals

**Mode:** AFK (agent can do alone)

**Status:** partly done: merged report exists; gate thresholds not yet recalibrated; free-tier daily quota (50/day) ran out, so no clean full re-run yet

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Faithfulness >= 0.85
- [x] <= 5% hallucinated answers on the unanswerable set
- [ ] Misses recorded honestly with the reason
