from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_serializer
from beanie import BeanieObjectId


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    full_name: Optional[str] = None

    @field_serializer("email", "username")
    def make_lower(self, v):
        if isinstance(v, str):
            return v.lower()
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