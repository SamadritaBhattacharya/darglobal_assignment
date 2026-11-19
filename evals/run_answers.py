"""Answer evals: the golden set through the whole app (real data, real free model, real verifier).

Usage (repo root):  python -m evals.run_answers [--categories ranked,adversarial,unanswerable]
Needs OPENROUTER_API_KEY in .env for categories that reach the model. Writes evals/results/answers*.json|md.
Faithfulness here is RULE-BASED: every number in an answer must appear in the pages it cites. An LLM judge
is not used, so this does not catch wrong claims that contain no numbers.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from dar.adapters.openrouter import OpenRouterLLM  # noqa: E402
from dar.main import create_app, load_corpus  # noqa: E402
from dar.settings import Settings  # noqa: E402
from evals.metrics import fact_recall, numbers_grounded  # noqa: E402
from evals.report import summarize  # noqa: E402


class CountingLLM(OpenRouterLLM):
    calls = 0

    def complete(self, prompt: str) -> str:
        CountingLLM.calls += 1
        return super().complete(prompt)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--categories", default="")
    parser.add_argument("--ids", default="", help="comma-separated golden ids to run (saves free-tier quota)")
    args = parser.parse_args()
    wanted = {c for c in args.categories.split(",") if c}
    wanted_ids = {i for i in args.ids.split(",") if i}

    key = re.search(r"^OPENROUTER_API_KEY=(.+)$", (ROOT / ".env").read_text(encoding="utf-8"), re.M).group(1).strip()
    settings = Settings()
    app = create_app(settings.data_dir, CountingLLM(key, settings.models), index_dir=settings.index_dir,
                     rate_limit_per_minute=10**6)
    client = TestClient(app)

    page_text: dict[str, str] = {}
    for chunk in load_corpus(settings.data_dir):
        page_text[chunk.url] = page_text.get(chunk.url, "") + "\n" + chunk.text

    items = [json.loads(l) for l in (ROOT / "evals" / "golden.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    items = [i for i in items if (not wanted or i["category"] in wanted) and (not wanted_ids or i["id"] in wanted_ids)]

    rows = []
    for item in items:
        started = time.time()
        response = client.post("/api/chat", json={"message": item["question"], "history": item["history"]})
        events = [json.loads(l[6:]) for l in response.text.splitlines() if l.startswith("data: ")]
        text = "".join(e["text"] for e in events if e["type"] == "token")
        cited = [s["url"] for s in next((e["sources"] for e in events if e["type"] == "sources"), [])]
        verdict = events[-1]["verdict"] if events else "error"
        rows.append({
            "id": item["id"], "category": item["category"], "question": item["question"],
            "expected": item["expected_verdict"], "verdict": verdict, "seconds": round(time.time() - started, 1),
            "fact_recall": fact_recall(item["expected_facts"], text),
            "source_hit": (sum(u in cited for u in item["expected_sources"]) / len(item["expected_sources"])) if item["expected_sources"] else None,
            # Ranked/count answers are computed from structured fields (their template has list numbers and the
            # sample size), so only model-written answers are checked for grounding.
            "grounded": numbers_grounded(text, [page_text.get(u, "") for u in cited])
            if verdict in ("answered", "partial") and item["category"] != "ranked" else None,
            "answer": text[:600], "cited": cited,
        })
        print(f"{item['id']:6} {item['expected_verdict']:9} -> {verdict:9} facts={rows[-1]['fact_recall']:.2f} {rows[-1]['seconds']:5.1f}s", flush=True)

    summary = summarize(rows, model_calls=CountingLLM.calls)
    tag = "-".join(sorted(wanted)) or ("ids-" + "-".join(sorted(wanted_ids)) if wanted_ids else "all")
    out = ROOT / "evals" / "results"
    out.mkdir(exist_ok=True)
    (out / f"answers-{tag}.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print("\nSUMMARY\n" + json.dumps(summary, indent=2))
    wrong = [(r["id"], r["expected"], r["verdict"]) for r in rows if r["verdict"] != r["expected"]]
    print("\nverdict mismatches:", wrong)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
