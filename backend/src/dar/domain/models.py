from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from dar.domain.pii import redact


class Chunk(BaseModel):
    """A processed record / retrievable unit (see TECH_SPEC section 4)."""

    id: str
    source: Literal["darglobal", "wasalt"]
    url: str
    title: str
    section: str
    text: str
    scraped_at: str
    city: str | None = None
    district: str | None = None
    property_type: str | None = None
    listing_kind: Literal["sale", "rent"] | None = None
    price: float | None = None
    currency: str | None = None
    price_period: str | None = None  # "per year" / "per month" for rentals
    area_sqm: float | None = None
    bedrooms: int | None = None
    image_url: str | None = None  # the page's preview photo (public https URL on the source site's own CDN)

    @field_validator("image_url")
    @classmethod
    def _only_secure_urls(cls, value: str | None) -> str | None:
        """Anything that is not a plain https URL (null, relative, javascript:, http:) is dropped, never rendered."""
        return value if value and re.match(r"^https://[^\s\"'<>]+$", value) else None

    @model_validator(mode="after")
    def _reject_personal_data(self) -> "Chunk":
        for name in ("title", "section", "text", "city", "district"):
            value = getattr(self, name)
            if value and redact(value).text != value:
                raise ValueError(f"personal data detected in field '{name}'")
        return self


class TurnSource(BaseModel):
    """A result an earlier answer showed (what the page sends back so "the 1st one" can be resolved)."""

    n: int = Field(ge=1, le=50)
    title: str = Field(max_length=300)
    url: str = Field(max_length=600)


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    sources: list[TurnSource] = Field(default_factory=list, max_length=10)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[Turn] = Field(default_factory=list, max_length=100)


Verdict = Literal["answered", "partial", "dont_know", "refused", "error"]


class StepEvent(BaseModel):
    type: Literal["step"] = "step"
    text: str


class TokenEvent(BaseModel):
    type: Literal["token"] = "token"
    text: str


class SourceRef(BaseModel):
    n: int
    title: str
    url: str
    image: str | None = None  # photo for the card, when the source page has one
    detail: str = ""  # one short line for the card


class SourcesEvent(BaseModel):
    type: Literal["sources"] = "sources"
    sources: list[SourceRef]


class DoneEvent(BaseModel):
    type: Literal["done"] = "done"
    verdict: Verdict


Event = StepEvent | TokenEvent | SourcesEvent | DoneEvent
