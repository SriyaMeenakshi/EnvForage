"""Middleware to reject HTTP request bodies exceeding a configurable byte limit."""

# At the top of payload_size.py, add to imports:
import json

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_PAYLOAD_BYTES: int = 1 * 1024 * 1024  # 1 MB


class PayloadSizeLimitMiddleware:
    """
    Reject requests whose body exceeds MAX_PAYLOAD_BYTES.

    Two-layer strategy:
      Layer 1 — Content-Length fast-path:
          Reject immediately if declared Content-Length exceeds limit.
      Layer 2 — Stream guard:
          Count bytes as chunks arrive. Catches lying clients and
          chunked-transfer-encoding requests (no Content-Length).
    """

    def __init__(self, app: ASGIApp, max_bytes: int = MAX_PAYLOAD_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)

        # Layer 1: Content-Length fast-path
        content_length_header = headers.get("content-length")
        if content_length_header is not None:
            try:
                declared_size = int(content_length_header)
            except ValueError:
                declared_size = 0
            if declared_size > self.max_bytes:
                await self._send_413(send)
                return

        # Layer 2: Stream guard
        bytes_seen = 0
        limit_exceeded = False

        async def limited_receive() -> Message:
            nonlocal bytes_seen, limit_exceeded
            message = await receive()
            if message["type"] == "http.request":
                chunk: bytes = message.get("body", b"")
                bytes_seen += len(chunk)
                if bytes_seen > self.max_bytes:
                    limit_exceeded = True
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        async def guarded_send(message: Message) -> None:
            if limit_exceeded:
                if message.get("type") == "http.response.start":
                    await self._send_413(send)
                    return
                if message.get("type") == "http.response.body":
                    return
            await send(message)

        await self.app(scope, limited_receive, guarded_send)
@staticmethod
async def _send_413(send: Send) -> None:
    """Send a structured 413 response matching the API error envelope."""
    await send({
        "type": "http.response.start",
        "status": 413,
        "headers": [
            (b"content-type", b"application/json"),
        ],
    })

    body = json.dumps({
        "error": {
            "code": "PAYLOAD_TOO_LARGE",
            "message": (
                f"Request body exceeds the maximum allowed size "
                f"of {MAX_PAYLOAD_BYTES // (1024 * 1024)} MB."
            ),
        }
    }).encode("utf-8")
    await send({
        "type": "http.response.body",
        "body": body,
        "more_body": False,
    })
