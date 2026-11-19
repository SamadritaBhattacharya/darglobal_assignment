# PRD: DarGlobal & Wasalt Real-Estate Chatbot

Status: draft for confirmation · Deadline: Fri 20 Nov 2026 · Live URL target: Thu 19 Nov afternoon

## Destination: what "done" looks like

A recruiter at DarGlobal opens a public URL on any device, with no setup, and chats with a real-estate assistant. They ask about DarGlobal projects and Wasalt listings in English. They get fast, streamed answers with clickable source citations. When the data doesn't support an answer, the bot says it doesn't know and does not guess. Asking it to ignore its rules, give investment advice, or talk about unrelated things gets a polite refusal. The repo shows a clean scrape -> store -> index -> agent -> eval pipeline, and the README shows measured results.

### Success criteria (all must hold to submit)

**Delivery**
- [ ] A public URL (Hugging Face Spaces, Docker) loads the chat UI and answers questions, tested from a second device and a mobile browser.
- [ ] One `docker build` plus `docker run` (with `OPENROUTER_API_KEY` supplied via environment) reproduces the app locally. No secrets in the repo or image layers.
- [ ] Cold start to first usable page is acceptable (index and embedding model are baked into the image, no scraping or index building at runtime).
- [ ] The submission email contains: location, current package, expected package, notice period, repo link, README and working URL.

**Data**
- [ ] DarGlobal: about 100-150 high-value pages (projects, property pages, one-of-one, partners, rayana/amaya/trump-plaza, about/FAQ, 10-15 press/insights items). Blog bulk and utility pages excluded. The method used (Playwright or manual save) is stated in the README.
- [ ] Wasalt: a stratified sample of about 300-500 listings (spread across city, property type, sale vs rent) plus a few area/category pages.
- [ ] No owner/agent personal data (names, licence numbers, contact details) is stored anywhere.
- [ ] Every record carries `source`, `url`, `title`, `scraped_at`. The UI shows a "data as of" date.
- [ ] Raw pages, processed JSON and a readable txt export are all committed. The app never scrapes at runtime.

**Behaviour**
- [ ] Answers include numbered citations that link to the source URLs.
- [ ] Numeric and ranking questions ("cheapest 3-bed in Riyadh") are computed by filtering and sorting in code, and the answer says it covers the sampled listings only.
- [ ] Follow-up questions ("what about its price?") resolve correctly from the recent chat history.
- [ ] Out-of-scope, unanswerable and unsupported questions get "I don't know" (or a partial answer that says what is missing).
- [ ] Prompt-injection and rule-bypass attempts do not change behaviour. The system prompt is not revealed.
- [ ] If the primary free model fails or is rate-limited, the next model in the chain is used and the user still gets an answer or a friendly error.

**Quality bars (measured on the golden set, reported in the README)**
- [ ] Faithfulness >= 0.85.
- [ ] Hallucinated answers on the unanswerable subset <= 5%.
- [ ] Hybrid retrieval is at least as good as dense-only and BM25-only on recall@5 and MRR.
- [ ] Context precision and context recall are reported, and the retrieval-gate threshold is calibrated from them.
- [ ] Abstention precision/recall, correctness and injection resistance are reported.

The quality bars are targets. If a bar is missed, the README reports the real number honestly and says why.

## Problem Statement

A recruiter reviewing a junior applied-AI candidate wants proof they can ship an end-to-end AI product. They need a live chatbot, grounded in real DarGlobal and Wasalt data, that answers accurately and admits when it doesn't know. A code dump with no URL, or a chatbot that confidently invents prices and project details, fails that test. Free LLMs add reliability risks: rate limits, models disappearing, and weak tool-calling.

## Solution

A deployed web chatbot. The data is scraped offline, stored as files, indexed into a hybrid (vector + keyword) search, and queried by a bounded LangGraph agent through two search tools. A mandatory verifier checks every answer against the retrieved evidence before it reaches the user. A golden dataset and an eval harness measure the quality and calibrate the "I don't know" threshold. A Next.js chat UI is served by the same container as the API.

## User Stories

*Visitor / recruiter*
1. As a recruiter, I want to open one public URL and start chatting, so that I can evaluate the work without setup.
2. As a visitor, I want suggested starter questions, so that I know what the bot can answer.
3. As a visitor, I want answers to stream as they are written, so that the app feels fast.
4. As a visitor, I want each claim to have a numbered citation linking to the source page, so that I can verify it.
5. As a visitor, I want to see a short "searching DarGlobal / Wasalt…" trace, so that I understand what the assistant is doing.
6. As a visitor, I want to ask about a DarGlobal project's location, amenities, unit types and status, so that I can learn about it.
7. As a visitor, I want to ask about Wasalt listings by city, type, price and bedrooms, so that I can explore the market.
8. As a visitor, I want questions like "cheapest 3-bedroom in Riyadh" answered correctly, so that I can rely on numbers.
9. As a visitor, I want such answers to tell me they are based on a sample of listings, so that I don't mistake them for site-wide facts.
10. As a visitor, I want to compare a DarGlobal project with Wasalt listings in an area, so that I get a cross-source view.
11. As a visitor, I want follow-up questions to work ("what about its price?"), so that the conversation feels natural.
12. As a visitor, I want the bot to say "I don't know" when the data doesn't cover my question, so that I'm not misled.
13. As a visitor, I want partial answers to say clearly what is missing, so that I know what to look up elsewhere.
14. As a visitor, I want off-topic questions redirected politely, so that the bot stays useful and safe.
15. As a visitor, I want the bot not to give legal, financial or investment advice, so that I am not misled on high-stakes decisions.
16. As a visitor, I want to see a "data as of <date>" badge, so that I know prices are a snapshot.
17. As a visitor, I want my chat history to survive a page refresh, so that I don't lose context.
18. As a visitor, I want a "clear chat" button, so that I control what is stored in my browser.
19. As a visitor, I want a usable mobile layout, so that I can test from my phone.
20. As a visitor, I want friendly error messages when the service is busy, so that I'm not left with a blank screen.
21. As a visitor, I want a clear message if I write in a language other than English, so that I know English is supported.
22. As a visitor, I want my messages never stored on the server, so that my privacy is respected.

*Recruiter reviewing the repo*
23. As a reviewer, I want committed raw, processed and txt data, so that I can inspect scraping quality.
24. As a reviewer, I want a README with an architecture diagram, so that I understand the system quickly.
25. As a reviewer, I want measured eval results in the README, so that quality claims are evidence-based.
26. As a reviewer, I want to see why hybrid retrieval was chosen via a retriever comparison, so that I can judge the engineering.
27. As a reviewer, I want a golden dataset in the repo, so that I can re-run the evals.
28. As a reviewer, I want one command to rebuild the data and another to rebuild the index, so that freshness is handled.
29. As a reviewer, I want the README to state how DarGlobal was scraped (Playwright or manual save), so that the method is transparent.
30. As a reviewer, I want known limitations (sample size, snapshot, English only, free-model limits, Arabic as future work), so that the author shows self-awareness.

*Operator (the candidate)*
31. As the operator, I want the API key in an environment variable only, so that it is never committed.
32. As the operator, I want automatic fallback across several free models, so that the demo survives a rate limit.
33. As the operator, I want per-IP rate limiting and request timeouts, so that a reviewer or bot can't burn my quota.
34. As the operator, I want the scraper to respect robots.txt, use a descriptive User-Agent, and stop on a block, so that I behave ethically.
35. As the operator, I want to stop and report if Wasalt's terms forbid scraping, so that I avoid legal risk.
36. As the operator, I want personal data dropped at scrape time, so that it never enters storage.
37. As the operator, I want JSONL logs of agent runs and eval runs, so that I can debug failures.
38. As the operator, I want the retrieval-gate threshold calibrated from the golden set, so that it isn't a guess.
39. As the operator, I want a thin end-to-end version deployed early, so that deployment risk is cleared first.
40. As the operator, I want a clear cut order when time is short, so that I protect the essentials.

## Implementation Decisions

**Architecture**
- Single deployable: a Python API (FastAPI) that also serves the statically exported Next.js UI. One container, one port, one public URL. The target host is Hugging Face Spaces with the Docker runtime.
- Offline stages (run by the operator, outputs committed): scrape -> processed JSON -> txt export. Build-time stage: ingest -> index. Runtime stages: agent -> verifier -> stream.
- The app never scrapes at runtime. The index and embedding model are baked into the image.

**Data pipeline**
- Three data layers: raw pages, processed structured records, and a readable txt export. RAG is built from the processed records.
- A common record contract: `source` (darglobal or wasalt), `url`, `title`, `section`, `text`, `scraped_at`, plus source-specific structured fields. Wasalt listings add city, district, property type, sale/rent, price (with currency), area, bedrooms and features.
- Wasalt: before scraping, read the raw robots.txt (including the stanza naming `anthropic-ai`) and try the terms page. If the terms explicitly forbid scraping, stop and report. Otherwise take a stratified sample via the page-embedded JSON in plain HTTP requests, using a descriptive User-Agent, about 1 request/second, backoff on 403/429, skipping `/search` and not using the CMS API. Owner/agent personal fields are discarded at parse time.
- DarGlobal: sitemap-driven URL list, cleaned and deduplicated (mixed case, entities, duplicate slugs, utility pages dropped). Playwright at human pace, one page at a time, respecting robots.txt. If the Incapsula challenge appears, stop and do not bypass. The time box is about 45 minutes, then the fallback: the operator saves key pages from their own browser, parsed by the same pipeline (top 30-40 pages first).
- Source scope: projects, property pages, one-of-one, partners, rayana/amaya/trump-plaza, info pages (about, FAQ), 10-15 press/insights items. Most blog posts are excluded.

**Chunking**
- Wasalt listing: one chunk per listing, rendered as a short readable block. Filterable fields go in vector-store metadata.
- DarGlobal: one chunk per heading section. Long prose is split recursively (about 400 tokens, 50 overlap).
- Every chunk starts with `Source | Page title | Section`. Chunks have `doc_id` and `parent_id`. The parent is the full page or section, enabling small-to-big expansion.

**Retrieval**
- Hybrid: dense vectors in Chroma plus a BM25 index over the same chunks, merged with Reciprocal Rank Fusion. Top 5-10 from each side.
- Filters (source, city, district, type, sale/rent, price range, bedrooms) and sort apply on structured metadata, in code. Results are capped at about 10.
- The embedding model is local and baked into the image. It is chosen by testing recall on the golden set.

**Agent (LangGraph, free-roaming but bounded)**
- Two tools: a hybrid search tool with optional filters and sort, and a get-document tool that returns the parent page or section.
- Hard cap of about 4 tool steps. Target 2-3 LLM calls per typical question to protect free-tier quotas.
- Comparisons across sources are done by the model from retrieved evidence. There is no separate compare tool.
- No `remember` tool and no server-side memory.

**LLM gateway**
- OpenRouter, `:free` models only, with an ordered fallback chain, retries with backoff, and per-model timeouts. At build time, probe which free models support tool calling and sufficient context, and pick a primary and fallbacks.
- Free-tier limits (from memory: roughly 20 requests/minute and about 50/day without credits) must be verified at build time. Adding about $10 credit to the account raises the daily limit and is the operator's decision.

**Memory (mapped to the three types)**
- Procedural: a version-controlled, human-authored rules file (behaviour, format, "when unsure say I don't know"), read-only to the agent.
- Semantic: the Chroma knowledge base.
- Episodic: the current conversation, kept in browser `localStorage` and sent as the last N turns with each request. History is trimmed oldest-first by token budget sized for the smallest context window in the model chain. There is no summarisation (it would cost extra LLM calls).
- Retrieved evidence always wins over user claims. User text and retrieved text are treated as data, never as instructions.

**"I don't know" and verification**
- Layer 1, retrieval gate: if the best hybrid score is below a threshold, answer "I don't know" without calling the answer model. The threshold is calibrated on the golden set.
- Layer 2, prompt rule: every claim needs a numbered citation. Partial support gets a partial answer plus a statement of what is missing.
- Layer 3, verifier: a non-skippable final step, mostly rule-based (citations exist, numbers/names/prices appear in the retrieved text), using the LLM only when unclear. A failure turns the reply into a hedged answer or "I don't know".

**Guardrails**
- Input: English only, off-topic redirect, injection treated as data, no legal/financial/investment advice, message cap about 500 characters.
- Output: citations required, no facts or prices absent from evidence, "data snapshot as of <date>", system prompt not revealed.
- Service: per-IP rate limit (about 20 requests/minute), request timeouts, friendly errors, model fallback.

**API contract**
- One chat endpoint takes the latest message plus the last N turns and streams events: agent-step notices, answer text chunks, a final sources list, and a verdict (answered, partial, or don't-know).
- A health endpoint reports readiness and the data-as-of date.

**UI**
- Next.js static export: streamed chat, clickable source cards, a "data as of" badge, starter questions, `localStorage` history with a clear button, an agent-step trace, a mobile layout, and friendly error states.

**Golden set and evals**
- About 50 questions with expected answers and source chunk IDs/URLs, drafted from stored data and spot-checked by the operator. The mix is DarGlobal lookups (~10), Wasalt lookups (~8), filtered/numeric (~8), cross-source comparison (~5), follow-ups needing history (~5), unanswerable/out-of-scope (~10) and adversarial/injection (~4).
- Retrieval metrics: recall@5, MRR, context precision and context recall for dense, BM25 and hybrid.
- Answer metrics: faithfulness, correctness, abstention precision/recall and injection resistance. Rule-based checks run first, then a free-model judge for the rest. Free judges are noisy, so scores are indicative.
- Run logs are written as JSONL. A results table goes in the README.

**Seams (proposed, to confirm)**
- Primary seam: the chat endpoint, with the LLM gateway replaceable by a stub for deterministic runs. Almost all behaviour (retrieval, agent, verifier, guardrails, streaming) is tested through it.
- Secondary seam: the processed-data contract. Scrapers and ingestion are tested by validating output against the record contract, not by testing their internals.

## Testing Decisions

- A good test checks external behaviour only: given a question and history, what the response, sources and verdict are. It doesn't check which internal function ran.
- Chat-endpoint tests use a stubbed LLM gateway for deterministic cases (gate triggers "I don't know", verifier rejects an unsupported number, rate limit returns the right error, injection text is ignored, history trimming respects the budget, fallback chain advances on failure).
- Real-model evals run through the same endpoint against the golden set and are reported, not asserted as unit tests, because free models are non-deterministic.
- Data-contract tests: every processed record validates against the schema, has a URL and date, and contains no personal-data fields.
- Retrieval comparisons (dense, BM25, hybrid) are evals, not unit tests.
- Prior art: none (greenfield). The golden set is the main regression suite.

## Out of Scope

- Arabic input or output (future work, noted in the README).
- Server-side or cross-session memory, a `remember` tool, and user accounts.
- Live scraping, a full Wasalt crawl, and incremental crawling.
- Bypassing bot protection of any kind.
- Fine-tuning, reranker models, and LLM-based summarisation of history.
- Analytics, authentication, payments and a database.
- Wasalt's CMS API and any contact or lead-capture flows.

## Further Notes

- Cut order if time is short: small-to-big expansion, then LLM-judge evals, then UI polish. Never cut the deployment, the "I don't know" behaviour or the golden set.
- Open items decided by testing: embedding model, primary and fallback free models, the retrieval-gate threshold.
- Unverified assumptions to check early: Wasalt terms, free-tier OpenRouter limits and current free model list, whether Incapsula blocks Playwright, and the exact field names in Wasalt's embedded JSON.
- No issue tracker is configured in this workspace. These documents are local Markdown. Running `/setup-matt-pocock-skills` would let the spec and tickets be published to a tracker.
