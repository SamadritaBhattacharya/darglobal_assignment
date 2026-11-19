"""Answer-quality metrics: small pure functions, verified by hand-computed examples."""
import pytest

from evals.metrics import abstention_stats, fact_recall, hallucination_rate, numbers_grounded


def test_fact_recall_is_the_share_of_expected_facts_stated_in_the_answer():
    assert fact_recall(["47", "Jeddah"], "The tower has 47 floors.") == 0.5
    assert fact_recall(["JEDDAH"], "It is in Jeddah") == 1.0
    assert fact_recall([], "anything") == 1.0


def test_typographic_hyphens_and_spaces_do_not_hide_a_correct_fact():
    # models often emit U+2011 (non-breaking hyphen) and U+202F (narrow no-break space)
    assert fact_recall(["Al-Arid", "60,000 SAR"], "A floor in Al‑Arid, Riyadh for 60,000 SAR per year") == 1.0
    assert numbers_grounded("It costs 60,000 SAR", ["price 60,000 SAR"]) is True


def test_numbers_are_grounded_only_if_every_one_appears_in_the_cited_sources():
    sources = ["Apartments range from 70 to 365 sqm, price 1,200,000 SAR"]
    assert numbers_grounded("Sizes are 70 to 365 sqm [1].", sources) is True
    assert numbers_grounded("It costs 1200000 SAR.", sources) is True  # comma formatting does not matter
    assert numbers_grounded("It has 47 floors.", sources) is False
    assert numbers_grounded("A lovely place.", sources) is True  # no numbers, nothing to ground


def test_citation_markers_are_not_numbers():
    assert numbers_grounded("It is lovely [1][2].", ["no digits here"]) is True


def test_abstention_precision_and_recall():
    rows = [(True, True), (True, True), (True, False), (False, True), (False, False)]  # (should_abstain, abstained)
    stats = abstention_stats(rows)
    assert stats["precision"] == pytest.approx(2 / 3)  # 3 abstained, 2 rightly
    assert stats["recall"] == pytest.approx(2 / 3)  # 3 should have, 2 did


def test_abstention_with_nothing_to_measure_is_not_a_division_error():
    assert abstention_stats([]) == {"precision": 1.0, "recall": 1.0}
    assert abstention_stats([(False, False)]) == {"precision": 1.0, "recall": 1.0}


def test_hallucination_rate_is_the_share_of_unanswerable_questions_that_got_an_answer():
    rows = [(True, False), (True, True), (True, False), (True, False), (False, True)]  # (should_abstain, answered)
    assert hallucination_rate(rows) == 0.25  # 1 of the 4 unanswerable ones was answered
    assert hallucination_rate([(False, True)]) == 0.0
