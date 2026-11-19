# 09: Multi-step agent and cross-source comparison

**What to build:** LangGraph agent with two tools, capped at ~4 tool steps and 2-3 LLM calls per typical question, compares a DarGlobal project with Wasalt listings; UI shows a searching trace.

**Blocked by:** 07 Hybrid retrieval, 08 Filtered and ranked questions

**Mode:** AFK (agent can do alone)

**Status:** ready-for-agent

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [ ] Comparison question returns citations from both sources
- [ ] A runaway-tool stub run stops at the cap and still answers or declines
