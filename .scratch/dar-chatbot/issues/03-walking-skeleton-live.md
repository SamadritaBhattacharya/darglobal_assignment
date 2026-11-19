# 03: Walking skeleton goes live

**What to build:** The skeleton runs in Docker on Hugging Face Spaces with a real free model through the gateway at a public URL. API key is a host secret only.

**Blocked by:** 01 Walking skeleton: ask, get a cited answer (local)

**Mode:** HITL (needs the human)

**Status:** ready-for-agent

**Parent:** docs/PRD.md

**Test rule:** assert outcomes at the module edge only (see docs/ENGINEERING_RULES.md). Red -> Green -> Refactor.

- [ ] Live URL answers the fixture question from a second device
- [ ] Image and repo contain no secrets
