"""Ticket 15 - per-IP rate limiting, observed at the chat API edge with a controllable clock."""
import pathlib

from fastapi.testclient import TestClient

from dar.adapters.llm import ScriptedLLM
from dar.main import create_app

CORPUS = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "corpus.json"


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def make(limit=3):
    clock = Clock()
    app = create_app(corpus_path=CORPUS, llm=ScriptedLLM(reply="ok"), rate_limit_per_minute=limit, clock=clock)
    return TestClient(app), clock


def post(client, ip="9.9.9.9", message="Alpha Residences"):
    return client.post("/api/chat", json={"message": message, "history": []}, headers={"X-Forwarded-For": ip})


def test_requests_over_the_limit_get_a_friendly_429_with_retry_hint():
    client, _ = make(limit=3)
    assert [post(client).status_code for _ in range(3)] == [200, 200, 200]

    blocked = post(client)
    assert blocked.status_code == 429
    assert "wait" in blocked.json()["detail"].lower()
    assert int(blocked.headers["Retry-After"]) > 0


def test_the_limit_resets_after_the_window_passes():
    client, clock = make(limit=2)
    post(client), post(client)
    assert post(client).status_code == 429
    clock.now += 61
    assert post(client).status_code == 200


def test_each_visitor_has_their_own_allowance():
    client, _ = make(limit=1)
    assert post(client, ip="1.1.1.1").status_code == 200
    assert post(client, ip="1.1.1.1").status_code == 429
    assert post(client, ip="2.2.2.2").status_code == 200


def test_a_spoofed_leading_forwarded_address_does_not_buy_extra_requests():
    client, _ = make(limit=1)  # the trusted proxy appends the real address LAST
    assert post(client, ip="6.6.6.6, 8.8.8.8").status_code == 200
    assert post(client, ip="7.7.7.7, 8.8.8.8").status_code == 429


def test_health_checks_are_never_rate_limited():
    client, _ = make(limit=1)
    assert all(client.get("/api/health").status_code == 200 for _ in range(10))
