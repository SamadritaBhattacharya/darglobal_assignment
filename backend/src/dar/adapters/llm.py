from __future__ import annotations

from dar.domain.ports import LLMUnavailable


class ScriptedLLM:
    """Test double for the LLM network boundary. Implements dar.domain.ports.LLM."""

    def __init__(self, reply: str = "", fail: bool = False) -> None:
        self._reply = reply
        self._fail = fail
        self.received_prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        if self._fail:
            raise LLMUnavailable("scripted failure")
        self.received_prompts.append(prompt)
        return self._reply
