"""Understand structured listing questions ("cheapest 3-bedroom apartment for sale in Riyadh") without an LLM."""
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

_NUMBER_WORDS = {"studio": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
_BEDS_DIGITS = re.compile(r"(\d+)\s*[- ]?\s*(?:bed(?:room)?s?|br)\b", re.IGNORECASE)
_MAX = re.compile(r"(?:under|below|less than|up to|within|at most|maximum|max|cheaper than)\s*(?:sar\s*)?([\d][\d,\.]*)\s*(million|m|thousand|k)?\b", re.IGNORECASE)
_MIN = re.compile(r"(?:over|above|more than|at least|minimum|min)\s*(?:sar\s*)?([\d][\d,\.]*)\s*(million|m|thousand|k)?\b", re.IGNORECASE)
_SORTS = [
    (re.compile(r"cheapest|lowest[- ]priced?|lowest price|least expensive|most affordable", re.IGNORECASE), "price_asc"),
    (re.compile(r"most expensive|highest[- ]priced?|highest price|priciest", re.IGNORECASE), "price_desc"),
    (re.compile(r"largest|biggest|most spacious", re.IGNORECASE), "area_desc"),
    (re.compile(r"smallest|least spacious", re.IGNORECASE), "area_asc"),
]
# Property-type words a visitor might use; asking for one the data lacks must not be silently ignored.
_TYPE_WORDS = ("villa", "apartment", "floor", "land", "studio", "office", "shop", "warehouse", "building", "farm",
               "chalet", "duplex", "townhouse", "house", "compound", "hotel", "showroom")
# "how many" is a listing count only when the question is clearly about listings, so that
# "how many floors does <project> have?" is left to the normal path.
_COUNT = re.compile(r"\bhow many\b", re.IGNORECASE)
_ABOUT_LISTINGS = re.compile(r"\b(listings?|propert(?:y|ies)|wasalt|for sale|for rent|rentals?|do you have|available)\b", re.IGNORECASE)
# A plain listing request ("what 3-bedroom listings do you have in Riyadh?") needs an explicit listing cue, so that
# DarGlobal project questions ("which projects are in Riyadh?", "what is available at Neptune?") are left alone.
_LISTING_REQUEST = re.compile(r"\b(listings?|for sale|for rent|to rent|to buy|rentals)\b", re.IGNORECASE)
_PHOTO_REQUEST = re.compile(r"\b(images?|photos?|pictures?|pics?)\b", re.IGNORECASE)
_MONEY = re.compile(r"\b(sar|riyals?|million|thousand)\b|\d\s*[mk]\b", re.IGNORECASE)
_PLACE = re.compile(r"\b(?:in|at|near|around)\s+([A-Za-z][\w'\-]*(?:\s+[A-Za-z][\w'\-]*){0,3})", re.IGNORECASE)
_PLACE_STOP = {"for", "under", "below", "over", "above", "with", "or", "and", "that", "which", "to", "from", "by",
               "the", "a", "an", "of", "sale", "rent", "price", "sar", "million", "bedrooms", "bedroom", "listing",
               "listings", "my", "total", "general", "please"}
_COUNTRY = {"saudiarabia", "ksa", "kingdom", "thekingdom", "saudi"}


@dataclass(frozen=True)
class ListingQuery:
    cities: tuple[str, ...] = ()
    districts: tuple[str, ...] = ()
    types: tuple[str, ...] = ()
    kind: str | None = None  # "sale" | "rent"
    bedrooms: int | None = None
    max_price: float | None = None
    min_price: float | None = None
    sort: str | None = None  # price_asc | price_desc | area_desc | area_asc
    unavailable: tuple[str, ...] = ()  # things the visitor asked for that the data does not have
    count: bool = False  # "how many ...": answer with a count instead of a list


def _amount(number: str, unit: str | None) -> float:
    value = float(number.replace(",", "").rstrip("."))
    unit = (unit or "").lower()
    if unit in ("million", "m"):
        return value * 1_000_000
    if unit in ("thousand", "k"):
        return value * 1_000
    return value


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _mentions(name: str, lowered: str) -> bool:
    """Whole-name match where spaces and hyphens are interchangeable ("Al-Arid" == "Al Arid")."""
    parts = [re.escape(p) for p in re.split(r"[\s\-]+", name.strip()) if p]
    return bool(parts) and re.search(r"\b" + r"[\s\-]*".join(parts) + r"\b", lowered, re.IGNORECASE) is not None


def _unknown_places(question: str, known: set[str]) -> list[str]:
    unknown = []
    for match in _PLACE.finditer(question):
        words = []
        for word in match.group(1).split():
            if word.lower() in _PLACE_STOP or word[0].isdigit():
                break
            words.append(word)
        phrase = " ".join(words)
        normalised = _norm(phrase)
        if not normalised or normalised in _COUNTRY or any(k and k in normalised for k in known):
            continue
        unknown.append(phrase)
    return unknown


def parse_listing_query(
    question: str, cities: Iterable[str], types: Iterable[str], districts: Iterable[str] = ()
) -> ListingQuery | None:
    """Return a structured query, or None when the question is not a ranking/price-bound listing question."""
    lowered = question.lower()
    sort = next((name for pattern, name in _SORTS if pattern.search(question)), None)
    max_match, min_match = _MAX.search(question), _MIN.search(question)
    counting = bool(_COUNT.search(question) and _ABOUT_LISTINGS.search(question))
    cities, types, districts = list(cities), list(types), list(districts)

    bedrooms = None
    if match := _BEDS_DIGITS.search(question):
        bedrooms = int(match.group(1))
    elif match := re.search(r"\b(" + "|".join(_NUMBER_WORDS) + r")[- ]?(?:bed(?:room)?s?|br)\b|\bstudio\b", question, re.IGNORECASE):
        bedrooms = _NUMBER_WORDS[(match.group(1) or "studio").lower()]

    kind = None
    if re.search(r"\b(for rent|rent|rental|rentals|to rent)\b", lowered):
        kind = "rent"
    elif re.search(r"\b(for sale|buy|purchase|to buy|sale)\b", lowered):
        kind = "sale"

    found_types = tuple(t for t in types if re.search(rf"\b{re.escape(t.lower())}s?\b", lowered))
    found_cities = tuple(c for c in cities if _mentions(c, lowered))
    found_districts = tuple(d for d in districts if _mentions(d, lowered))

    # A photo request ("images of 11 bedroom villas") is a listing search once it names real listing criteria.
    photo_request_with_criteria = bool(
        _PHOTO_REQUEST.search(question) and (bedrooms is not None or kind or found_cities or found_districts)
    )
    listing_request = bool(_LISTING_REQUEST.search(question)) or photo_request_with_criteria
    if not (sort or max_match or min_match or counting or listing_request):
        return None

    # A sort word alone ("the biggest residences at Marea") is not a listing question: require real listing context.
    mentions_a_type = any(re.search(rf"\b{word}s?\b", lowered) for word in _TYPE_WORDS)
    has_context = bool(
        found_types or found_cities or found_districts or kind or mentions_a_type
        or _ABOUT_LISTINGS.search(question) or _MONEY.search(question)
    )
    if not has_context:
        return None
    unavailable = [
        word for word in _TYPE_WORDS
        if re.search(rf"\b{word}s?\b", lowered) and not any(word in t.lower() for t in types)
    ]
    if bedrooms == 0 and "studio" in unavailable:
        unavailable.remove("studio") if found_types else None  # "studio" doubles as a bedroom count
    known_places = {_norm(c) for c in cities} | {_norm(d) for d in districts}
    unavailable += _unknown_places(question, known_places)

    return ListingQuery(
        cities=found_cities,
        districts=found_districts,
        types=found_types,
        kind=kind,
        bedrooms=bedrooms,
        max_price=_amount(*max_match.groups()) if max_match else None,
        min_price=_amount(*min_match.groups()) if min_match else None,
        sort=sort or ("price_asc" if (max_match or min_match) else None),  # no ordering is claimed unless asked for
        unavailable=tuple(dict.fromkeys(unavailable)),
        count=counting and not sort,
    )
