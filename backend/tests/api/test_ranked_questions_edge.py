"""Ticket 08 - filtered and ranked questions, observed at the chat API edge."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus_listings.json"


@pytest.fixture(scope="module")
def setup():
    llm = ScriptedLLM(reply="Marlow Plaza is a fictional luxury high-rise.")
    return TestClient(create_app(corpus_path=CORPUS, llm=llm, rate_limit_per_minute=1000)), llm


def ask(client, question):
    response = client.post("/api/chat", json={"message": question, "history": []})
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    text = "".join(e["text"] for e in events if e["type"] == "token")
    sources = [s["url"].rsplit("/", 1)[-1] for s in next(e["sources"] for e in events if e["type"] == "sources")]
    return events[-1]["verdict"], text, sources


def test_cheapest_three_bedroom_apartment_for_sale_in_riyadh_is_computed_not_guessed(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text, sources = ask(client, "What is the cheapest 3-bedroom apartment for sale in Riyadh?")
    assert verdict == "answered"
    assert sources[0] == "l2"  # 950,000 beats 1,400,000; the villa, the Jeddah and the rental listings are excluded
    assert "950,000" in text and "1,400,000" in text
    assert "3,900,000" not in text and "45,000" not in text
    assert len(llm.received_prompts) == before  # computed in code, the model is never asked


def test_every_ranked_answer_says_it_covers_the_sampled_listings_only(setup):
    _, text, _ = ask(setup[0], "cheapest villa in Jeddah")
    assert "sample of 6 wasalt listings" in text.lower()
    assert "not the whole site" in text.lower()
    assert "Source: Wasalt.sa" in text


def test_most_expensive_and_largest_sort_in_the_right_direction(setup):
    client, _ = setup
    assert ask(client, "most expensive villa in Jeddah")[2][0] == "l5"
    assert ask(client, "largest listing in Riyadh")[2][0] == "l3"


def test_price_ceilings_exclude_pricier_listings(setup):
    _, text, sources = ask(setup[0], "apartments for sale in Riyadh under 1,000,000 SAR")
    assert sources == ["l2"]
    assert "1,400,000" not in text


def test_millions_shorthand_is_understood(setup):
    _, _, sources = ask(setup[0], "villas under 3 million in Riyadh or Jeddah")
    assert set(sources) == {"l4"}


def test_rentals_are_found_when_asked_for(setup):
    assert ask(setup[0], "cheapest apartment for rent in Riyadh")[2] == ["l6"]


def test_a_rental_price_says_whether_it_is_per_year_or_per_month(setup):
    _, text, _ = ask(setup[0], "cheapest apartment for rent in Riyadh")
    assert "45,000 SAR per year" in text


def test_districts_can_be_asked_for_with_or_without_a_hyphen(setup):
    assert ask(setup[0], "cheapest apartment in Al Malqa")[2] == ["l2"]
    assert ask(setup[0], "cheapest apartment in Al-Malqa")[2] == ["l2"]


@pytest.mark.parametrize("question", [
    "cheapest villa for sale in Dubai",          # a place that is not in the data
    "cheapest studio for rent in Riyadh",        # a property type that is not in the data
    "cheapest apartment in Al Nowhere",          # an unknown district
])
def test_asking_for_something_the_data_does_not_have_never_returns_unrelated_listings(setup, question):
    verdict, text, sources = ask(setup[0], question)
    assert verdict == "dont_know" and sources == []
    assert "sample of 6 wasalt listings" in text.lower()


def test_naming_the_country_is_not_treated_as_an_unknown_place(setup):
    assert ask(setup[0], "cheapest apartment for sale in Saudi Arabia")[2][0] == "l2"


def test_how_many_listings_is_counted_in_code_and_says_it_is_a_count_within_the_sample(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text, _ = ask(client, "How many listings do you have?")
    assert verdict == "answered"
    assert "found 6 matching listings" in text and "sample of 6 wasalt listings" in text.lower()
    assert "not the total" in text.lower()
    assert len(llm.received_prompts) == before  # computed, the model is never asked


@pytest.mark.parametrize("question, expected", [
    ("How many apartments for sale are there in Riyadh?", "found 2 matching listings"),
    ("How many villa listings are in Jeddah?", "found 2 matching listings"),
    ("How many rentals do you have?", "found 1 matching listing "),
])
def test_counts_respect_the_filters_in_the_question(setup, question, expected):
    assert expected in ask(setup[0], question)[1]


@pytest.mark.parametrize("question", [
    "How many Wasalt listings are there in Mecca?",
    "How many properties for sale in Dubai?",
])
def test_counting_something_the_data_does_not_have_is_a_dont_know_not_a_guess(setup, question):
    verdict, text, sources = ask(setup[0], question)
    assert verdict == "dont_know" and sources == []
    assert "sample of 6 wasalt listings" in text.lower()


def test_a_how_many_question_about_a_project_is_not_hijacked(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    _, _, sources = ask(client, "How many floors does Marlow Plaza have?")
    assert sources and sources[0] == "marlow"
    assert len(llm.received_prompts) == before + 1  # went down the normal path and asked the model


@pytest.mark.parametrize("question", [
    "How large are the biggest residences at Marlow Plaza?",   # real miss: 'biggest' alone is not a listing question
    "What is the cheapest way to enjoy the sky lounge at Marlow Plaza?",
    "Which is the largest tower?",
])
def test_a_sort_word_alone_does_not_turn_a_project_question_into_a_listing_ranking(setup, question):
    client, llm = setup
    before = len(llm.received_prompts)
    _, text, _ = ask(client, question)
    assert "sample of 6" not in text.lower() and "matching wasalt listings" not in text.lower()  # not the ranking template


@pytest.mark.parametrize("question, expected", [
    ("What 3-bedroom listings do you have in Riyadh?", {"l1", "l2"}),   # the exact question that failed for a real visitor
    ("Show me apartments for sale in Riyadh", {"l1", "l2"}),
    ("Do you have any rentals in Riyadh?", {"l6"}),
    ("Any villas for sale in Jeddah?", {"l4", "l5"}),
    ("List the listings in Jeddah", {"l4", "l5"}),
    ("What listings are in Al Malqa?", {"l2"}),
])
def test_a_plain_listing_request_is_answered_exactly_in_code(setup, question, expected):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text, sources = ask(client, question)
    assert verdict == "answered" and set(sources) == expected
    assert "sample of 6 wasalt listings" in text.lower() and "Source: Wasalt.sa" in text
    assert "cheapest first" not in text.lower()  # nobody asked for an ordering, so none is claimed
    assert len(llm.received_prompts) == before  # free: no model call


def test_when_no_listing_has_the_requested_bedrooms_the_closest_ones_are_offered_and_labelled(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text, sources = ask(client, "What 9-bedroom listings do you have in Riyadh?")
    assert verdict == "partial"
    assert "couldn't find a 9-bedroom" in text and "Riyadh" in text
    assert "without the bedroom filter" in text.lower()
    assert set(sources) <= {"l1", "l2", "l3", "l6"} and sources  # only Riyadh listings, none from Jeddah
    assert len(llm.received_prompts) == before


def test_relaxing_never_invents_a_place(setup):
    verdict, _, sources = ask(setup[0], "What 3-bedroom listings do you have in Dubai?")
    assert verdict == "dont_know" and sources == []


def test_a_listing_request_for_a_place_the_data_lacks_says_so(setup):
    verdict, text, sources = ask(setup[0], "Do you have any listings in Dubai?")
    assert verdict == "dont_know" and sources == []


@pytest.mark.parametrize("question", [
    "Which DarGlobal projects are in Riyadh?",
    "What amenities are available at Marlow Plaza?",
    "What rental returns does Marlow Plaza mention?",
])
def test_project_questions_that_mention_places_or_availability_are_not_turned_into_listing_searches(setup, question):
    _, text, _ = ask(setup[0], question)
    assert "matching wasalt listings" not in text.lower() and "sample of 6" not in text.lower()


def test_no_matching_listing_says_so_instead_of_guessing(setup):
    verdict, text, sources = ask(setup[0], "cheapest 9 bedroom villa in Riyadh")
    assert verdict == "dont_know" and sources == []
    assert "sample of 6 wasalt listings" in text.lower()


def test_at_most_five_listings_are_shown(setup):
    _, _, sources = ask(setup[0], "cheapest listing for sale")
    assert 1 <= len(sources) <= 5


def test_ordinary_questions_are_not_hijacked_by_the_ranking_path(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, _, sources = ask(client, "Tell me about Marlow Plaza")
    assert sources[0] == "marlow"
    assert len(llm.received_prompts) == before + 1  # the normal path asked the model
