from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator
from beanie import BeanieObjectId

from src.core.exception.custom import UserError
from src.core.exception.reason import Reason


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r'^[A-Za-z0-9_]+$'
    )
    password: str = Field(
        min_length=8,
        max_length=100
    )
    full_name: Optional[str] = None

    @field_serializer("email", "username")
    def make_lower(self, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator("password", mode="before")
    @classmethod
    def check_password(cls, v):
        if not any(c.isupper() for c in v):
            raise UserError(Reason.UPPER_PASSWORD)
        if not any(c.isdigit() for c in v):
            raise UserError(Reason.DIGIT_PASSWORD)
        if not any(not c.isalnum() for c in v):
            raise UserError(Reason.CHAR_PASSWORD)
        return v

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str

class ObjId(BaseModel):
    id: BeanieObjectId

class UserResponse(ObjId):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class MeResponse(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None