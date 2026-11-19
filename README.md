---
title: DarGlobal Assistant
emoji: 🏢
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
python_version: 3.11.13
pinned: false
---
# DarGlobal & Wasalt assistant

A grounded, citation-first chatbot over public **DarGlobal** project pages and **Wasalt** property listings. Ask in English; get an answer built only from stored sources, with a link to each one. When the data does not support an answer, it says **"I don't know"** instead of guessing.

**Live demo:** [darglobal-assiatant.vercel.app](https://darglobal-assiatant.vercel.app/)

## What it does

- Answers questions about DarGlobal projects and Wasalt listings, streamed token by token.
- Cites every factual claim with numbered sources, shown as cards with photo, key details and a "Click to know more" link to the original page.
- Abstains honestly: unanswerable questions get a visible "Not in my data" badge, advice requests and prompt-injection attempts are refused.
- Handles follow-ups ("open the 1st one") using the last six turns, held in the browser only.
- Shows live progress while it works (thinking, searching, generating), with a light/dark theme toggle.

## How it works

```
scrapers (offline) -> data/raw -> data/processed/*.json
                                      |
                              ingest (build time)
                                      v
 Browser (Next.js static) -> POST /api/chat -> guardrails -> agent -> verifier
                                                    |           |
                                           Retriever port    LLM port
                                           (Chroma + BM25)   (OpenRouter free-model chain)
```

1. **Guardrails:** English-only, 500-character cap, off-topic redirect, injection treated as data, no legal/financial advice, per-IP rate limit.
2. **Hybrid retrieval:** dense vectors (Chroma, local embedding model) and BM25 over the same chunks, merged with Reciprocal Rank Fusion. A relevance gate refuses weak matches (precision over recall).
3. **Agent:** a small tool-using agent (search with filters, get document) capped at a few steps.
4. **Verifier:** numbers, names and prices in the answer must appear in the retrieved text, otherwise the verdict is downgraded to `partial` or `dont_know`.
5. **Verdicts:** every response ends with `answered`, `partial`, `dont_know`, `refused` or `error`.

Full design in [docs/TECH_SPEC.md](docs/TECH_SPEC.md); requirements in [docs/PRD.md](docs/PRD.md); goals in [docs/GOALS.md](docs/GOALS.md).

## Project layout

| Path                       | What lives there                                                                                                                                          |
| -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend/src/dar/`       | FastAPI app, layered: `domain` (models, ports, PII), `app` (use-cases), `adapters` (retrieval, LLM), `api` (HTTP), `main.py` (composition root) |
| `backend/tests/`         | Behaviour tests at module edges, plus `test_architecture.py` enforcing the layers                                                                       |
| `frontend/`              | Next.js UI, statically exported and served by the backend                                                                                                 |
| `scraper/`               | Offline scrapers for DarGlobal and Wasalt (never run at request time)                                                                                     |
| `data/`                  | `raw/` cached pages, `processed/` records the app reads, `export/`, `index/`                                                                      |
| `evals/`                 | Golden set (48 questions), retrieval and answer evals, results                                                                                            |
| `docs/`                  | PRD, tech spec, engineering rules, tickets, decisions                                                                                                     |
| `Dockerfile`, `app.py` | One-container build; `app.py` is the Hugging Face Spaces entry point                                                                                    |

## Run it locally

Requirements: Python 3.11, Node 22, and a free [OpenRouter](https://openrouter.ai) API key.

```bash
# 1. configure
cp .env.example .env            # set OPENROUTER_API_KEY (OPENROUTER_API_KEY_2 is an optional backup)

# 2. build the UI to static files
cd frontend && npm ci && npm run build && cd ..

# 3. install and start the backend (serves API and UI)
python -m venv .venv && .venv\Scripts\activate      # source .venv/bin/activate on macOS/Linux
pip install -r backend/requirements.txt
cd backend && uvicorn src.dar.main:app --reload --port 8000
```

Open http://localhost:8000. For UI work with hot reload, run `npm run dev` in `frontend/`.

### Docker

```bash
docker build -t darglobal .
docker run -p 7860:7860 -e OPENROUTER_API_KEY=your_key darglobal
```

The index and embedding model are baked into the image, so a cold start takes seconds. The key is supplied at run time and never stored in the image.

### Deploy to Hugging Face Spaces

The Space runs `app.py` (Gradio SDK, since the Docker SDK is paid). Add `OPENROUTER_API_KEY` (and optionally `OPENROUTER_API_KEY_2`) as Space secrets.

## Tests

```bash
cd backend && ..\.venv\Scripts\python -m pytest     # backend
cd frontend && npm test                             # UI (vitest)
```

Development follows strict Red -> Green -> Refactor with tests that assert outcomes at module edges only. See [docs/ENGINEERING_RULES.md](docs/ENGINEERING_RULES.md).

## Refresh the data

One human-run, polite pipeline (cached, robots-aware, about 1 request per second, never at runtime):

```bash
python -m scraper.darglobal.fetch     # download pages (needs Playwright)
python -m scraper.darglobal.build     # -> data/processed/darglobal.json
python -m scraper.wasalt.build        # -> data/processed/wasalt.json
```

## Evaluation

Run from the repo root:

```bash
python -m evals.run_retrieval     # retrieval metrics, no model calls
python -m evals.run_answers       # answer evals against the live model chain
python -m evals.summarize         # merge saved runs into one report, no model calls
```

**Retrieval** (21 answerable golden questions, top 5):

| retriever       | recall@5 | MRR  | context precision | context recall |
| --------------- | -------- | ---- | ----------------- | -------------- |
| keyword (BM25)  | 0.90     | 0.77 | 0.39              | 0.93           |
| vector (Chroma) | 1.00     | 0.91 | 0.57              | 1.00           |
| hybrid (RRF)    | 0.95     | 0.86 | 0.50              | 0.95           |

On this small set, vector-only beat hybrid, which missed the goal of hybrid matching or beating both. With a corpus this size and mostly natural-language questions, BM25 adds noise to a strong dense ranking.

**Answers** (48 golden questions, merged latest runs):

| metric                            | result      |
| --------------------------------- | ----------- |
| verdict accuracy                  | 0.96        |
| answerable questions attempted    | 31 / 31     |
| fact recall (answerable)          | 0.98        |
| source hit (answerable)           | 1.00        |
| numeric grounding                 | 1.00        |
| abstention precision / recall     | 1.00 / 1.00 |
| hallucination rate (unanswerable) | 0.00        |
| adversarial prompts refused       | 1.00        |
| average latency                   | 5.2 s       |

These come from rule-based checks. A free-model LLM judge for faithfulness is not part of the numbers above.

## Limits you should know about

- **Sample and snapshot, not live data:** 502 DarGlobal records and only 23 Wasalt listings, scraped once. Always check wasalt.sa for current prices and availability.
- **English only.** No Arabic support.
- **Free-model quotas:** answers come from a chain of OpenRouter `:free` models; during heavy use, quota limits can cause errors or slower fallbacks.
- **Precision over recall:** loosely worded paraphrases near the relevance threshold may be refused.
- **Verifier limits:** numbers and names are checked against all retrieved evidence, not per cited source, and written numbers ("two") are not checked. See [docs/TECH_SPEC.md](docs/TECH_SPEC.md) section 9.
- **No server memory:** conversation history lives in your browser and is sent with each question.

## Privacy and safety

- Personal data is redacted with an in-memory vault and never stored; logs are redacted.
- No secrets in the repo or image; keys come from the environment only.
- The scrapers never bypass bot protection and are never run at request time.

## Data sources and attribution

Content comes from public DarGlobal pages and public Wasalt listing pages, used as a small, attributed, **non-commercial** sample for a job assessment. Wasalt content is credited as "Source: Wasalt.sa". See [docs/decisions/0001-wasalt-access-note.md](docs/decisions/0001-wasalt-access-note.md) for what the site's robots.txt and AI policy allow.

## Tech stack

Python 3.11, FastAPI, Chroma, rank-bm25, LangGraph/LangChain, OpenRouter free models, Next.js (static export), Docker, Hugging Face Spaces.
