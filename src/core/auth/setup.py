from typing import Annotated

from fastapi import Request, WebSocket

from dishka import FromComponent, Scope, provide
from dishka.integrations.fastapi import FastapiProvider

from src.core.auth.jwt import JWTAuthBackend
from src.core.auth.schemas import UserInfo
from src.core.config import Config


class BaseAuthProvider(FastapiProvider):

    @provide(scope=Scope.APP)
    async def get_auth_backend(
        self,
        config: Annotated[Config, FromComponent()]
    ) -> JWTAuthBackend:
        return JWTAuthBackend(
            secret_key=config.jwt.secret_key,
            algorithm=config.jwt.algorithm,
        )

class RequestAuthProvider(BaseAuthProvider):
    scope: Scope = Scope.REQUEST
    component: str = "request_auth"

    @provide
    async def get_current_user(
        self,
        request: Annotated[
            Request,
            FromComponent("request_auth"),
        ],
        backend: JWTAuthBackend,
    ) -> UserInfo:
        return await backend(request)


class SessionAuthProvider(BaseAuthProvider):
    scope: Scope = Scope.SESSION
    component: str = "session_auth"

    @provide
    async def get_current_user(
        self,
        websocket: Annotated[
            WebSocket,
            FromComponent("session_auth")
        ],
        backend: JWTAuthBackend,
    ) -> UserInfo:
        return await backend(websocket)



CurrentUser = Annotated[UserInfo, FromComponent("request_auth")]
CurrentUserWS = Annotated[UserInfo, FromComponent("session_auth")]