"""Wasalt saved listing page -> one listing record (pure, no network).

Privacy by construction: only an allow-list of structured property facts is read. Owner, agent,
contact, licence and free-text description fields are never read, so they cannot leak.
"""
from __future__ import annotations

import json
import re

from pydantic import ValidationError

from dar.domain.models import Chunk
from scraper.images import og_image

_NEXT_DATA = re.compile(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.DOTALL)
_PERIOD = {"/year": "per year", "/month": "per month"}


def _number(value) -> float | None:
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _attribute(attributes: list, key: str):
    for item in attributes or []:
        if isinstance(item, dict) and item.get("key") == key:
            return item.get("value")
    return None


def parse_listing(html: str, scraped_at: str) -> Chunk | None:
    match = _NEXT_DATA.search(html or "")
    if not match:
        return None
    try:
        details = json.loads(match.group(1))["props"]["pageProps"]["propertyDetailsV3"]
        info = details["propertyInfo"]
    except (ValueError, KeyError, TypeError):
        return None

    kind = info.get("propertyFor")
    title, slug, listing_id = info.get("title"), info.get("slug"), details.get("id")
    price = _number(info.get("salePrice") if kind == "sale" else info.get("expectedRent"))
    if kind not in ("sale", "rent") or not (title and slug and listing_id and price):
        return None

    attributes = details.get("attributes") or []
    area = _number(_attribute(attributes, "builtUpArea"))
    if area is None:  # some types (e.g. rest houses) keep the size elsewhere, but the title always states it
        in_title = re.search(r"([\d,]+(?:\.\d+)?)\s*SQM", title, re.IGNORECASE)
        area = _number(in_title.group(1)) if in_title else None
    beds_raw = _attribute(attributes, "noOfBedrooms")
    bedrooms = int(beds_raw) if isinstance(beds_raw, (int, float, str)) and str(beds_raw).isdigit() else None

    currency = info.get("currencyType") or "SAR"
    city = info.get("city") or None
    district = info.get("zone") or info.get("district") or None
    ptype = (info.get("propertySubType") or "").strip()
    period = _PERIOD.get(str(info.get("expectedRentType", "")).lower(), "") if kind == "rent" else ""

    place = ", ".join(p for p in (district, city) if p)
    facts = []
    if bedrooms is not None:
        facts.append("studio" if bedrooms == 0 else f"{bedrooms} bedrooms")
    if area:
        facts.append(f"{area:g} sqm")
    facts.append(f"{price:,.0f} {currency}" + (f" {period}" if period else ""))
    sentence = f"{ptype or 'Property'} for {kind}" + (f" in {place}" if place else "") + ". " + ", ".join(facts) + "."

    try:
        return Chunk(
            id=f"wasalt:{listing_id}",
            source="wasalt",
            url=f"https://wasalt.sa/en/property/{kind}/{slug}",
            title=title,
            section="Listing",
            text=f"Wasalt | {title} | Listing\n{sentence}\nSource: Wasalt.sa",
            scraped_at=scraped_at,
            city=city,
            district=district,
            property_type=ptype.lower() or None,
            listing_kind=kind,
            price=price,
            currency=currency,
            price_period=period or None,
            image_url=og_image(html),
            area_sqm=area,
            bedrooms=bedrooms,
        )
    except ValidationError:
        return None  # e.g. personal data detected in a field: skip the listing rather than store it
