"""Rate-limiting setup. Identifies by user id when authenticated, else IP."""
import hashlib

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings


def _key_func(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        # SHA-256 of the full token → unique per session, collision-resistant
        digest = hashlib.sha256(auth[7:].encode()).hexdigest()
        return f"bearer:{digest[:32]}"
    return get_remote_address(request)


limiter = Limiter(key_func=_key_func, default_limits=[settings.RATE_LIMIT_DEFAULT])
