"""Context memory: the assistant can recall what was said earlier in THIS conversation (kept in the visitor's
browser and sent back with each message) and introduce the two companies. Observed at the chat API edge."""
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


def say(who, text):
    return {"role": who, "content": text}


EARLIER = [
    say("user", "Where is Neptune located?"), say("assistant", "Neptune is in North Riyadh."),
    say("user", "Do you have any rentals in Riyadh?"), say("assistant", "Here are the matching listings."),
    say("user", "How does Neptune compare with Marea?"), say("assistant", "Both are villa collections."),
]


def chat(client, message, history=(), profile=None):
    body = {"message": message, "history": list(history)}
    if profile:
        body["profile"] = profile
    r = client.post("/api/chat", json=body)
    assert r.status_code == 200, r.text
    ev = [json.loads(l[6:]) for l in r.text.splitlines() if l.startswith("data: ")]
    return ev[-1]["verdict"], "".join(e["text"] for e in ev if e["type"] == "token"), next(e["sources"] for e in ev if e["type"] == "sources")


# ---------------- "do you remember me?" ----------------
@pytest.mark.parametrize("message", ["do you remember me?", "Do you know me", "remember me?", "have we talked before?", "do you still remember me"])
def test_remembering_the_visitor_uses_their_name_and_what_they_talked_about(setup, message):
    client, llm = setup
    before = len(llm.received_prompts)
    verdict, text, _ = chat(client, message, EARLIER, profile={"name": "Samadrita"})
    assert verdict == "answered"
    assert "Samadrita" in text and "Neptune" in text and "rentals in Riyadh" in text
    assert "couldn't find" not in text.lower()
    assert len(llm.received_prompts) == before  # free: no model call


def test_without_a_name_it_still_remembers_the_conversation(setup):
    _, text, _ = chat(setup[0], "do you remember me?", EARLIER)
    assert "remember" in text.lower() and "Neptune" in text
    assert "my name is" in text.lower()  # and invites the visitor to share a name


def test_with_nothing_said_before_it_says_so_honestly(setup):
    _, text, _ = chat(setup[0], "do you remember me?")
    assert "haven't talked" in text.lower() and "my name is" in text.lower()


def test_it_is_honest_that_it_only_remembers_this_browsers_chat(setup):
    _, text, _ = chat(setup[0], "do you remember me?", EARLIER, profile={"name": "Samadrita"})
    assert "this chat" in text.lower() or "this browser" in text.lower()


# ---------------- the replies read like a person, not a log line ----------------
@pytest.mark.parametrize("history", [EARLIER[:2], EARLIER[:4], EARLIER])
def test_remembering_the_visitor_sounds_warm_and_invites_the_next_step(setup, history):
    _, text, _ = chat(setup[0], "do you remember me?", history, profile={"name": "Samadrita"})
    assert "Samadrita" in text[:70]                           # addressed by name straight away
    assert not text.startswith("Yes, I remember you")         # no stock "Yes, <name>" opening
    assert "So far in this chat you've asked" not in text     # no log-style phrasing
    assert text.rstrip().endswith("?")                        # ends by inviting what to do next


def test_the_wording_varies_so_it_does_not_repeat_word_for_word(setup):
    openings = {chat(setup[0], "do you remember me?", h, profile={"name": "Samadrita"})[1].split("\n")[0][:40]
                for h in (EARLIER[:2], EARLIER[:4], EARLIER)}
    assert len(openings) >= 2


def test_greetings_also_vary_but_always_greet_the_visitor_by_name(setup):
    replies = [chat(setup[0], "hi", h, profile={"name": "Samadrita"})[1] for h in ([], EARLIER[:2], EARLIER[:4], EARLIER)]
    assert len({r.split("\n")[0] for r in replies}) >= 2
    assert all("Samadrita" in r.split("\n")[0] and r.lower().startswith(("hello", "hi", "hey")) for r in replies)


def test_a_recap_is_introduced_naturally(setup):
    _, text, _ = chat(setup[0], "what did I ask you earlier?", EARLIER)
    assert text.startswith(("Sure", "Of course", "Happy to"))
    assert "Here's what you've asked me so far in this chat" not in text


# ---------------- "what did I ask?" ----------------
@pytest.mark.parametrize("message", ["what did I ask you earlier?", "what did i ask before", "what have we talked about?",
                                     "summarize our conversation", "recap", "what were we talking about"])
def test_the_assistant_recaps_the_earlier_questions_in_order(setup, message):
    _, text, _ = chat(setup[0], message, EARLIER)
    assert text.index("Where is Neptune located?") < text.index("rentals in Riyadh") < text.index("compare with Marea")


def test_the_first_question_can_be_asked_for_specifically(setup):
    _, text, _ = chat(setup[0], "what was my first question?", EARLIER)
    assert "Where is Neptune located?" in text and "rentals" not in text


def test_the_last_question_can_be_asked_for_specifically(setup):
    _, text, _ = chat(setup[0], "what was my last question?", EARLIER)
    assert "compare with Marea" in text and "Where is Neptune" not in text


def test_a_recap_before_anything_was_asked_says_we_just_started(setup):
    _, text, _ = chat(setup[0], "what did I ask earlier?")
    assert "just started" in text.lower() or "nothing" in text.lower()


def test_recaps_do_not_list_the_recap_questions_themselves(setup):
    history = EARLIER + [say("user", "what did I ask earlier?"), say("assistant", "Here is what you asked…")]
    _, text, _ = chat(setup[0], "recap", history)
    assert text.lower().count("what did i ask") == 0


def test_personal_details_the_visitor_typed_are_not_echoed_back(setup):
    history = [say("user", "my email is jane.doe@example.com, where is Neptune?"), say("assistant", "North Riyadh.")]
    _, text, _ = chat(setup[0], "what did I ask earlier?", history)
    assert "jane.doe@example.com" not in text and "Neptune" in text


def test_long_questions_are_shortened_in_a_recap(setup):
    history = [say("user", "Tell me about " + "the villas " * 60), say("assistant", "ok")]
    _, text, _ = chat(setup[0], "what did I ask earlier?", history)
    assert len(text) < 700


def test_what_did_i_say_my_name_was_uses_the_remembered_name(setup):
    _, text, _ = chat(setup[0], "what did I say my name was?", EARLIER, profile={"name": "Samadrita"})
    assert "Samadrita" in text


def test_an_ordinary_question_that_resembles_a_recap_is_not_one(setup):
    client, llm = setup
    before = len(llm.received_prompts)
    _, _, cards = chat(client, "What did Alpha Residences announce earlier?", EARLIER)
    assert len(llm.received_prompts) == before + 1 or cards is not None  # went down the normal path, not a recap


# ---------------- "what is Wasalt / DarGlobal?" ----------------
@pytest.fixture(scope="module")
def companies(tmp_path_factory):
    records = [
        {"id": "wasalt:about", "source": "wasalt", "url": "https://wasalt.sa/en", "title": "About Wasalt", "section": "Overview",
         "scraped_at": "2026-11-19T10:00:00Z", "image_url": "https://cdn.wasalt.sa/images/wasalt-logo.svg",
         "text": "Wasalt | About Wasalt | Overview\nFind properties for sale and rent in Saudi Arabia: the Saudi's largest selection of properties.\nSource: Wasalt.sa"},
        {"id": "dg-about-1", "source": "darglobal", "url": "https://darglobal.co.uk/about", "title": "About DarGlobal", "section": "Overview",
         "scraped_at": "2026-11-19T10:00:00Z",
         "text": "DarGlobal | About DarGlobal | Overview\nDarGlobal develops branded luxury residences in partnership with global names."},
    ]
    path = tmp_path_factory.mktemp("c") / "c.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    llm = ScriptedLLM(reply="unused")
    return TestClient(create_app(corpus_path=path, llm=llm, rate_limit_per_minute=100000)), llm


@pytest.mark.parametrize("message", ["what is wasalt?", "What's Wasalt", "who is wasalt", "tell me about wasalt", "what does wasalt do", "wasalt?"])
def test_asking_what_wasalt_is_gets_its_own_description_with_a_card(companies, message):
    client, llm = companies
    before = len(llm.received_prompts)
    verdict, text, cards = chat(client, message)
    assert verdict == "answered" and "largest selection of properties" in text
    assert [c["url"] for c in cards] == ["https://wasalt.sa/en"] and cards[0]["image"]
    assert "wasalt.sa" in text.lower()
    assert len(llm.received_prompts) == before  # free


@pytest.mark.parametrize("message", ["what is darglobal?", "Who is Dar Global", "tell me about darglobal", "what does darglobal do"])
def test_asking_what_darglobal_is_gets_its_own_description_with_a_card(companies, message):
    verdict, text, cards = chat(companies[0], message)
    assert verdict == "answered" and "branded luxury residences" in text
    assert [c["url"] for c in cards] == ["https://darglobal.co.uk/about"]


def test_a_longer_question_that_merely_mentions_a_company_is_not_an_introduction(companies):
    _, text, _ = chat(companies[0], "tell me about wasalt listings in Riyadh")
    assert "largest selection of properties" not in text
