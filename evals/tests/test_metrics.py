"""Retrieval metrics: small pure functions, verified by hand-computed examples."""
import pytest

from evals.metrics import context_precision, context_recall, mean, recall_at_k, reciprocal_rank

RETRIEVED = ["a", "b", "c", "d", "e"]


def test_recall_is_the_share_of_expected_sources_found_in_the_top_k():
    assert recall_at_k(RETRIEVED, ["a", "d"], k=3) == 0.5
    assert recall_at_k(RETRIEVED, ["a", "d"], k=5) == 1.0
    assert recall_at_k(RETRIEVED, ["z"], k=5) == 0.0


def test_repeated_urls_in_the_results_count_once():
    assert recall_at_k(["a", "a", "a", "b"], ["b"], k=2) == 1.0  # 'a' x3 is one source, so 'b' is 2nd


def test_reciprocal_rank_rewards_an_early_first_hit():
    assert reciprocal_rank(RETRIEVED, ["a"]) == 1.0
    assert reciprocal_rank(RETRIEVED, ["c", "e"]) == pytest.approx(1 / 3)
    assert reciprocal_rank(RETRIEVED, ["z"]) == 0.0


def test_context_precision_is_the_share_of_retrieved_sources_that_were_wanted():
    assert context_precision(RETRIEVED, ["a", "b"], k=4) == 0.5  # a,b wanted; c,d not
    assert context_precision([], ["a"], k=4) == 0.0


def test_context_recall_is_the_share_of_expected_facts_present_in_the_retrieved_text():
    texts = ["The tower has 47 floors in Jeddah", "Apartments from 70 to 365 sqm"]
    assert context_recall(["47", "365", "Riyadh"], texts) == pytest.approx(2 / 3)
    assert context_recall(["JEDDAH"], texts) == 1.0  # case-insensitive
    assert context_recall([], texts) == 1.0  # nothing was required


def test_mean_of_nothing_is_zero_not_an_error():
    assert mean([]) == 0.0 and mean([1, 0]) == 0.5
