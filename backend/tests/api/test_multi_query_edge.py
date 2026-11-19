"""Follow-ups and comparisons must still reach the right pages (real failures seen against the live model)."""
import json

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app


def build(tmp_path, pages: dict[str, list[str]]):
    records, n = [], 0
    for slug, texts in pages.items():
        for text in texts:
            n += 1
            records.append({"id": f"c{n}", "source": "darglobal", "url": f"https://example.test/{slug}",
                            "title": slug.title(), "section": "Overview", "text": f"DarGlobal | {slug.title()} | Overview\n{text}",
                            "scraped_at": "2026-11-18T10:00:00Z"})
    path = tmp_path / "c.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return TestClient(create_app(corpus_path=path, llm=ScriptedLLM(reply="ok [1]"), rate_limit_per_minute=1000))


def cited(client, message, history=()):
    r = client.post("/api/chat", json={"message": message, "history": list(history)})
    events = [json.loads(l[6:]) for l in r.text.splitlines() if l.startswith("data: ")]
    return [s["url"].rsplit("/", 1)[-1] for s in next(e["sources"] for e in events if e["type"] == "sources")]


# Many other towers answer "how big are the apartments" just as well, which swamps a follow-up's real subject.
DISTRACTORS = {f"tower{c}": [f"Tower {c} apartments range from {60 + i} to {300 + i} sqm with large rooms and big balconies"]
               for i, c in enumerate("BCDEFGH")}


def test_a_follow_up_still_reaches_the_page_about_the_topic_of_the_conversation(tmp_path):
    pages = {"alpha": ["Alpha Heights is a seafront tower in Jeddah developed by DarGlobal. Apartments range from 70 to 365 sqm."],
             **DISTRACTORS}
    client = build(tmp_path, pages)
    history = [{"role": "user", "content": "Tell me about Alpha Heights"},
               {"role": "assistant", "content": "Alpha Heights is a seafront tower in Jeddah."}]
    assert "alpha" in cited(client, "How big are the apartments?", history)


def test_a_comparison_brings_evidence_for_both_sides(tmp_path):
    pages = {"neptune": [f"Neptune is a villa collection in Riyadh with refined finishes, part {i}" for i in range(6)],
             "marea": ["Marea is a gated community in Cortesin, Spain with sea views"]}
    client = build(tmp_path, pages)
    sources = cited(client, "Compare Neptune and Marea")
    assert "neptune" in sources and "marea" in sources


def test_other_comparison_phrasings_also_cover_both_sides(tmp_path):
    pages = {"lesvagues": [f"Les Vagues is a seafront complex in Doha, residences from 86 to 389 sqm, part {i}" for i in range(6)],
             "astera": ["The Astera is a beachfront development in Ras Al Khaimah, residences from 61 to 265 sqm"]}
    client = build(tmp_path, pages)
    sources = cited(client, "How do the residence sizes at Les Vagues and The Astera compare?")
    assert "lesvagues" in sources and "astera" in sources


def test_a_plain_question_is_unaffected(tmp_path):
    pages = {"alpha": ["Alpha Heights is a seafront tower in Jeddah. Apartments range from 70 to 365 sqm."], **DISTRACTORS}
    assert cited(build(tmp_path, pages), "Tell me about Alpha Heights")[0] == "alpha"
