"""The golden dataset is itself checked: valid shape, balanced coverage, and every expected answer is
really supported by the data it cites (so the eval measures the bot, not a typo in the labels)."""
import json
import pathlib
import re
from collections import Counter
from typing import Literal

import pytest
from pydantic import BaseModel, Field

from dar.domain.models import Turn
from dar.domain.pii import redact

REPO = pathlib.Path(__file__).resolve().parents[2]
GOLDEN = REPO / "evals" / "golden.jsonl"
PROCESSED = REPO / "data" / "processed"

Category = Literal["darglobal_lookup", "wasalt_lookup", "ranked", "comparison", "follow_up", "unanswerable", "adversarial"]
MINIMUM = {"darglobal_lookup": 10, "wasalt_lookup": 4, "ranked": 4, "comparison": 3, "follow_up": 5,
           "unanswerable": 10, "adversarial": 4}


class Item(BaseModel):
    id: str
    category: Category
    question: str = Field(min_length=1, max_length=500)
    history: list[Turn] = []
    expected_verdict: Literal["answered", "dont_know", "refused"]
    expected_facts: list[str] = []
    expected_sources: list[str] = []
    notes: str = ""


@pytest.fixture(scope="module")
def items():
    assert GOLDEN.exists(), "evals/golden.jsonl is missing"
    return [Item(**json.loads(line)) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture(scope="module")
def source_text():
    texts: dict[str, str] = {}
    for file in PROCESSED.glob("*.json"):
        for record in json.loads(file.read_text(encoding="utf-8")):
            texts[record["url"]] = texts.get(record["url"], "") + "\n" + record["text"]
    return texts


def test_ids_are_unique_and_the_set_is_big_enough(items):
    assert len({i.id for i in items}) == len(items)
    assert len(items) >= 40


def test_every_category_meets_its_minimum_and_unanswerable_is_a_fifth_or_so(items):
    counts = Counter(i.category for i in items)
    assert {c: counts[c] for c in MINIMUM if counts[c] < MINIMUM[c]} == {}
    assert 0.15 <= counts["unanswerable"] / len(items) <= 0.35


def test_labels_are_consistent_with_the_category(items):
    for i in items:
        if i.category == "adversarial":
            assert i.expected_verdict == "refused" and not i.expected_sources and not i.expected_facts, i.id
        elif i.category == "unanswerable":
            assert i.expected_verdict == "dont_know" and not i.expected_sources and not i.expected_facts, i.id
        else:
            assert i.expected_verdict == "answered" and i.expected_facts and i.expected_sources, i.id


def test_follow_ups_carry_a_conversation_that_ends_with_the_assistants_turn(items):
    for i in items:
        if i.category == "follow_up":
            assert i.history and i.history[-1].role == "assistant", i.id
        else:
            assert not i.history, i.id


def test_every_cited_source_exists_in_the_committed_data(items, source_text):
    missing = [(i.id, u) for i in items for u in i.expected_sources if u not in source_text]
    assert missing == []


def test_every_expected_fact_really_appears_in_the_sources_it_cites(items, source_text):
    unsupported = []
    for i in items:
        haystack = " ".join(source_text[u] for u in i.expected_sources).lower()
        unsupported += [(i.id, fact) for fact in i.expected_facts if fact.lower() not in haystack]
    assert unsupported == []


def test_questions_contain_no_personal_data(items):
    for i in items:
        assert redact(i.question).text == i.question, i.id
