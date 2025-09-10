from enum import StrEnum

class EventStatus(StrEnum):
    scheduled = "scheduled"
    canceled = "canceled"
    completed = "completed"