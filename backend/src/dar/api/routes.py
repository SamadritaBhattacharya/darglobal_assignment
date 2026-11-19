from __future__ import annotations

from collections.abc import Callable, Iterator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from dar.domain.models import ChatRequest, Event
from dar.domain.ratelimit import SlidingWindowLimiter

Answer = Callable[[ChatRequest], Iterator[Event]]

TOO_MANY = "You're asking quickly. Please wait a moment and try again."


def client_key(request: Request) -> str:
    """The trusted proxy appends the real address last, so a client-supplied leading value can't be spoofed."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def build_router(answer: Answer, data_as_of: str | None, limiter: SlidingWindowLimiter) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.post("/chat")
    def chat(chat_request: ChatRequest, request: Request):
        allowed, retry_after = limiter.check(client_key(request))
        if not allowed:
            return JSONResponse({"detail": TOO_MANY}, status_code=429, headers={"Retry-After": str(retry_after)})

        def stream() -> Iterator[str]:
            for event in answer(chat_request):
                yield f"data: {event.model_dump_json()}\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream")

    @router.get("/health")
    def health() -> dict[str, str | None]:
        return {"status": "ok", "data_as_of": data_as_of}

    return router
