"""Plain-language answers for structured listing questions, written from data (never by a model)."""
from __future__ import annotations

from dar.app.cards import card_detail
from dar.domain.listing_query import ListingQuery
from dar.domain.models import Chunk

_ORDER = {
    "price_asc": "cheapest first",
    "price_desc": "most expensive first",
    "area_desc": "largest first",
    "area_asc": "smallest first",
}
_LIVE = "Source: Wasalt.sa. Prices and availability change, so please check wasalt.sa for live details."


def render_listings(query: ListingQuery, results: list[Chunk], total: int) -> str:
    order = f", {_ORDER[query.sort]}" if query.sort else ""
    lines = [
        f"Here are the matching Wasalt listings{order}, from my sample of "
        f"{total} Wasalt listings (a snapshot, not the whole site):"
    ]
    for n, c in enumerate(results, start=1):
        beds = "studio" if c.bedrooms == 0 else f"{c.bedrooms} bedrooms" if c.bedrooms is not None else None
        parts = [f"{c.price:,.0f} {c.currency or 'SAR'}" + (f" {c.price_period}" if c.price_period else "")]
        if c.area_sqm is not None:
            parts.append(f"{c.area_sqm:g} sqm")
        if beds:
            parts.append(beds)
        lines.append(f"{n}. {c.title}: {', '.join(parts)} [{n}]")
    return "\n".join(lines) + "\n\n" + _LIVE


def render_passages(chunks: list[Chunk], shown: int = 3) -> str:
    """Used when the language model is unavailable: show the best passages found instead of a dead end."""
    lines = [
        "I'm having trouble reaching my language model right now, so I can't write a full answer. "
        "Here are the most relevant passages I found:"
    ]
    for n, c in enumerate(chunks[:shown], start=1):
        lines.append(f"{n}. {c.title} ({c.section}): {card_detail(c, 260)} [{n}]")
    lines.append("Please try again in a moment for a complete answer.")
    return "\n\n".join(lines)


def render_count(found: int, total: int) -> str:
    noun = "listing" if found == 1 else "listings"
    return (
        f"I found {found} matching {noun} in my sample of {total} Wasalt listings (a snapshot, not the whole site), "
        f"so this is not the total on Wasalt.\n\n{_LIVE}"
    )


def render_closest(query: ListingQuery, results: list[Chunk], total: int) -> str:
    """No listing has the requested bedroom count: say so, then offer what is there without that filter."""
    where = " in " + " or ".join(query.cities + query.districts) if (query.cities or query.districts) else ""
    kind = " for rent" if query.kind == "rent" else " for sale" if query.kind == "sale" else ""
    head = (
        f"I couldn't find a {query.bedrooms}-bedroom listing{kind}{where} in my sample of {total} Wasalt listings. "
        "Here is what I do have (without the bedroom filter):"
    )
    return head + "\n" + render_listings(query, results, total).split("\n", 1)[1]


_OPEN_PAGE = "Press the “Click to know more” button on the card to open the full page"


def render_details(chunks: list[Chunk]) -> str:
    """The details of one picked result, written from its stored fields (no model involved)."""
    first = chunks[0]
    if first.price is not None:  # a Wasalt listing: list its facts
        kind = {"sale": "for sale", "rent": "for rent"}.get(first.listing_kind or "", "")
        place = ", ".join(p for p in (first.district, first.city) if p)
        lines = [f"Here are the details for {first.title}:"]
        lines.append(f"- Type: {(first.property_type or 'property').capitalize()} {kind}".rstrip())
        if place:
            lines.append(f"- Location: {place}")
        if first.bedrooms is not None:
            lines.append("- Bedrooms: studio" if first.bedrooms == 0 else f"- Bedrooms: {first.bedrooms} bedrooms")
        if first.area_sqm:
            lines.append(f"- Size: {first.area_sqm:g} sqm")
        lines.append(f"- Price: {first.price:,.0f} {first.currency or 'SAR'}" + (f" {first.price_period}" if first.price_period else ""))
        return "\n".join(lines) + f"\n\n{_OPEN_PAGE} with all its photos on Wasalt.sa.\n\nSource: Wasalt.sa"
    parts = [f"Here is what I have on {first.title}:"]
    parts += [card_detail(c, 300) for c in chunks[:2] if card_detail(c, 300)]
    return "\n\n".join(parts) + f"\n\n{_OPEN_PAGE} on darglobal.co.uk."


def render_pick_help(shown: int) -> str:
    if shown == 0:
        return ("I don't have a list of results to pick from yet. Ask me something first, for example "
                '"Do you have any rentals in Riyadh?", and then say "open the 1st one".')
    if shown == 1:
        return "I only showed 1 result, so there is just the one to open."
    return f"I only showed {shown} results, so please pick a number from 1 to {shown} (for example “the 2nd one”)."


def render_which_one(shown: int) -> str:
    return (f"I showed {shown} results. Which one would you like to see? Tell me the number, "
            "for example “the 1st one” or “the 2nd one”.")


def render_no_match(total: int) -> str:
    return (
        f"I couldn't find any listings matching that in my sample of {total} Wasalt listings, so I can't say. "
        "Try a different city, size or budget, or check wasalt.sa directly."
    )
