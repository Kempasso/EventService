from datetime import datetime
from typing import Optional, Annotated

from beanie import Document, Indexed

class User(Document):
    email: Annotated[str, Indexed(unique=True)]
    username: Annotated[str, Indexed(unique=True)]
    password_hash: str
    full_name: Optional[str] = None
    is_verified: bool = True
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "users"