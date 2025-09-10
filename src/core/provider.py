import os
from typing import AsyncIterator

from dishka import provide, Scope, make_async_container
from dishka.integrations.fastapi import FastapiProvider
from redis.asyncio.client import Redis

from src.core.auth.setup import RequestAuthProvider, SessionAuthProvider
from src.core.brokers.setup import MessagingProvider
from src.services.provider import RepositoryProvider
from src.core.config import Config
from src.core.database.provider import DatabaseConnectionProvider
from src.core.manager import ServiceManagerProvider
from src.services.redis.setup import RedisServiceProvider

CONFIG_DEFAULT_PATH = "settings/config.json"

class CoreProvider(DatabaseConnectionProvider):
    scope: Scope = Scope.APP
    config_path: str = os.getenv("CONFIG_PATH", CONFIG_DEFAULT_PATH)

    def get_config(self) -> Config:
        return Config.parse(self.config_path)

    @provide
    def get_core_config(self) -> Config:
        return self.get_config()

    @provide
    async def get_redis(self, config: Config) -> AsyncIterator[Redis]:
        redis = Redis.from_url(
            config.redis.redis_uri,
            max_connections=config.redis.max_connections
        )
        try:
            yield redis
        finally:
            await redis.aclose()


CORE_PROVIDERS = (
    CoreProvider(),
    ServiceManagerProvider(),
    MessagingProvider(),
    RepositoryProvider(),
    RedisServiceProvider(),
    RequestAuthProvider(),
    SessionAuthProvider(),
    FastapiProvider()
)

core_container = make_async_container(*CORE_PROVIDERS)