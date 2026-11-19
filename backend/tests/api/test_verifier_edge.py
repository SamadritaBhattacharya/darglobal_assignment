"""Ticket 13 - the verifier, observed at the chat API edge with a (possibly lying) scripted model."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus.json"
# Evidence in the fixture: "Alpha Residences ... offering two bedroom apartments from 1,000,000 SAR."


def ask(model_reply: str, question="What does Alpha Residences offer?"):
    client = TestClient(create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply=model_reply)))
    response = client.post("/api/chat", json={"message": question, "history": []})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    return events[-1]["verdict"], "".join(e["text"] for e in events if e["type"] == "token")


def test_a_grounded_answer_passes_through_unchanged():
    reply = "Alpha Residences offers two bedroom apartments from 1,000,000 SAR [1]."
    verdict, text = ask(reply)
    assert verdict == "answered" and text.strip() == reply


def test_a_fabricated_price_never_reaches_the_visitor():
    verdict, text = ask("Alpha Residences apartments start from 750,000 SAR [1].")
    assert "750,000" not in text
    assert verdict == "dont_know"


def test_unsupported_sentences_are_dropped_and_the_rest_is_kept_with_a_note():
    verdict, text = ask("Alpha Residences offers two bedroom apartments [1]. Prices start at 750,000 SAR [1].")
    assert verdict == "partial"
    assert "two bedroom apartments" in text and "750,000" not in text
    assert "couldn't verify" in text.lower()


def test_an_invented_name_is_caught_too():
    verdict, text = ask("Alpha Residences offers apartments [1]. It was designed by Zaha Hadid [1].")
    assert "Hadid" not in text
    assert verdict == "partial"


def test_citation_numbers_and_the_visitors_own_words_are_not_mistaken_for_claims():
    verdict, text = ask("Alpha Residences offers two bedroom apartments [1].", question="What does Alpha Residences offer?")
    assert verdict == "answered"


def ask_full(model_reply: str):
    client = TestClient(create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply=model_reply)))
    response = client.post("/api/chat", json={"message": "What does Alpha Residences offer?", "history": []})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    sources = next(e["sources"] for e in events if e["type"] == "sources")
    return events[-1]["verdict"], "".join(e["text"] for e in events if e["type"] == "token"), sources


@pytest.mark.parametrize("reply", [
    "I don't know. The information does not list the amenities of Alpha Residences [1].",
    "I do not know; the data doesn't say. [1]",
    "I couldn't find that in the information provided.",
])
def test_a_model_that_says_it_does_not_know_is_labelled_dont_know_without_source_links(reply):
    verdict, text, sources = ask_full(reply)
    assert verdict == "dont_know"
    assert sources == []
    assert "[1]" not in text and text.strip() != ""


def test_an_answer_that_merely_mentions_not_knowing_later_is_still_an_answer():
    verdict, _, sources = ask_full("Alpha Residences offers two bedroom apartments [1]. I don't know the exact opening date.")
    assert verdict == "answered" and sources


@pytest.mark.parametrize("reply", [
    "**Overview:** Alpha Residences is a beachfront development in Testville [1].",
    "- **Summary**: The development offers two bedroom apartments [1].",
    "Here is what I found:\n\n* **Description:** Alpha Residences sits by the sea [1].",
])
def test_markdown_labels_and_bullets_are_not_mistaken_for_invented_names(reply):
    verdict, text = ask(reply)
    assert verdict == "answered", text


def test_a_name_hidden_behind_a_markdown_label_is_still_caught():
    verdict, text = ask("Alpha Residences offers apartments [1].\n- **Architect:** designed by Zaha Hadid [1].")
    assert verdict == "partial" and "Hadid" not in text


def ask_with(chunks: list[str], reply: str, tmp_path, question="Tell me about the sizes"):
    records = [{"id": f"c{i}", "source": "darglobal", "url": f"https://example.test/{i}", "title": "Sizes", "section": "Overview",
                "text": text, "scraped_at": "2026-11-18T10:00:00Z"} for i, text in enumerate(chunks)]
    path = tmp_path / "c.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    client = TestClient(create_app(corpus_path=path, llm=ScriptedLLM(reply=reply)))
    events = [json.loads(l[6:]) for l in client.post("/api/chat", json={"message": question, "history": []}).text.splitlines() if l.startswith("data: ")]
    return events[-1]["verdict"], "".join(e["text"] for e in events if e["type"] == "token")


def test_a_range_whose_two_ends_come_from_different_places_is_rejected(tmp_path):
    # real failure seen with a live model: "84 to 389" when the page says "86 to 389" and mentions 84 elsewhere
    chunks = ["Sizes: residences range from 86 to 389 sqm", "Parking: unit type B has 84 parking bays"]
    reply = "The residences range from 84 to 389 sqm [1]."
    question = "Tell me about the sizes and the parking bays"  # so that BOTH chunks reach the verifier
    verdict, text = ask_with(chunks, reply, tmp_path, question)
    assert verdict == "dont_know" and "84 to 389" not in text


@pytest.mark.parametrize("reply", ["Residences range from 86 to 389 sqm [1].", "Sizes run 86–389 sqm [1]."])
def test_a_range_stated_together_in_one_place_is_accepted(tmp_path, reply):
    chunks = ["Sizes: residences range from 86 to 389 sqm", "Parking: unit type B has 84 parking bays"]
    verdict, _ = ask_with(chunks, reply, tmp_path, "Tell me about the sizes and the parking bays")
    assert verdict == "answered"


def test_comparing_two_separate_figures_from_different_places_is_still_allowed(tmp_path):
    chunks = ["Project A starts from 1,000,000 SAR", "Project B costs 4,500,000 SAR"]
    verdict, _ = ask_with(chunks, "Project A starts from 1,000,000 SAR, while Project B costs 4,500,000 SAR [1][2].", tmp_path,
                          question="Compare Project A and Project B prices")
    assert verdict == "answered"


@pytest.mark.parametrize("reply, number",[("The area is 900 sqm [1].", "900"), ("It has 12 floors [1].", "12")])
def test_numbers_missing_from_the_evidence_are_always_rejected(reply, number):
    verdict, text = ask(reply)
    assert verdict == "dont_know"
    assert number not in text
