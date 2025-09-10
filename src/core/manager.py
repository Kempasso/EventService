from typing import AsyncIterator, TYPE_CHECKING

from dishka import Provider, provide, Scope

if TYPE_CHECKING:
    from src.services.auth.service import AuthService
    from src.services.events.service import EventService


class ServiceManager:
    auth: 'AuthService'
    event: 'EventService'

    def __init__(self):
        from src.services.auth.service import AuthService
        from src.services.events.service import EventService
        self.auth = AuthService()
        self.event = EventService()


class ServiceManagerProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_service_manager(self) -> AsyncIterator[ServiceManager]:
        yield ServiceManager()