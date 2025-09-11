from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable

from starlette.responses import JSONResponse
from  pydantic import BaseModel
from src.core.provider import core_container
from src.services.redis.service import RedisService


def rate_limiter(
    *,
    count: int = 5,
    minutes: int = 1,
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """
    Only for login now) I would like to make it more useful, but i have no time))
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            res = await func(*args, **kwargs)
            if not isinstance(res, BaseModel):
                return res
            async with core_container() as cnt:
                redis_service: RedisService = await cnt.get(RedisService)
                body = kwargs.get("request")
                username = getattr(body, "username", None)
                key = f"user:{username}"

                current = await redis_service.increment_var(key)
                if current == 1:
                    await redis_service.set_expire(key, minutes)
                if current >= count:
                    return JSONResponse(content={"error": "Too Many Requests"}, status_code=429)
                return res

        return wrapper
    return decorator