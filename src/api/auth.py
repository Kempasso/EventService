from functools import wraps
from typing import Annotated

from fastapi import APIRouter
from dishka.integrations.fastapi import DishkaRoute
from dishka import FromComponent

from src.core.application.utils import rate_limiter
from src.core.auth.setup import CurrentUser
from src.core.manager import ServiceManager
from src.services.auth.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, MeResponse, UserResponse
)

router = APIRouter(
    prefix="/v1/auth", tags=["auth"], route_class=DishkaRoute
)


@router.post("/register")
async def register(
    manager: Annotated[
        ServiceManager,
        FromComponent("")
    ],
    request: RegisterRequest
) -> UserResponse:
    return await manager.auth.create_user(request=request)

@router.post("/login")
@rate_limiter(count=10, minutes=1)
async def login(
    manager: Annotated[
        ServiceManager,
        FromComponent("")
    ],
    request: LoginRequest
) -> TokenResponse:
    return await manager.auth.login(request=request)

@router.get("/me")
async def me(
    manager: Annotated[
        ServiceManager,
        FromComponent("")
    ],
    user: CurrentUser
) -> MeResponse:
    """
    Provides information about the current user.
    """
    return await manager.auth.get_user_info(user.user_id)
