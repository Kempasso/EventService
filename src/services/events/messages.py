from typing import Literal

from pydantic import BaseModel, field_serializer
from datetime import datetime

class EventMessage(BaseModel):
    id: str
    title: str
    action: str = Literal["created", "updated", "deleted"]
    timestamp: datetime | str
    user_id: str

    @field_serializer("timestamp")
    def serialize_timestamp(self, v: datetime) -> str | datetime:
        if isinstance(v, datetime):
            return v.isoformat()
        return v