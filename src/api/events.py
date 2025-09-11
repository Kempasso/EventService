from datetime import datetime, timezone
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Query
from starlette.responses import JSONResponse

from dishka.integrations.fastapi import FromDishka, DishkaRoute

from src.core.auth.setup import CurrentUser
from src.core.brokers.rabbitmq import RabbitMqPublisher
from src.core.exception.custom import UserError
from src.core.exception.reason import Reason
from src.core.manager import ServiceManager
from src.core.schemas import TableRequest
from src.services.events.messages import EventMessage
from src.services.events.schemas import (
    EventCreate, EventResponse, EventListFilters, EventUpdate
)
from src.services.redis.service import RedisService

router = APIRouter(
    prefix="/v1/events", tags=["events"], route_class=DishkaRoute
)


@router.post("/")
async def create_event(
    user: CurrentUser,
    manager: FromDishka[ServiceManager],
    publisher: FromDishka[RabbitMqPublisher],
    request: EventCreate
) -> EventResponse:
    event_data = await manager.event.create_event(
        user_id=user.user_id, request=request
    )
    event_message = EventMessage(
        id=str(event_data.id), title=event_data.title, action="created",
        timestamp=datetime.now(tz=timezone.utc),
        user_id=str(event_data.created_by.id)
    )
    await publisher.publish(
        event_message.model_dump(),
        "events.created",
    )
    return event_data


@router.get("/{event_id}")
async def get_event(
    _: CurrentUser,
    manager: FromDishka[ServiceManager],
    event_id: str
) -> EventResponse:
    return await manager.event.get_by_id(event_id)


@router.get("/")
async def list_events(
    _: CurrentUser,
    manager: FromDishka[ServiceManager],
    request: Annotated[TableRequest[EventListFilters], Query()]
):
    return await manager.event.list_events(request=request)


@router.patch("/{event_id}")
async def update_event(
    _: CurrentUser,
    manager: FromDishka[ServiceManager],
    publisher: FromDishka[RabbitMqPublisher],
    event_id: str,
    request: EventUpdate
) -> EventResponse:
    event_data = await manager.event.update_by_id(
        event_id=event_id, request=request
    )
    event_message = EventMessage(
        id=str(event_data.id),
        title=event_data.title,
        action="updated",
        timestamp=datetime.now(tz=timezone.utc),
        user_id=str(event_data.created_by.id)
    )
    await publisher.publish(
        event_message.model_dump(), "events.updated"
    )
    return event_data


@router.delete("/{event_id}")
async def delete_event(
    _: CurrentUser,
    manager: FromDishka[ServiceManager],
    publisher: FromDishka[RabbitMqPublisher],
    event_id: str
):
    event_data = await manager.event.delete_by_id(event_id=event_id)
    event_message = EventMessage(
        id=str(event_data.id),
        title=event_data.title,
        action="deleted",
        timestamp=datetime.now(tz=timezone.utc),
        user_id=str(event_data.created_by.id)
    )
    await publisher.publish(
        event_message.model_dump(), "events.deleted"
    )
    return event_data

@router.post("/{event_id}/subscribe")
async def subscribe(
    user: CurrentUser,
    manager: FromDishka[ServiceManager],
    redis_service: FromDishka[RedisService],
    event_id: str
):
    if not await manager.event.get_by_id(event_id):
        raise UserError(Reason.EVENT_NOT_FOUND)

    await manager.event.subscribe(
        user_id=user.user_id, event_id=event_id, redis=redis_service
    )
    return JSONResponse(content={"success": True}, status_code=HTTPStatus.OK)