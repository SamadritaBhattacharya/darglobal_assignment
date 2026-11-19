"""Ticket 11 - the LLM gateway at its edge: text in, text out, or a typed failure.

Only the network is faked (httpx MockTransport). We assert the visible outcome and what went over the wire.
"""
import json

import httpx
import pytest

from dar.adapters.openrouter import OpenRouterLLM
from dar.domain.ports import LLMUnavailable


def ok(text: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


class Wire:
    """Scripted OpenRouter: a list of responses (or exceptions) consumed in order; records requests."""

    def __init__(self, *script):
        self.script = list(script)
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    @property
    def models_tried(self):
        return [json.loads(r.content)["model"] for r in self.requests]


def gateway(wire: Wire, models=("m/one:free", "m/two:free", "m/three:free"), **kw):
    return OpenRouterLLM(api_key="test-key", models=list(models), transport=httpx.MockTransport(wire),
                         sleep=lambda _s: None, **kw)


def test_returns_the_first_models_answer_and_sends_key_model_and_prompt():
    wire = Wire(ok("Hello there"))
    assert gateway(wire).complete("What is Neptune?") == "Hello there"

    request = wire.requests[0]
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer test-key"
    body = json.loads(request.content)
    assert body["model"] == "m/one:free"
    assert "What is Neptune?" in json.dumps(body["messages"])


def test_a_rate_limited_model_hands_over_to_the_next_one_immediately():
    wire = Wire(httpx.Response(429, json={"error": "rate limited"}), ok("from two"))
    assert gateway(wire).complete("hi") == "from two"
    assert wire.models_tried == ["m/one:free", "m/two:free"]


def test_a_transient_server_error_is_retried_on_the_same_model_first():
    wire = Wire(httpx.Response(503), ok("recovered"))
    assert gateway(wire).complete("hi") == "recovered"
    assert wire.models_tried == ["m/one:free", "m/one:free"]


def test_timeouts_and_empty_answers_move_to_the_next_model():
    wire = Wire(httpx.ReadTimeout("slow"), httpx.ReadTimeout("slow"), ok("   "), ok("third time lucky"))
    assert gateway(wire).complete("hi") == "third time lucky"
    assert wire.models_tried[-1] == "m/three:free"


def test_when_every_model_fails_a_typed_error_is_raised():
    wire = Wire(*[httpx.Response(429)] * 3)
    with pytest.raises(LLMUnavailable):
        gateway(wire).complete("hi")
    assert len(wire.requests) == 3


def test_a_total_time_budget_stops_the_chain_so_the_visitor_is_not_kept_waiting():
    now = {"t": 0.0}

    def slow(request):
        now["t"] += 30  # every attempt burns 30 seconds, then times out
        raise httpx.ReadTimeout("slow")

    llm = OpenRouterLLM(api_key="k", models=["a:free", "b:free", "c:free", "d:free"],
                        transport=httpx.MockTransport(slow), sleep=lambda _s: None,
                        budget_seconds=45, clock=lambda: now["t"])
    with pytest.raises(LLMUnavailable):
        llm.complete("hi")
    assert now["t"] <= 90  # gave up after the second attempt, not after all eight


def test_without_an_api_key_it_fails_cleanly_and_makes_no_network_call():
    wire = Wire()
    llm = OpenRouterLLM(api_key="", models=["m/one:free"], transport=httpx.MockTransport(wire), sleep=lambda _s: None)
    with pytest.raises(LLMUnavailable):
        llm.complete("hi")
    assert wire.requests == []
