# Implementation Notes

Companion to [PRD.md](PRD.md) and [TICKETS.md](TICKETS.md). These are working notes for whoever (or whatever agent) implements the tickets.

## Working agreements

- **Integration branch:** all work lands on one integration branch. Each ticket is built in its own worktree and branch, and merged back before dependent tickets start. The folder is not yet a git repo, so `git init` is the first action once implementation is approved.
- **Build order:** test-first through the chat endpoint seam (see the PRD). Prefer the highest seam, so tests describe behaviour and not internals.
- **Context pointers over repeated text:** tickets point to the PRD. Don't copy requirements into subagent prompts.
- **Scratch notes** (research, probe results) go outside the repo, and only the durable decisions are copied back into these docs.

## Day plan (today Wed 18 Nov, deadline Fri 20 Nov)

| When | Focus |
|---|---|
| Wed evening | T1 scaffold and contracts. T2 terms check. Start T3 and T4 (the scrapers are the biggest unknown). T7 model probe. |
| Thu morning | Finish scraping (DarGlobal time box about 45 minutes, then fall back). T5 ingestion, T6 retrieval. |
| Thu midday | T8 agent, T9 verifier and gate, T10 API, T11 UI. |
| **Thu afternoon** | **T12: M1 live on Spaces, even with partial data.** |
| Thu night | T13 golden set. T14 evals and calibration. |
| Fri morning | Fix the biggest eval failures. Re-test the URL on another device and a phone. |
| Fri afternoon | T15 README and email, leaving a buffer before the deadline. |

## Decisions to make by testing (not by asking)

- **Embedding model:** compare two or three small local models on recall@5 and MRR over the golden set. Prefer the smallest that is good enough, since the image has to stay light.
- **LLM chain:** probe which `:free` models are currently live, support tool calling, and have enough context. Pick one primary and two or more fallbacks. Record context sizes, because the history budget uses the smallest.
- **Retrieval-gate threshold:** pick it from the score distributions of answerable vs unanswerable golden questions, favouring fewer wrong answers over fewer refusals.
- **Chunk sizes:** start at about 400 tokens with 50 overlap for prose, and adjust only if context recall is poor.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| DarGlobal's Incapsula challenge blocks Playwright | 45-minute time box, no bypass, manual-save fallback of the top 30-40 pages. |
| Wasalt terms forbid scraping | T2 is a hard gate. Stop and tell the operator. |
| Wasalt field names in the embedded JSON are unknown | Inspect one page first and write the parser against real fields. Never guess. |
| Free-model quota is exhausted (verify actual limits) | 2-3 calls per question, a mostly rule-based verifier, a fallback chain, a per-IP rate limit and, if the operator wants, a small account credit. |
| Weak tool-calling on free models | Only two simple tools, a step cap, and a fallback to a fixed retrieve-then-answer path if tool calls keep failing. |
| Cold start or sleeping host | Bake the index and model into the image. Warm the model at startup. The UI shows a "waking up" state. |
| Hallucinated prices | Verifier checks that numbers appear in the evidence. Numeric questions are computed in code. |
| Memory or prompt poisoning | No server memory, no `remember` tool. The rules file is read-only. Evidence beats user claims. |
| Personal data in Wasalt JSON | Drop at parse time and test that none is present in stored files. |
| Image too large for the host | Use a small embedding model, avoid heavy dependencies, and use multi-stage builds. |

## Conventions

- Secrets: environment only. `.env.example` lists the variable names with no values. Check that nothing sensitive is in the image layers.
- Logging: one JSONL line per agent run (question, tool calls, retrieved ids, scores, verdict, model used, latency) with no personal data. Eval runs log the same plus the labels.
- Determinism: eval runs record the model name, temperature and data snapshot date.
- Data freshness: the data-as-of date comes from the processed data, and the health endpoint and UI show it.
- Politeness: the scrapers cache every fetched page and never refetch a page they already have.

## Verification before claiming done

Each ticket's "Done when" is verified by actually running it, and the result is reported honestly, including misses. Before submission, walk through the PRD's success checklist line by line:
1. Open the public URL from a different device, on mobile data if possible.
2. Ask one question of each type: DarGlobal lookup, Wasalt lookup, numeric, comparison, follow-up, unanswerable, injection.
3. Confirm the eval table in the README matches the latest run.
4. Confirm the repo and image contain no secrets.

## Open questions for the operator

- Seams: is the chat endpoint (plus the processed-data contract) the right pair of seams? The PRD proposes this and needs your confirmation.
- Whether to add small credit to the OpenRouter account.
- Hugging Face account and GitHub repo: ready?
- Email details: location, current package, expected package, notice period (needed only at T15, but decide early).
- Issue tracker: none is set up. `/setup-matt-pocock-skills` would let the spec and tickets be published to one.
