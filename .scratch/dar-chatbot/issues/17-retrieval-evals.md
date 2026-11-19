# 17: Retrieval evals

**What to build:** One command reports recall@5, MRR, context precision and context recall for dense-only, BM25-only and hybrid.

**Blocked by:** 07 Hybrid retrieval, 16 Golden dataset

**Mode:** AFK (agent can do alone)

**Status:** done, but one bar NOT met: hybrid did not beat vector-only on the 21 retrieval questions (see evals/results/retrieval.md)

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [x] Report exists
- [ ] Hybrid >= either retriever alone
- [ ] Figures copied to README
