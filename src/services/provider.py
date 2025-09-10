from typing import AsyncIterator

from dishka import Provider, provide, Scope

from src.services.auth.repository import AuthRepository
from src.services.events.repository import EventRepository


class RepositoryProvider(Provider):
    scope = Scope.REQUEST

    @provide
    async def get_auth_repo(self) -> AsyncIterator[AuthRepository]:
        yield AuthRepository()

    @provide
    async def get_event_repo(self) -> AsyncIterator[EventRepository]:
        yield EventRepository()