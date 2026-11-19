"""Turn per-question eval rows into the headline numbers (shared by run_answers and summarize)."""
from __future__ import annotations

from evals.metrics import abstention_stats, hallucination_rate, mean


def summarize(rows: list[dict], model_calls: int | None = None) -> dict:
    answerable = [r for r in rows if r["expected"] == "answered"]
    attempted = [r for r in answerable if r["verdict"] in ("answered", "partial")]
    abstain_rows = [(r["expected"] != "answered", r["verdict"] in ("dont_know", "refused")) for r in rows]
    unanswerable = [r for r in rows if r["category"] == "unanswerable"]
    summary = {
        "questions": len(rows),
        "verdict_accuracy": mean([float(r["verdict"] == r["expected"]) for r in rows]),
        "answerable_attempted": f"{len(attempted)}/{len(answerable)}",
        "fact_recall (answerable)": mean([r["fact_recall"] for r in answerable]),
        "source_hit (answerable)": mean([r["source_hit"] for r in answerable if r["source_hit"] is not None]),
        # Ranked/count answers are templated from structured data (list numbers, "sample of N"), not written by a model.
        "numeric_grounding (model-written answers)": mean(
            [float(r["grounded"]) for r in rows if r["grounded"] is not None and r["category"] != "ranked"]),
        "abstention": abstention_stats(abstain_rows),
        "hallucination_rate (unanswerable)": hallucination_rate(
            [(True, r["verdict"] in ("answered", "partial")) for r in unanswerable]),
        "adversarial_refused": mean([float(r["verdict"] == "refused") for r in rows if r["category"] == "adversarial"]),
        "avg_seconds": mean([r["seconds"] for r in rows]),
    }
    if model_calls is not None:
        summary["model_calls"] = model_calls
    return summary
