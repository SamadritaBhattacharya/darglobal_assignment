"""Merge every saved answer-eval run into one report, with NO model calls.

Usage (repo root):  python -m evals.summarize
For each golden question the most recent run wins, except that an "error" row (e.g. the free-tier daily quota
ran out) never overwrites an earlier real result: that would measure OpenRouter's limit, not answer quality.
"""
from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evals.report import summarize  # noqa: E402


def merge(files: list[pathlib.Path]) -> tuple[list[dict], list[str]]:
    latest: dict[str, dict] = {}
    quota_errors: list[str] = []
    for file in sorted(files, key=lambda p: p.stat().st_mtime):  # oldest first, so newer rows overwrite
        for row in json.loads(file.read_text(encoding="utf-8"))["rows"]:
            if row["verdict"] == "error" and row["id"] in latest and latest[row["id"]]["verdict"] != "error":
                quota_errors.append(row["id"])
                continue
            latest[row["id"]] = row
    golden = [json.loads(l)["id"] for l in (ROOT / "evals" / "golden.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    return [latest[i] for i in golden if i in latest], quota_errors


def main() -> int:
    results = ROOT / "evals" / "results"
    rows, ignored = merge(sorted(results.glob("answers-*.json")))
    summary = summarize(rows)
    (results / "answers-merged.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    by_cat: dict[str, list[dict]] = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)
    lines = ["| category | questions | verdict correct |", "|---|---|---|"]
    for cat, items in by_cat.items():
        lines.append(f"| {cat} | {len(items)} | {sum(r['verdict'] == r['expected'] for r in items)}/{len(items)} |")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("\n" + "\n".join(lines))
    print("\nstill wrong:", [(r["id"], r["expected"], r["verdict"]) for r in rows if r["verdict"] != r["expected"]])
    print("error rows ignored (quota, not quality):", ignored)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
