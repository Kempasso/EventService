import asyncio
from contextlib import asynccontextmanager
from typing import Callable, Coroutine, Iterable

from dishka.integrations.fastapi import setup_dishka
from beanie import init_beanie
from fastapi import FastAPI, APIRouter

from src.core.config import Config
from src.services.auth.models import User
from src.container import container
from src.services.events.models import Event


def create(
    *,
    base_router_path: str,
    routers: Iterable[APIRouter],
    startup_tasks: Iterable[Callable[[], Coroutine]] | None = None,
    shutdown_tasks: Iterable[Callable[[], Coroutine]] | None = None,
    **kwargs
) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config = await container.get(Config)
        await init_beanie(
            connection_string=config.database.db_uri,
            document_models=[User, Event]
        )
        if startup_tasks:
            await asyncio.gather(*[task() for task in startup_tasks])
        yield
        if shutdown_tasks:
            await asyncio.gather(*[task() for task in shutdown_tasks])

    app = FastAPI(lifespan=lifespan, **kwargs)

    for router in routers:
        app.include_router(router, prefix=base_router_path)

    # also add exception handlers
    setup_dishka(container, app)
    return app

