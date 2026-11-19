# Tickets: task graph

> **Superseded.** The approved vertical-slice tickets live in `.scratch/dar-chatbot/issues/` (20 files). This earlier layer-ordered list is kept only for reference.

Source spec: [PRD.md](PRD.md). Status: all `ready-for-agent` unless marked **HITL** (needs the human).

## Graph

```
T1 Scaffold & contracts
 ├─ T2 Wasalt terms check (HITL) ─► T3 Wasalt scraper ─┐
 ├─ T4 DarGlobal scraper (+ manual-save fallback, HITL)─┤
 ├─ T7 LLM gateway ─────────────────────────────────┐  │
 └─ T5 Ingestion (fixture data first) ◄──────────────┼──┘
        └─ T6 Retrieval ──► T8 Agent ──► T9 Verifier + gate + guardrails ──► T10 Chat API
                                                                              ├─ T11 Frontend (mock first)
                                                                              └─ T12 Docker + deploy (HITL) ── M1 thin slice live
T3,T4 ─► T13 Golden set (HITL spot-check) ─► T14 Eval harness + calibration ─► T15 README + submission (HITL)
```

Frontier at start: T1. After T1: T2, T4, T5, T7, T11 (against the contract with a mock). T3 waits on T2.

## Milestones

- **M1, thin slice live (Thu 19 Nov afternoon):** T1-T12 working with whatever data exists. Even a reduced dataset is fine.
- **M2, quality (Thu night to Fri morning):** T13, T14 and threshold calibration done.
- **M3, submit (Fri 20 Nov, with buffer):** T15 done and email sent.

## Tickets

### T1: Scaffold and contracts
Blocked by: none · Blocks: everything
- Repo layout, environment handling (key via env only, `.env.example`, ignore rules), shared settings.
- Define the data-record contract, the chat API contract (request, event stream, verdict) and the procedural rules file.
- Done when: both contracts are written down and validated by a trivial fixture, and the app boots with a health endpoint.

### T2: Wasalt terms and robots check (HITL)
Blocked by: T1 · Blocks: T3
- Read the raw robots.txt, including the stanza naming `anthropic-ai`. Try to read the terms page. Record the findings.
- Done when: a short note says "proceed" or "stop", and the operator has seen it. If the terms explicitly forbid scraping, stop and report. T3 does not start.

### T3: Wasalt scraper (sample)
Blocked by: T2 · Blocks: T5 (real data), T13
- Stratified sample of about 300-500 listings plus a few area pages, from sitemap and page-embedded data. Polite: descriptive User-Agent, about 1 request/second, backoff, no `/search`, no CMS API. Personal data is dropped at parse time.
- Output raw, processed JSON and txt export, each with `scraped_at`.
- Done when: output validates against the contract, spans several cities/types/sale-rent, contains no personal fields, and a rerun is idempotent and resumable.

### T4: DarGlobal scraper (and manual-save fallback)
Blocked by: T1 · Blocks: T5 (real data), T13
- Sitemap-driven, cleaned, deduplicated URL list with utility pages and most blog posts dropped. Playwright, human pace, one page at a time, robots.txt respected. If the challenge appears, stop and do not bypass. Time box about 45 minutes.
- Fallback (HITL): the operator saves the top 30-40 pages from their own browser, and the same parser handles them. The README states which method was used.
- Done when: about 100-150 pages (or 30-40 via fallback) are stored as raw, processed JSON and txt, validated by the contract.

### T5: Ingestion (chunk and index)
Blocked by: T1 (fixtures), real data from T3/T4 for the final run · Blocks: T6
- Structure-based chunking (listing = chunk, heading section = chunk, recursive split for long prose), chunk header, ids and parent ids, metadata. Build the vector index and the keyword index at image build time.
- Done when: the index builds from the processed data with one command, chunk counts and sizes are reported, and no listing is split across chunks.

### T6: Hybrid retrieval and document expansion
Blocked by: T5 · Blocks: T8
- Hybrid search with rank fusion, metadata filters and sort (in code), capped results, and parent-document expansion.
- Done when: known queries return the expected chunks on the fixtures, and filters and sort give correct results on hand-checkable cases.

### T7: LLM gateway
Blocked by: T1 · Blocks: T8
- OpenRouter client, ordered free-model chain, retries with backoff, timeouts, a stub for tests. A probe script lists free models that support tool calling and reports context size. Verify current free-tier limits.
- Done when: the chain advances on simulated failure and rate-limit errors, and the probe's findings are noted in the implementation notes. The primary and fallbacks are chosen.

### T8: Agent graph
Blocked by: T6, T7 · Blocks: T9
- LangGraph agent with the two tools, the step cap, history trimming by token budget, and procedural rules loaded read-only. Evidence is treated as data.
- Done when: simple lookups, filtered questions and follow-ups work against the stub and a real free model within the call budget.

### T9: Verifier, retrieval gate and guardrails
Blocked by: T8 · Blocks: T10
- Retrieval gate (placeholder threshold, calibrated in T14), rule-based verifier with LLM fallback, input and output guardrails, sample-limit wording for numeric answers.
- Done when: unsupported numbers are rejected, unanswerable and off-topic inputs get "I don't know" or a redirect, injection attempts do not change behaviour, and advice requests are declined.

### T10: Chat API
Blocked by: T9 · Blocks: T11 (final wiring), T12
- Streaming endpoint (agent steps, text, sources, verdict), health endpoint with data-as-of date, per-IP rate limit, timeouts, friendly errors.
- Done when: the endpoint satisfies the contract in T1 end-to-end with the stub and a real model.

### T11: Frontend
Blocked by: T1 (builds against a mock), T10 for the final wiring · Blocks: T12
- Chat UI with streaming, source cards, data-as-of badge, starter questions, `localStorage` history and clear button, agent-step trace, mobile layout and error states. Static export.
- Done when: it works against the live API on desktop and mobile widths, and survives a refresh.

### T12: Docker and deploy (HITL)
Blocked by: T10, T11 · Blocks: T15, M1
- Multi-stage image (build UI, then Python runtime with model and index baked in). Deploy to Hugging Face Spaces. The operator provides the account and sets the API key as a secret.
- Done when: the public URL answers a real question, is tested from a second device and mobile, and no secrets are in the repo or image layers.

### T13: Golden dataset (HITL spot-check)
Blocked by: T3, T4 · Blocks: T14
- About 50 questions with expected answers and source chunk IDs or URLs, in the agreed mix (about 20% unanswerable, a few adversarial). The operator spot-checks a subset.
- Done when: the file validates, every answerable question's sources exist in the index, and the operator has reviewed a sample.

### T14: Eval harness and calibration
Blocked by: T10, T13 · Blocks: T15
- Retrieval evals (recall@5, MRR, context precision, context recall) for dense, BM25 and hybrid. Answer evals (faithfulness, correctness, abstention precision/recall, injection resistance), with rule-based checks first and a free-model judge second. JSONL logs. Calibrate the retrieval-gate threshold.
- Done when: a single command produces the results table, hybrid is at least as good as either retriever alone, faithfulness >= 0.85, and unanswerable hallucinations <= 5%. If a bar is missed, the real number is recorded with the reason.

### T15: README and submission (HITL)
Blocked by: T12, T14
- README with an architecture diagram, setup, data refresh commands, scraping method and ethics, eval table, limitations and future work (Arabic, memory). Draft the email.
- Done when: the operator supplies location, packages and notice period, sends the email with repo link and URL, and the URL still works after sending.
