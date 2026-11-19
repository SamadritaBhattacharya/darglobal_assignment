from __future__ import annotations

import time
from collections.abc import Callable

import httpx

from dar.domain.ports import LLMUnavailable

URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterLLM:
    """OpenRouter chat gateway with an ordered model chain. Implements dar.domain.ports.LLM.

    Per model: a rate limit (429) or client error moves on immediately; a transient failure
    (5xx, timeout, network error, empty text) is retried up to `attempts` times, then moves on.
    If every model fails on the primary key, the whole chain is retried with the fallback key.
    When both keys are exhausted, LLMUnavailable is raised.
    """

    def __init__(
        self,
        api_key: str,
        models: list[str],
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        attempts: int = 2,
        timeout: float = 30.0,
        budget_seconds: float = 45.0,
        clock: Callable[[], float] = time.monotonic,
        fallback_api_key: str = "",
    ) -> None:
        self._keys = [k for k in (api_key, fallback_api_key) if k]  # primary first, secondary as backup
        self._models = models
        self._attempts = attempts
        self._sleep = sleep
        self._budget = budget_seconds
        self._clock = clock
        self._client = httpx.Client(transport=transport, timeout=timeout)

    def complete(self, prompt: str) -> str:
        if not self._keys:
            raise LLMUnavailable("no API key configured", reason="not_configured")
        deadline = self._clock() + self._budget
        outcomes: list[str] = []  # why each failed attempt failed
        for key in self._keys:
            for model in self._models:
                text = self._try_model(key, model, prompt, deadline, outcomes)
                if text:
                    return text
                if self._clock() >= deadline:
                    outcomes.append("timeout")
                    raise LLMUnavailable("the time budget ran out", reason=_most_telling(outcomes))
        raise LLMUnavailable("all models failed on every API key", reason=_most_telling(outcomes))

    def _try_model(self, key: str, model: str, prompt: str, deadline: float, outcomes: list[str]) -> str | None:
        for attempt in range(self._attempts):
            if self._clock() >= deadline:
                return None
            try:
                response = self._client.post(
                    URL,
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                )
            except httpx.TimeoutException:
                outcomes.append("timeout")
                self._backoff(attempt)
                continue
            except httpx.HTTPError:
                outcomes.append("unavailable")
                self._backoff(attempt)
                continue
            if response.status_code == 429:
                outcomes.append("rate_limited")
                return None
            if response.status_code in (401, 403):
                outcomes.append("not_configured")  # the key was refused
                return None
            if 400 <= response.status_code < 500:
                outcomes.append("unavailable")
                return None  # retrying this model will not help
            if response.status_code != 200:
                outcomes.append("unavailable")
                self._backoff(attempt)
                continue
            text = _content(response)
            if text:
                return text
            return None  # an empty answer is not worth retrying
        return None

    def _backoff(self, attempt: int) -> None:
        self._sleep(0.5 * (2**attempt))


_PRIORITY = ["rate_limited", "timeout", "not_configured", "unavailable"]


def _most_telling(outcomes: list[str]) -> str:
    """The reason worth telling the visitor: a rate limit beats a timeout beats a refused key beats a plain outage."""
    return next((r for r in _PRIORITY if r in outcomes), "unavailable")


def _content(response: httpx.Response) -> str:
    try:
        return (response.json()["choices"][0]["message"]["content"] or "").strip()
    except (ValueError, KeyError, IndexError, TypeError):
        return ""
