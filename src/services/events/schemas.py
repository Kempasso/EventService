from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from beanie import BeanieObjectId

from src.core.exception.custom import UserError
from src.core.exception.reason import Reason
from src.core.schemas import RangeFilter
from src.services.auth.models import User
from src.services.auth.schemas import UserResponse
from src.services.events.types import EventStatus

class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    location: str = Field(min_length=1)
    start_time: datetime | str
    end_time: datetime | str
    created_by: User | str | None = None
    tags: List[str] = Field(default_factory=list)
    max_attendees: Optional[int] = Field(default=10, gt=0)
    status: EventStatus = EventStatus.scheduled

    @field_validator('start_time', 'end_time', mode='before')
    @classmethod
    def ensure_aware_utc(cls, v):
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v.astimezone(timezone.utc)
        raise UserError(Reason.INVALID_DATETIME)

    @model_validator(mode="after")
    def validate_times(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be greater than start_time")
        now = datetime.now(timezone.utc)
        if self.start_time < now or self.end_time < now:
            raise ValueError("start/end time cannot be in the past")
        return self

class EventUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[EventStatus] = None

class EventResponse(BaseModel):
    id: BeanieObjectId
    title: str
    description: str = Field(..., min_length=1)
    location: str = Field(min_length=1)
    start_time: datetime
    end_time: datetime
    created_by: UserResponse
    tags: List[str]
    max_attendees: int
    status: EventStatus


class EventListFilters(BaseModel):
    start_time: RangeFilter[datetime] | None = None
    end_time: RangeFilter[datetime] | None = None