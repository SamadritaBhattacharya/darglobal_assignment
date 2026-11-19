# Goals

## Goal
Prove end-to-end applied-AI engineering for the DarGlobal Junior AI Engineer assignment: scrape public data, build a grounded chatbot, containerise it, deploy it, and measure it.

## Destination
A public URL where a recruiter chats about DarGlobal projects and Wasalt listings in English. Answers are cited. When the data does not support an answer, the bot says "I don't know".

## Success (all must hold)
1. **Live:** the URL works from a second device and a phone, with no setup. Deadline Fri 20 Nov 2026; target live Thu 19 Nov afternoon.
2. **Grounded:** every factual claim carries a citation to a stored source. No fact or price appears that is not in the retrieved evidence.
3. **Honest:** unanswerable questions get "I don't know" (hallucination on the unanswerable set <= 5%).
4. **Measured:** faithfulness >= 0.85; hybrid retrieval >= dense-only and BM25-only on recall@5 and MRR; context precision and recall reported.
5. **Safe:** no secrets in repo or image; no personal data stored; injection and advice requests refused; rate-limited.
6. **Reproducible:** one Docker build and run; one command to refresh data; one command to run evals.
7. **Transparent:** README states scraping method, limits (sample, snapshot, English only, free-model quotas) and results, including any missed bar.

## Non-goals
Arabic, server-side memory, accounts, live scraping, full Wasalt crawl, bypassing bot protection, fine-tuning.

## Priority order when time is short
Never cut: deployment, "I don't know" behaviour, golden set. Cut first: small-to-big expansion, then LLM-judge evals, then UI polish.
