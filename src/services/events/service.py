import math
from src.core.database.utils import parse_filters
from src.core.exception.custom import UserError
from src.core.exception.reason import Reason
from src.core.provider import core_container
from src.core.schemas import TableRequest, TableResponse
from src.services.auth.models import User
from src.services.auth.repository import AuthRepository
from src.services.events.models import Event
from src.services.events.repository import EventRepository
from src.services.events.schemas import (
   EventCreate, EventResponse, EventListFilters, EventUpdate
)

from bson import ObjectId

from src.services.redis.service import RedisService


class EventService:

   async def create_event(
       self, user_id: str, request: EventCreate
   ) -> EventResponse:
      async with core_container() as cnt:
         auth_repo = await cnt.get(AuthRepository)
         event_repo = await cnt.get(EventRepository)
         user = await auth_repo.get_one(where=(User.id == ObjectId(user_id)))
         if not user:
            raise UserError(Reason.USER_NOT_FOUND)
         request.created_by = user
         event = await event_repo.create(**request.model_dump())
         return EventResponse(**event.model_dump())

   async def get_by_id(self, event_id: str) -> EventResponse:
      async with core_container() as cnt:
         event_repo = await cnt.get(EventRepository)
         event = await event_repo.get_one(
            where=(Event.id == ObjectId(event_id)), fetch_links=True
         )
         if not event:
            raise UserError(Reason.EVENT_NOT_FOUND)
         return EventResponse(**event.model_dump())

   async def update_by_id(self, event_id: str, request: EventUpdate) -> EventResponse:
      async with core_container() as cnt:
         event_repo = await cnt.get(EventRepository)
         await event_repo.update(
            where=(Event.id == ObjectId(event_id)),
            **request.model_dump(exclude_none=True)
         )
         event = await event_repo.get_one(
            where=(Event.id == ObjectId(event_id)), fetch_links=True
         )
         return EventResponse(**event.model_dump())

   async def delete_by_id(self, event_id: str) -> EventResponse:
      async with core_container() as cnt:
         event_repo = await cnt.get(EventRepository)
         event = await event_repo.get_one(
            where=(Event.id == ObjectId(event_id))
         )
         if not event:
            raise UserError(Reason.EVENT_NOT_FOUND)
         response = EventResponse(**event.model_dump())
         await event_repo.delete(event)
         return response

   async def list_events(
       self, request: TableRequest[EventListFilters]
   ) -> TableResponse[EventResponse]:
      clause = parse_filters(model=Event, filters=request.filters)
      async with core_container() as cnt:
         event_repo = await cnt.get(EventRepository)
         offset = request.page_size * (request.page - 1)
         events = await event_repo.get_many(
            where=clause, limit=request.page_size, skip=offset, fetch_links=True
         )
         count = await event_repo.count(where=clause)
         return TableResponse(
            page=request.page,
            pages=math.ceil(count / request.page_size),
            total_count=count,
            items=[EventResponse(**event.model_dump()) for event in events]
         )


   async def subscribe(
       self, user_id: str, event_id: str, redis: RedisService
   ) -> None:
      key = f"event:{event_id}:subscribers"
      payload = {"key": key}
      if not await redis.find_keys(key):
         async with core_container() as cnt:
            event_repo = await cnt.get(EventRepository)
            event = await event_repo.get_one(
               where=(Event.id == ObjectId(event_id))
            )
            payload.update(**{"init": True, "expire_at": event.end_time})
      await redis.add_to_set(user_id, **payload)