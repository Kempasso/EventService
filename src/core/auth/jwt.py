from dataclasses import dataclass, field

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer
import jwt
from starlette.requests import HTTPConnection

from src.core.auth.schemas import UserInfo


@dataclass
class JWTAuthBackend:
    secret_key: str
    algorithm: str

    _security: HTTPBearer = field(default_factory=HTTPBearer, init=False)

    async def __call__(self, request: HTTPConnection) -> UserInfo:
        creds = await self._security(request)
        try:
            token = creds.credentials
            payload = jwt.decode(
                jwt=token, key=self.secret_key, algorithms=[self.algorithm]
            )
            return UserInfo.model_validate(payload)

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )