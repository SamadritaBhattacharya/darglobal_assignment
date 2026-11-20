"""Everyday social phrases get a natural, matching reply: "good morning" is answered with "Good morning!"."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus.json"


@pytest.fixture(scope="module")
def setup():
    llm = ScriptedLLM(reply="Alpha Residences offers two bedroom apartments [1].")
    return TestClient(create_app(corpus_path=CORPUS, llm=llm, rate_limit_per_minute=100000)), llm


def chat(client, message, profile=None):
    body = {"message": message, "history": []}
    if profile:
        body["profile"] = profile
    r = client.post("/api/chat", json=body)
    ev = [json.loads(l[6:]) for l in r.text.splitlines() if l.startswith("data: ")]
    return ev[-1]["verdict"], "".join(e["text"] for e in ev if e["type"] == "token")


def free(setup, message, profile=None):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text = chat(client, message, profile)
    assert verdict == "answered" and "couldn't find" not in text.lower()
    assert len(llm.received_prompts) == before  # social replies never use the model
    return text


@pytest.mark.parametrize("message, echoed", [
    ("Good morning", "Good morning"), ("good afternoon", "Good afternoon"), ("Good evening!", "Good evening"),
    ("good day", "Good day"), ("morning", "Good morning"), ("evening", "Good evening"),
])
def test_a_timed_greeting_is_answered_with_the_same_greeting(setup, message, echoed):
    assert free(setup, message).startswith(echoed)


def test_the_timed_greeting_also_uses_the_name_when_known(setup):
    first_line = free(setup, "good morning", {"name": "Samadrita"}).split("\n")[0]
    assert first_line.startswith("Good morning") and "Samadrita" in first_line


def test_a_greeting_with_an_introduction_keeps_the_timed_greeting(setup):
    text = free(setup, "good evening i am Samadrita. who are you?")
    assert text.startswith("Good evening") and "Samadrita" in text and "assistant" in text.lower()


@pytest.mark.parametrize("message", ["salam", "assalamu alaikum", "Assalamu Alaikum"])
def test_salam_is_just_answered_with_a_normal_greeting(setup, message):
    text = free(setup, message)
    assert text.lower().startswith(("hello", "hi", "hey"))   # an ordinary greeting, not a translated one
    assert "alaikum" not in text.lower() and "assalam" not in text.lower()


@pytest.mark.parametrize("message", ["good night", "Good night!", "night night"])
def test_good_night_gets_a_good_night(setup, message):
    assert "good night" in free(setup, message).lower()


@pytest.mark.parametrize("message", ["have a great day", "Have a nice day!", "enjoy your evening", "have a good weekend"])
def test_well_wishes_are_returned(setup, message):
    assert "you too" in free(setup, message).lower()


@pytest.mark.parametrize("message", ["nice to meet you", "Pleased to meet you", "nice meeting you"])
def test_nice_to_meet_you_is_returned(setup, message):
    assert "nice to meet you too" in free(setup, message).lower()


@pytest.mark.parametrize("message", ["ok", "okay", "cool", "great", "nice", "awesome", "got it", "alright", "perfect", "wow",
                                     "sounds good", "i see", "understood"])
def test_short_acknowledgements_get_a_friendly_nudge_forward(setup, message):
    text = free(setup, message)
    assert text.rstrip().endswith("?")  # invites what to do next, never a dead end


@pytest.mark.parametrize("message", ["ok thanks", "cool thank you", "great, thanks"])
def test_an_acknowledgement_with_thanks_is_a_thank_you(setup, message):
    assert "welcome" in free(setup, message).lower()


@pytest.mark.parametrize("message", ["sorry", "my bad", "oops", "sorry about that", "I'm sorry"])
def test_apologies_are_waved_away_kindly(setup, message):
    assert "no worries" in free(setup, message).lower()


@pytest.mark.parametrize("message", ["you are great", "you're awesome", "good bot", "nice work", "well done", "great job",
                                     "you're really helpful"])
def test_compliments_are_received_graciously(setup, message):
    assert "thank you" in free(setup, message).lower()


@pytest.mark.parametrize("message", ["hello?", "are you there", "anyone there", "are you still there"])
def test_are_you_there_gets_a_yes(setup, message):
    assert "here" in free(setup, message).lower()


@pytest.mark.parametrize("message", ["how is your day going", "how was your day", "how's your day"])
def test_asking_about_the_assistants_day_gets_a_friendly_answer(setup, message):
    assert "asking" in free(setup, message).lower()


@pytest.mark.parametrize("message", ["good morning, tell me about Alpha Residences", "okay, tell me about Alpha Residences",
                                     "great, where is Alpha Residences?"])
def test_a_social_opener_followed_by_a_real_question_is_still_a_real_question(setup, message):
    client, llm = setup
    before = len(llm.received_prompts)
    chat(client, message)
    assert len(llm.received_prompts) == before + 1  # went down the normal path
