"""Bound request bytes before multipart parsing, including chunked requests."""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, limit: int = 5 * 1024 * 1024) -> None:
        self.app, self.limit = app, limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > self.limit:
                await JSONResponse({"error": {"code": "REQUEST_BODY_TOO_LARGE"}}, status_code=413)(
                    scope, receive, send
                )
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        buffered: bytes | None = bytes(body)
        del body

        async def replay() -> Message:
            nonlocal buffered
            if buffered is None:
                return await receive()
            content, buffered = buffered, None
            return {"type": "http.request", "body": content, "more_body": False}

        await self.app(scope, replay, send)
