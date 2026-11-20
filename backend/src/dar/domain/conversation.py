"""Everyday conversation: greetings, who the assistant is, remembering the visitor's name, and politely
declining questions about how the assistant is built.

Only fires when EVERY sentence of the message is conversation. "Hi, tell me about Neptune" is a real question.
Answers are written from templates: no search and no model call, so they are free and can never leak anything.
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from dar.domain.greetings import greeting_phrase, strip_greeting
from dar.domain.names import extract_name
from dar.domain.pii import redact

_FILLER = r"(?:\s+(?:there|everyone|all|assistant|bot|team|friend))*"
_GREETING = re.compile(
    rf"^(?:hi+|hello+|hey+|hiya|howdy|greetings|yo|good\s+(?:morning|afternoon|evening|day)|morning|afternoon|evening|"
    rf"salam|assalamu?\s+alaikum){_FILLER}$"
)
_ACK_WORD = r"(?:ok|okay|cool|great|nice|alright|awesome|perfect)"
_THANKS = re.compile(
    rf"^(?:{_ACK_WORD}[ ,]+)?(?:thanks|thank\s+you|thx|ty|cheers|much\s+appreciated|appreciate\s+it)"
    rf"(?:\s+(?:so\s+much|a\s+lot|very\s+much))?{_FILLER}$"
)
_BYE = re.compile(r"^(?:bye+|goodbye|good\s+bye|see\s+you(?:\s+(?:later|soon))?|take\s+care|cya)$")
_GOOD_NIGHT = re.compile(r"^(?:good\s*night|night\s+night|nighty\s+night|gn)(?:\s+(?:everyone|all|assistant|bot|team|friend))*$")
_WELL_WISH = re.compile(
    r"^(?:have\s+(?:a|an)\s+(?:nice|great|good|lovely|wonderful|fantastic|amazing)\s+(?:day|evening|night|weekend|one|time)|"
    r"enjoy\s+your\s+(?:day|evening|night|weekend)|have\s+a\s+good\s+one)$"
)
_NICE_TO_MEET = re.compile(r"^(?:(?:it'?s\s+)?(?:nice|pleased|good|lovely|great)\s+to\s+meet\s+you|(?:nice|lovely|great)\s+meeting\s+you)$")
_HOW_ARE_YOU = re.compile(
    r"^(?:how\s+are\s+you(?:\s+doing)?(?:\s+today)?|how\s+is\s+it\s+going|how'?s\s+it\s+going|what'?s\s+up|"
    r"how(?:'?s|\s+is|\s+was)\s+your\s+day(?:\s+going)?|how\s+has\s+your\s+day\s+been)$"
)
_STATUS_GOOD = re.compile(
    r"^(?:(?:i\s*am|i'?m|im)\s+(?:doing\s+)?(?:good|fine|great|well|ok|okay|alright|fantastic|wonderful)(?:\s+(?:thanks|thank\s+you))?|"
    r"(?:doing\s+)?(?:good|fine|great|well)\s+(?:thanks|thank\s+you)|not\s+bad|all\s+good|good\s+thanks)$"
)
_ACK = re.compile(
    r"^(?:ok|okay|k|cool|great|nice|awesome|alright|all\s+right|perfect|wow|sounds\s+good|i\s+see|understood|fine|"
    r"sure|noted|right|makes\s+sense|got\s+it|fair\s+enough|interesting|good|lovely)$"
)
_SORRY = re.compile(r"^(?:sorry(?:\s+about\s+that)?|my\s+bad|oops|apologies|i'?m\s+sorry|im\s+sorry|so\s+sorry)$")
_COMPLIMENT = re.compile(
    r"^(?:(?:you\s*are|you'?re|youre|u\s*r)\s+(?:so\s+|very\s+|really\s+|quite\s+)?(?:great|awesome|amazing|helpful|smart|good|cool|nice|"
    r"the\s+best|wonderful|brilliant|fantastic|clever)|good\s+(?:bot|job|work)|great\s+(?:bot|job|work)|nice\s+(?:bot|job|work)|"
    r"well\s+done|nicely\s+done|excellent|brilliant|bravo|love\s+(?:it|this)|i\s+love\s+(?:it|this))$"
)
_PRESENCE = re.compile(r"^\s*(?:(?:hello|hi|hey)\s*\?+|(?:are\s+you|you)\s+(?:still\s+)?there\s*\??|anyone\s+(?:there|here)\s*\??|hello\s+are\s+you\s+there\s*\??)\s*$", re.IGNORECASE)
_HELP = re.compile(
    r"^(?:what\s+can\s+you\s+do|what\s+do\s+you\s+(?:do|know)|help(?:\s+me)?|can\s+you\s+help(?:\s+me)?|"
    r"how\s+can\s+you\s+help(?:\s+me)?|how\s+(?:do|can)\s+i\s+use(?:\s+this)?)$"
)
_IDENTITY = re.compile(
    r"^(?:who\s+are\s+you|what\s+are\s+you|what(?:\s+is|'?s)\s+your\s+name|your\s+name|may\s+i\s+know\s+your\s+name|"
    r"are\s+you\s+(?:a\s+|an\s+)?(?:bot|robot|human|person|real|real\s+person|ai|chatbot|machine|assistant|real\s+human)|"
    r"who\s+(?:made|built|created|developed|designed|programmed|trained)\s+you|who\s+is\s+your\s+(?:creator|developer|maker|owner))$"
)
_NAME_QUESTION = re.compile(
    r"^(?:(?:do|can|could)\s+you\s+(?:still\s+)?(?:remember|know|recall)\s+(?:my\s+name|who\s+i\s+am)|"
    r"what(?:\s+is|'?s)\s+my\s+name(?:\s+again)?|who\s+am\s+i|say\s+my\s+name|tell\s+me\s+my\s+name|my\s+name|"
    r"what\s+did\s+i\s+(?:say|tell\s+you)\s+my\s+name\s+(?:was|is))$"
)
# Memory of THIS conversation (the page sends it back with every message; nothing is stored on the server).
_KNOWS_ME = re.compile(
    r"^(?:(?:do|can|could)\s+you\s+(?:still\s+)?(?:remember|know|recognise|recognize)\s+me(?:\s+(?:already|yet|still|from\s+before))?|"
    r"remember\s+me|have\s+we\s+(?:talked|spoken|chatted|met)(?:\s+before)?)$"
)
_RECAP_FIRST = re.compile(r"^(?:what\s+(?:was|is)\s+my\s+first\s+(?:question|message)|what\s+did\s+i\s+ask\s+(?:you\s+)?first|my\s+first\s+question)$")
_RECAP_LAST = re.compile(
    r"^(?:what\s+(?:was|is)\s+my\s+(?:last|previous|latest|earlier)\s+(?:question|message)|what\s+did\s+i\s+ask\s+(?:you\s+)?last|"
    r"repeat\s+my\s+last\s+question)$"
)
_RECAP_ALL = re.compile(
    r"^(?:what\s+(?:did|have)\s+i\s+(?:ask|asked|say|said|tell|told|mention|mentioned)(?:\s+you)?"
    r"(?:\s+(?:earlier|before|already|so\s+far|previously|just\s+now|today))?|"
    r"what\s+(?:have\s+we|did\s+we|were\s+we)\s+(?:talked|talk|discussed|discuss|spoken|talking|speaking)(?:\s+about)?"
    r"(?:\s+(?:so\s+far|earlier|before|today))?|"
    r"(?:summari[sz]e|recap)(?:\s+(?:our|this|the))?(?:\s+(?:chat|conversation|discussion))?)$"
)
# Questions about how the assistant is built. Each pattern needs the assistant itself as the subject, so
# "what technology does Alpha Residences use?" (a project question) is NOT matched.
_INTERNALS = [re.compile(p) for p in (
    r"\byour\s+(?:\w+\s+){0,2}(?:architectures?|tools?|tech(?:nology|nologies)?|tech\s*stack|stack|frameworks?|models?|llms?|"
    r"prompts?|instructions?|rules|guidelines|configuration|config|settings|functions?|apis?|database|backend|source|training)\b",
    r"\b(?:architectures?|tools?|technolog\w+|tech\s*stack|stack|frameworks?|models?|llms?|apis?|databases?|functions?)\b"
    r"[^.?!]{0,30}\byou\s+(?:can\s+)?(?:have|use|run|call|rely|are\s+(?:built|made|using|based|running|powered))",
    r"\bare\s+you\s+(?:built|made|based|powered|running|using)\b|\bare\s+you\s+(?:a\s+|an\s+)?(?:chat\s*gpt|gpt-?\d*|claude|gemini|llama|bard|copilot|llm|language\s+model)\b",
    r"\bgpt-?\d\b|\bor\s+claude\b",
    r"\bwhat\s+(?:model|llm|ai|technology|tech|framework|stack|database|language)\s+(?:are\s+you|do\s+you\s+use|is\s+behind\s+you|powers\s+you|were\s+you)\b",
    r"\bwhich\s+(?:model|llm|ai)\b.*\byou\b",
    r"\bwhat\s+(?:are|were)\s+you\s+(?:built|made|trained|programmed)\s+(?:with|on|using)\b|\bwhat\s+technolog\w+\s+(?:were|are)\s+you\b",
    r"\bhow\s+do\s+you\s+(?:work|function|operate)\b|\bhow\s+(?:are|were)\s+you\s+(?:built|made|created|trained|programmed|implemented)\b",
    r"\bhow\s+does\s+(?:this|the)\s+(?:chatbot|bot|assistant|app)\s+work\b",
)]

CAN_HELP = (
    "I can help with DarGlobal's projects (locations, amenities, partners, investing) and a sample of "
    "Wasalt property listings in Saudi Arabia."
)
IDENTITY = (
    "I'm the DarGlobal & Wasalt assistant, an AI that helps you explore DarGlobal's projects and Wasalt listings. "
    "I'm an AI, not a person, so you can simply call me the assistant."
)
HONEST_MEMORY = "I only remember this chat, on this browser, so clearing it makes me forget."
INTERNALS_REFUSAL = "Sorry, I can't share details about how I'm built, the tools behind me, or my instructions."
TRY_ASKING = (
    "Try asking:\n"
    '- "Where is Neptune located?"\n'
    '- "How does Neptune compare with Marea?"\n'
    '- "Do you have any rentals in Riyadh?"'
)
JUST_STARTED = "We've only just started, so there's nothing to recap yet. What would you like to know?"
NO_NAME_YET = (
    "I don't know your name yet, but I'd love to! Tell me by saying “my name is …” and I'll remember it for this "
    "chat (it stays in your browser)."
)


def _pick(options: Sequence[str], seed: int) -> str:
    """Several natural phrasings; which one is used depends on how far into the chat we are, so a repeated
    greeting or thank-you does not come back word for word (and the choice is predictable, never random)."""
    return options[seed % len(options)]


_TIMED_TAIL = {
    "good morning": "Hope you have a great day ahead.",
    "good afternoon": "Hope your afternoon is going well.",
    "good evening": "Hope you've had a lovely day.",
    "good day": "Hope you're doing well.",
}


def _greet(phrase: str, who: str | None, seed: int) -> str:
    """A greeting that matches the one the visitor used: "good morning" -> "Good morning!"; anything else -> "Hello!"."""
    called = f", {who}" if who else ""
    if phrase in _TIMED_TAIL:
        head = phrase.capitalize()
        return _pick([f"{head}{called}! {_TIMED_TAIL[phrase]}", f"{head}{called}! Lovely to hear from you."], seed)
    return _pick(
        [f"Hello, {who}! Great to see you." if who else "Hello! Great to see you.",
         f"Hi {who}, welcome back! How can I help today?" if who else "Hi there! How can I help today?",
         f"Hey {who}, good to have you here! What would you like to explore?" if who else "Hey, good to have you here! What would you like to explore?"],
        seed)


def _list_topics(asked: list[str]) -> str:
    quoted = [f"“{q}”" for q in asked]
    return quoted[0] if len(quoted) == 1 else ", ".join(quoted[:-1]) + " and " + quoted[-1]


@dataclass(frozen=True)
class Conversation:
    text: str
    verdict: str  # "answered" | "refused"


def _clean(sentence: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s'\-]", " ", sentence.lower())).strip()


def _kind(sentence: str) -> str | None:
    text = _clean(sentence)
    if not text:
        return None
    if any(p.search(text) for p in _INTERNALS):
        return "internals"
    if _PRESENCE.match(sentence):  # "hello?" with a question mark means "are you there?", not a greeting
        return "presence"
    for kind, pattern in (("greeting", _GREETING), ("good_night", _GOOD_NIGHT), ("thanks", _THANKS), ("bye", _BYE),
                          ("well_wish", _WELL_WISH), ("nice_to_meet", _NICE_TO_MEET), ("how_are_you", _HOW_ARE_YOU),
                          ("status_good", _STATUS_GOOD), ("compliment", _COMPLIMENT), ("sorry", _SORRY), ("ack", _ACK),
                          ("help", _HELP), ("identity", _IDENTITY), ("name_question", _NAME_QUESTION),
                          ("knows_me", _KNOWS_ME), ("recap_first", _RECAP_FIRST), ("recap_last", _RECAP_LAST),
                          ("recap_all", _RECAP_ALL)):
        if pattern.match(text):
            return kind
    if extract_name(sentence):
        return "name_statement"
    return None


def _kinds(sentence: str) -> list[str] | None:
    """What a sentence is. A greeting stuck to something else ("hi i am Sam") counts as both parts."""
    whole = _kind(sentence)  # e.g. "Hi, assistant" is simply a greeting
    if whole == "name_statement" and strip_greeting(sentence)[0]:
        return ["greeting", whole]  # "hi i am Sam": greet back as well as welcoming them
    if whole:
        return [whole]
    greeted, rest = strip_greeting(sentence)
    if greeted and rest:
        inner = _kind(rest) or ("name_statement" if extract_name(sentence) else None)
        return ["greeting", inner] if inner else None
    return None


def is_conversational(message: str) -> bool:
    """True if every sentence is small talk or a memory question (so it is not a real question to recap)."""
    sentences = [s for s in re.split(r"[.!?\n]+", message) if s.strip()]
    return bool(sentences) and all(_kinds(s) is not None for s in sentences)


def _asked(earlier: Sequence[str]) -> list[str]:
    """The visitor's earlier real questions, tidied for echoing back: no chit-chat, no personal details, short."""
    quoted = []
    for message in earlier:
        if is_conversational(message):
            continue
        text = " ".join(redact(message).text.split())
        quoted.append(text if len(text) <= 110 else text[:110].rsplit(" ", 1)[0] + "…")
    return quoted


def _recall(kind: str, name: str | None, asked: list[str], seed: int) -> str:
    if kind == "recap_first":
        return f"The very first thing you asked me was “{asked[0]}”." if asked else JUST_STARTED
    if kind == "recap_last":
        return f"Your most recent question was “{asked[-1]}”." if asked else JUST_STARTED
    if kind == "recap_all":
        if not asked:
            return JUST_STARTED
        intro = _pick(["Sure! Here's what we've covered so far:", "Of course, here's a quick recap:",
                       "Happy to! So far you've asked me:"], seed)
        listed = "\n".join(f"{i}. “{q}”" for i, q in enumerate(asked[-6:], start=1))
        return f"{intro}\n{listed}\nWould you like to dig into any of these, or ask something new?"

    # knows_me: warm, specific, honest about the limits, and ending by inviting the next step
    if not asked:
        if name:
            return f"Of course, {name}! We've only just started chatting, so there's not much to recall yet. What would you like to know?"
        return ("We haven't talked yet, so there's not much to remember, and I don't know your name yet. "
                "Tell me by saying “my name is …” and I'll remember it for this chat. What would you like to know?")
    topics = _list_topics(asked[-3:])
    if name:
        return _pick([
            f"Of course, {name}! We've already covered {topics}. {HONEST_MEMORY} Want to pick up from there, or explore something new?",
            f"I do, {name}! Earlier you asked about {topics}. {HONEST_MEMORY} Shall we continue with that, or look at something else?",
            f"Absolutely, {name}! So far we've talked about {topics}. {HONEST_MEMORY} What would you like to look at next?",
        ], seed)
    return (f"I do remember our chat: you've asked about {topics}. I don't have your name yet, though. Tell me by saying "
            f"“my name is …” and I'll use it. {HONEST_MEMORY} What would you like to explore next?")


def respond(message: str, name: str | None, earlier: Sequence[str] = ()) -> Conversation | None:
    """A conversational reply, or None if any part of the message is a real question for the knowledge base."""
    sentences = [s for s in re.split(r"[.!?\n]+", message) if s.strip()]
    per_sentence = [_kinds(s) for s in sentences]
    if not per_sentence:
        return None
    kinds: list[str | None] = [k for sentence_kinds in per_sentence for k in (sentence_kinds or [None])]
    if "internals" in kinds:
        # A probe for how the assistant is built is declined wherever it appears, even with friendly chatter around it.
        other_questions = any(k is None for k in kinds)
        text = f"{INTERNALS_REFUSAL} {CAN_HELP}"
        if other_questions:
            text += " If you had another question, please ask it on its own and I'll look it up."
        return Conversation(text=f"{text}\n\n{TRY_ASKING}", verdict="refused")
    if any(k is None for k in kinds):
        return None

    learned = extract_name(message)
    who = learned or name
    seed = len(earlier)  # how far into the chat we are: picks between natural phrasings
    parts: list[str] = []
    seen: set[str] = set()
    for kind in kinds:
        if kind in seen:
            continue
        seen.add(kind)
        if kind == "greeting":
            parts.append(_greet(greeting_phrase(next((s for s in sentences if _kinds(s) and _kinds(s)[0] == "greeting"), "")), who, seed))
        elif kind == "good_night":
            parts.append(_pick([f"Good night{', ' + who if who else ''}! Sleep well.",
                                "Good night! Sweet dreams, and come back any time."], seed))
        elif kind == "well_wish":
            parts.append(_pick(["You too! Have a wonderful day.", "Thank you, and you too!"], seed))
        elif kind == "nice_to_meet":
            parts.append(_pick(["Nice to meet you too! How can I help?", "Nice to meet you too! What would you like to explore?"], seed))
        elif kind == "ack":
            parts.append(_pick(["Glad that helps! Is there anything else you'd like to know?",
                                "Great! What would you like to explore next?",
                                "Perfect. Want to look at another project or a listing?"], seed))
        elif kind == "status_good":
            parts.append(_pick(["Glad to hear it! What would you like to explore today?",
                                "That's great to hear! How can I help?"], seed))
        elif kind == "sorry":
            parts.append(_pick(["No worries at all! What can I help you with?", "No worries, it happens! What would you like to know?"], seed))
        elif kind == "compliment":
            parts.append(_pick(["Thank you, that's kind of you! What else can I help you with?",
                                "Thank you! Happy to help. Is there anything else you'd like to explore?"], seed))
        elif kind == "presence":
            parts.append(_pick(["Yes, I'm here! What would you like to know?", "I'm here! How can I help you?"], seed))
        elif kind == "thanks":
            parts.append(_pick(["You're welcome! Happy to help.",
                                "You're welcome! Let me know if there's anything else.",
                                "You're welcome, my pleasure! Ask me anything else about DarGlobal or Wasalt."], seed))
        elif kind == "bye":
            parts.append(_pick(["Goodbye! Come back any time.", "Take care! I'll be here whenever you need me.",
                                "See you soon! Come back whenever you like."], seed))
        elif kind == "how_are_you":
            parts.append(_pick(["I'm doing well, thank you for asking! How are you?",
                                "All good here, thanks for asking! How about you?"], seed))
        elif kind == "name_statement":
            parts.append(_pick([f"Nice to meet you, {learned}!", f"It's lovely to meet you, {learned}!",
                                f"Great to meet you, {learned}!"], seed))
        elif kind == "name_question":
            parts.append(_pick([f"Your name is {who}, of course!", f"You're {who}. It's nice chatting with you!"], seed)
                         if who else NO_NAME_YET)
        elif kind in ("knows_me", "recap_first", "recap_last", "recap_all"):
            parts.append(_recall(kind, who, _asked(earlier), seed))
        elif kind == "identity":
            parts.append(IDENTITY)
        elif kind == "help":
            parts.append(f"{CAN_HELP} I always show where my answers come from, and I'll say so honestly when something isn't in my data.")
        elif kind == "internals":
            parts.append(f"{INTERNALS_REFUSAL} {CAN_HELP}")

    wants_examples = bool(seen & {"greeting", "how_are_you", "help", "identity", "internals"})
    if wants_examples and "help" not in seen and "internals" not in seen and "identity" not in seen:
        parts.append(CAN_HELP)
    text = " ".join(parts[:1]) + (("\n\n" + "\n\n".join(parts[1:])) if len(parts) > 1 else "")
    if wants_examples:
        text += f"\n\n{TRY_ASKING}"
    return Conversation(text=text, verdict="refused" if "internals" in seen else "answered")
