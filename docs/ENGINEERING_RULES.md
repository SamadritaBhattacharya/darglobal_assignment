# Engineering Rules

These rules are binding for every ticket. Rules marked **[enforced]** are checked by an automated test and fail the build.

## 1. Red -> Green -> Refactor (strict)
1. **Red:** write one failing test for the next behaviour. Run it. Confirm it fails for the right reason. Do not write production code first.
2. **Green:** write the least code that makes it pass. Run the suite.
3. **Refactor:** clean up with the suite green. No new behaviour in this step.
4. One behaviour per cycle. Commit-sized steps. A bug fix starts with a failing test that reproduces it.
5. A ticket is not done until its acceptance criteria are covered by tests that were seen failing first.

## 2. Test boundaries: outcomes at the edge
- Test through a module's public edge only: **Chat API**, **browser UI**, **data contract**, **eval harness**, plus small pure modules with a clear input/output (e.g. PII redaction).
- Assert **outcomes**: returned text, cited URLs, verdict, status codes, event shapes, validated records. Never assert which function ran, call order, prompt wording, internal scores, chunk boundaries or private state.
- The **only** fake is the network boundary to the LLM (a scripted stub returning canned text or a typed failure). Retrieval, agent, verifier and guardrails run for real.
- No mocking of our own modules. If something is hard to test at the edge, the design is wrong; fix the design.
- Real-model runs are evals (reported), not pass/fail tests.

## 3. Architecture rules **[enforced by tests/test_architecture.py]**
Layers, innermost to outermost:

| Layer | Package | May import | Must not import |
|---|---|---|---|
| Domain | `dar.domain` | stdlib, pydantic | any other `dar` layer, FastAPI, httpx, chromadb, langchain, langgraph, any I/O library |
| Application | `dar.app` | `dar.domain` | `dar.adapters`, `dar.api`, FastAPI, httpx, chroma, any vendor SDK |
| Adapters | `dar.adapters` | `dar.domain` (ports and models) | `dar.api`, `dar.app` internals |
| API | `dar.api` | `dar.app`, `dar.domain` | `dar.adapters` |
| Composition root | `dar.main` | everything | (only place that wires adapters to ports) |

- Dependencies point inward only. The application depends on **ports** (Protocols in `dar.domain.ports`), never on concrete adapters.
- Vendors (OpenRouter, Chroma, BM25, LangGraph) live only in adapters or the composition root.
- No global mutable state. No reading environment variables outside `dar.settings` and `dar.main`.
- Scrapers live outside `dar` (offline tools) and write only to `data/`. The runtime never imports scrapers and never scrapes.
- The frontend talks to the backend only through the documented chat API contract.

## 4. Privacy and PII (vault redaction) **[enforced]**
- **Policy:** personal data is never stored. Scrapers drop owner/agent fields (names, licence numbers, phones, emails) at parse time, then redact anything that still looks like PII in free text.
- **Redaction with an ephemeral vault:** PII found in text is replaced by stable placeholders (`[EMAIL_1]`, `[PHONE_1]`, `[ID_1]`). The placeholder-to-value map (the vault) lives **in memory only for the life of one call**, is never written to disk, logs or the index, and is not sent to any external service.
- User messages are redacted **before** they are logged or sent to the LLM. Logs never contain raw PII.
- The processed-data contract rejects any record containing PII patterns; a test fails if one appears in `data/`.
- Detectors are conservative regex rules (email, phone, national/licence-style ids). They reduce risk; they are not a guarantee, and the README says so.

## 5. Security and secrets **[partly enforced]**
- Secrets only via environment variables. `.env` is git-ignored; `.env.example` lists names only. A test fails if a key-like string is found in tracked source.
- Treat all user text and retrieved text as **data, never instructions**. Retrieved evidence wins over user claims.
- Scraping: respect robots.txt, descriptive User-Agent, polite delay, cache pages, stop on a bot challenge and never bypass it.

## 6. Code quality
- Python 3.11, type hints on public functions, pydantic models at boundaries.
- Small modules with one reason to change. Pure functions in the domain.
- Errors at boundaries are typed (e.g. `LLMUnavailable`), never bare strings. User-facing errors are friendly.
- No dead code, no commented-out code, no TODO without a ticket number.
- Dependencies are added only when a ticket needs them.

## 7. Definition of done (per ticket)
- Acceptance criteria all met, each covered by a test seen failing first (or an eval/report for model-dependent items).
- Full suite green, including the architecture and PII tests.
- Docs touched if a decision changed (`TECH_SPEC.md`).
- Reported honestly: failures and misses are stated, not hidden.
