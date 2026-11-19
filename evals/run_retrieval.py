"""Retrieval evals on the golden set: keyword-only vs vector-only vs hybrid.

Usage (from the repo root):  python -m evals.run_retrieval
No model calls. Writes evals/results/retrieval.json and retrieval.md.
Ranking is measured with the relevance floors OPEN, so it reflects ordering quality, not the refusal gate
(the gate is calibrated separately in the answer evals).
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from dar.adapters.retrieval import Bm25Retriever, DenseRetriever, HybridRetriever  # noqa: E402
from dar.main import load_corpus  # noqa: E402
from evals.metrics import context_precision, context_recall, mean, recall_at_k, reciprocal_rank  # noqa: E402

K = 5
SKIPPED = {"ranked", "follow_up", "unanswerable", "adversarial"}


def main() -> int:
    chunks = load_corpus(ROOT / "data" / "processed")
    index_dir = ROOT / "data" / "index"
    retrievers = {
        "keyword (BM25)": Bm25Retriever(chunks),
        "vector (Chroma)": DenseRetriever(chunks, max_distance=9.0, index_dir=index_dir),
        "hybrid (RRF)": HybridRetriever(chunks, max_distance=9.0, min_coverage=0.0, index_dir=index_dir),
    }
    items = [json.loads(l) for l in (ROOT / "evals" / "golden.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    items = [i for i in items if i["category"] not in SKIPPED]

    results = {}
    for name, retriever in retrievers.items():
        rows = []
        for item in items:
            hits = retriever.search(item["question"], k=K)
            urls = [c.url for c in hits]
            rows.append({
                "id": item["id"],
                "recall": recall_at_k(urls, item["expected_sources"], K),
                "mrr": reciprocal_rank(urls, item["expected_sources"]),
                "precision": context_precision(urls, item["expected_sources"], K),
                "ctx_recall": context_recall(item["expected_facts"], [c.text for c in hits]),
            })
        results[name] = {
            "n": len(rows),
            "recall@5": mean([r["recall"] for r in rows]),
            "MRR": mean([r["mrr"] for r in rows]),
            "context precision": mean([r["precision"] for r in rows]),
            "context recall": mean([r["ctx_recall"] for r in rows]),
            "misses": [r["id"] for r in rows if r["recall"] < 1.0],
        }

    out = ROOT / "evals" / "results"
    out.mkdir(exist_ok=True)
    (out / "retrieval.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    lines = [f"Retrieval on {len(items)} answerable golden questions (top {K}; follow-ups and ranked excluded)", "",
             "| retriever | recall@5 | MRR | context precision | context recall |", "|---|---|---|---|---|"]
    for name, r in results.items():
        lines.append(f"| {name} | {r['recall@5']:.2f} | {r['MRR']:.2f} | {r['context precision']:.2f} | {r['context recall']:.2f} |")
    table = "\n".join(lines)
    (out / "retrieval.md").write_text(table + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(table)
    for name, r in results.items():
        print(f"\nmissed by {name}: {r['misses']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
