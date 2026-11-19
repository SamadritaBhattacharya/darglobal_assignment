from __future__ import annotations

from collections import defaultdict

from dar.domain.models import Chunk


class InMemoryCatalog:
    """Pages by URL. Implements dar.domain.ports.Catalog."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self._pages: dict[str, list[Chunk]] = defaultdict(list)
        for chunk in chunks:
            self._pages[chunk.url].append(chunk)

    def by_url(self, url: str) -> list[Chunk]:
        return list(self._pages.get(url, []))
