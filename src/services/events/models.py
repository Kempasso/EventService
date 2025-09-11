from datetime import datetime

from beanie import Document, Link
from pydantic import Field

from src.services.auth.models import User
from src.services.events.types import EventStatus


class Event(Document):
    title: str = Field(max_length=100)
    description: str = Field(max_length=500)
    location: str
    start_time: datetime
    end_time: datetime
    created_by: Link[User]
    tags: list[str] = []
    max_attendees: int
    status: EventStatus

    class Settings:
        name = "events"

class EventNotification(Document):
    event_id: str
    user_id: str
    timestamp: datetime