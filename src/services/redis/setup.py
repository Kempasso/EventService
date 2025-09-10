from typing import AsyncIterator

from dishka import Provider, Scope, provide
from redis.asyncio.client import Redis

from src.services.redis.service import RedisService


class RedisServiceProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_redis_service(
        self, redis_client: Redis
    ) -> AsyncIterator[RedisService]:
        yield RedisService(redis=redis_client)
