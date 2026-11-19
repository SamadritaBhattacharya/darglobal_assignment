# Technical Specification

Source of intent: [PRD.md](PRD.md). Rules: [ENGINEERING_RULES.md](ENGINEERING_RULES.md). Goals: [GOALS.md](GOALS.md).

## 1. System overview
Offline scrape -> processed JSON (+ txt export) -> build-time index -> runtime agent -> verifier -> streamed answer. One container serves a FastAPI API and the static Next.js UI on one port.

```
scrapers (offline) -> data/raw -> data/processed/*.json -> data/export/*.txt
                                      |
                              ingest (build time)
                                      v
 Browser (Next.js static) -> POST /api/chat -> app: guardrails -> agent -> verifier
                                                   |         |
                                          Retriever port   LLM port
                                          (Chroma + BM25)  (OpenRouter chain)
```

## 2. Stack
Python 3.11, FastAPI, pydantic, rank-bm25, Chroma, LangGraph/LangChain (agent, from ticket 9), local embedding model (chosen by test), OpenRouter `:free` models, Next.js static export, Docker, Hugging Face Spaces.

## 3. Package layout (backend)
`dar.domain` (models, ports, PII, verdicts) / `dar.app` (use-cases) / `dar.adapters` (retrieval, llm) / `dar.api` (HTTP) / `dar.main` (composition root) / `dar.settings`.

## 4. Data contract (processed record)
Required: `id`, `source` (`darglobal` | `wasalt`), `url`, `title`, `section`, `text`, `scraped_at` (ISO 8601). Optional listing fields (Wasalt): `city`, `district`, `property_type`, `listing_kind` (`sale` | `rent`), `price`, `currency`, `area_sqm`, `bedrooms`. Any PII pattern in any field invalidates the record.

## 5. Chunking
Wasalt: one readable chunk per listing, filter fields kept as metadata. DarGlobal: one chunk per heading section; long prose split recursively (~400 tokens, 50 overlap). Every chunk text begins `Source | Title | Section`. Chunks carry `doc_id` and `parent_id`.

## 6. Retrieval
Hybrid: dense (Chroma) + BM25 over the same chunks, merged with Reciprocal Rank Fusion, top 5-10 each. Metadata filters and sort applied in code; results capped ~10. (Ticket 1 starts with BM25 only behind the `Retriever` port.)

**Interim gate values (measured 2026-11-19 on real DarGlobal data, recalibrated in ticket 18):** a chunk is admitted if its cosine distance <= 0.68, or it contains >= 75% of the query's content words. On-topic best distances were 0.22-0.62; off-topic 0.71-0.86. **Known trade-off:** weakly worded paraphrases near 0.70 (e.g. "inexpensive flat close to the ocean") are refused. This is deliberate: precision over recall, because a wrong confident answer is worse than "I don't know".

## 7. Chat API contract
`POST /api/chat` body: `{ "message": str (<=500 chars), "history": [ {"role": "user"|"assistant", "content": str} ] }`.
Response: `text/event-stream` of JSON events:
- `{"type":"step","text":str}` progress notices
- `{"type":"token","text":str}` answer text
- `{"type":"sources","sources":[{"n":int,"title":str,"url":str}]}`
- `{"type":"done","verdict":"answered"|"partial"|"dont_know"|"refused"|"error"}`
Errors use a final `done` with verdict `error` and a friendly message token, never a stack trace.
`GET /api/health` -> `{ "status":"ok","data_as_of": ISO date | null }`.

## 8. Agent (ticket 9)
LangGraph, two tools: hybrid search (with filters/sort) and get-document. Cap ~4 tool steps, target 2-3 LLM calls per typical question. History trimmed oldest-first by token budget for the smallest context window in the model chain. No server memory.

## 9. "I don't know" and verification
Layer 1 retrieval gate (threshold calibrated in ticket 18). Layer 2 prompt requires numbered citations. Layer 3 verifier (mostly rule-based): numbers, names and prices in the answer must appear in retrieved text, else downgrade to `partial` or `dont_know`.

**Verifier limits (known):** numbers and capitalised names are checked against *all* retrieved evidence, not per cited source, so a real number attached to the wrong project can pass. It also cannot catch wrong claims that use no numbers or names. The LLM-judge evals (ticket 18) measure what remains. Written numbers ("two", "1 million") are not checked, and "1M" vs "1,000,000" may cause an over-cautious partial answer.

## 10. LLM gateway
Ordered `:free` model chain, retries with backoff, per-model timeout, typed failure (`LLMUnavailable`) after the chain is exhausted. Verify live model list and free-tier limits at build time (unverified assumption: ~20 req/min, ~50/day without credit).

## 11. Guardrails
English-only, 500-char cap, off-topic redirect, injection treated as data, no legal/financial/investment advice, system prompt never revealed, per-IP rate limit (~20/min), timeouts.

## 12. Privacy
See ENGINEERING_RULES section 4: ephemeral in-memory vault redaction, nothing personal stored, logs redacted.

## 13. Evals
Golden set (~50) in `evals/golden.jsonl`. Retrieval: recall@5, MRR, context precision/recall for dense, BM25, hybrid. Answers: faithfulness (>= 0.85), correctness, abstention precision/recall, injection resistance (rules first, free-model judge second). Hallucinated answers on unanswerable <= 5%.

## 14. Deployment
Multi-stage Dockerfile: build UI, then Python runtime with model and index baked in. Hugging Face Spaces (Docker). `OPENROUTER_API_KEY` as a host secret.

## 15. Known risks / unverified
Wasalt terms; DarGlobal Incapsula; free-model limits and tool-calling support; Wasalt embedded-JSON field names. Each is resolved by the ticket that touches it.
