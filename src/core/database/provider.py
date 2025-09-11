from typing import AsyncIterator

from dishka import provide, Provider, Scope
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.core.config import Config
from src.core.repository import BeanieRepository


class DatabaseConnectionProvider(Provider):
    scope: Scope = Scope.APP

    @provide
    async def get_motor_client(
        self, conf: Config
    ) -> AsyncIterator[AsyncIOMotorClient]:
        """
        Provides a database client for the application.
        """
        client = AsyncIOMotorClient(
            conf.database.mongo_uri, uuidRepresentation="standard"
        )
        try:
            yield client
        finally:
            if client and client.is_connected:
                client.close()


    @provide
    async def get_database(
        self, client: AsyncIOMotorClient, conf: Config
    ) -> AsyncIOMotorDatabase:
        """ Provides a database. """
        return client[conf.database.db_name]


    @provide(scope=Scope.REQUEST)
    async def get_repository[TItem](
        self, model: TItem
    ) -> BeanieRepository[TItem]:
        """ Provides a repository."""
        return BeanieRepository[TItem](model)
