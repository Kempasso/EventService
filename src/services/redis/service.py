from datetime import datetime

from redis.asyncio.client import Redis


class RedisService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def add_to_set(
        self, *values, key: str, init=False, expire_at: datetime | None = None
    ):
        await self.redis.sadd(key, *values)
        if init:
            await self.redis.expireat(name=key, when=expire_at)

    async def increment_var(self, key: str):
        return await self.redis.incr(name=key)

    async def set_expire(self, key: str, expire: int):
        await self.redis.expire(name=key, time=expire * 60)

    async def find_keys(self, pattern: str):
        return await self.redis.keys(pattern)
