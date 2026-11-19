from __future__ import annotations

from typing import Protocol

from dar.domain.listing_query import ListingQuery
from dar.domain.models import Chunk


class LLMUnavailable(Exception):
    """Raised when no model in the chain could answer.

    reason says why, so the visitor can be told: "rate_limited" (free daily limit reached), "timeout",
    "not_configured" (no usable API key) or "unavailable" (anything else, e.g. a provider outage).
    """

    def __init__(self, message: str = "", reason: str = "unavailable") -> None:
        super().__init__(message)
        self.reason = reason


class Retriever(Protocol):
    def search(self, query: str, k: int = 5) -> list[Chunk]: ...


class Listings(Protocol):
    """Structured access to the sampled property listings (filter and sort in code)."""

    def cities(self) -> list[str]: ...
    def districts(self) -> list[str]: ...
    def types(self) -> list[str]: ...
    def total(self) -> int: ...
    def find(self, query: ListingQuery, limit: int = 5) -> list[Chunk]: ...
    def count(self, query: ListingQuery) -> int: ...


class Catalog(Protocol):
    """Look pages up by their address (used to open a result the visitor picked)."""

    def by_url(self, url: str) -> list[Chunk]: ...


class LLM(Protocol):
    def complete(self, prompt: str) -> str: ...
