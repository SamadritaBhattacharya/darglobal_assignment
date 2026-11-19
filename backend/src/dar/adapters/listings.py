from __future__ import annotations

from dar.domain.listing_query import ListingQuery
from dar.domain.models import Chunk

_SORT_KEYS = {
    "price_asc": (lambda c: c.price, False),
    "price_desc": (lambda c: c.price, True),
    "area_desc": (lambda c: c.area_sqm or 0, True),
    "area_asc": (lambda c: c.area_sqm if c.area_sqm is not None else float("inf"), False),
}


class InMemoryListings:
    """Filters and sorts structured listing records. Implements dar.domain.ports.Listings."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self._listings = [c for c in chunks if c.price is not None]

    def cities(self) -> list[str]:
        return sorted({c.city for c in self._listings if c.city})

    def districts(self) -> list[str]:
        return sorted({c.district for c in self._listings if c.district})

    def types(self) -> list[str]:
        return sorted({c.property_type for c in self._listings if c.property_type})

    def total(self) -> int:
        return len(self._listings)

    def count(self, query: ListingQuery) -> int:
        return len(self.find(query, limit=len(self._listings)))

    def find(self, query: ListingQuery, limit: int = 5) -> list[Chunk]:
        if query.unavailable:
            return []  # the visitor asked for something the data does not have: never return look-alikes

        def keep(c: Chunk) -> bool:
            return (
                (not query.cities or (c.city or "").lower() in {x.lower() for x in query.cities})
                and (not query.districts or (c.district or "").lower() in {x.lower() for x in query.districts})
                and (not query.types or (c.property_type or "").lower() in {x.lower() for x in query.types})
                and (query.kind is None or c.listing_kind == query.kind)
                and (query.bedrooms is None or c.bedrooms == query.bedrooms)
                and (query.max_price is None or c.price <= query.max_price)
                and (query.min_price is None or c.price >= query.min_price)
            )

        key, descending = _SORT_KEYS[query.sort or "price_asc"]
        return sorted((c for c in self._listings if keep(c)), key=key, reverse=descending)[:limit]
