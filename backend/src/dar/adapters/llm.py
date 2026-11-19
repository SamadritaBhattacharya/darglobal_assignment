from __future__ import annotations

from dar.domain.ports import LLMUnavailable


class ScriptedLLM:
    """Test double for the LLM network boundary. Implements dar.domain.ports.LLM."""

    def __init__(self, reply: str = "", fail: bool = False, fail_reason: str = "unavailable") -> None:
        self._reply = reply
        self._fail = fail
        self._fail_reason = fail_reason
        self.received_prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        if self._fail:
            raise LLMUnavailable("scripted failure", reason=self._fail_reason)
        self.received_prompts.append(prompt)
        return self._reply
