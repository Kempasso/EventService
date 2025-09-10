from datetime import datetime, timezone, timedelta

import bcrypt
import jwt

from src.core.provider import CoreProvider, core_container
from src.services.auth.models import User
from src.services.auth.repository import AuthRepository
from src.services.auth.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, MeResponse, UserResponse
)

from bson import ObjectId
from pymongo.errors import DuplicateKeyError


class AuthService:

    async def create_user(
        self, request: RegisterRequest
    ) -> UserResponse:
        now = datetime.now(tz=timezone.utc)
        request = request.model_dump()
        request["password_hash"] = self._hash_password(
            plain_pwd=request["password"]
        )
        create_payload = {
            "created_at": now,
            "updated_at": now,
            **request
        }
        async with core_container() as cnt:
            auth_repo = await cnt.get(AuthRepository)
            try:
                user = await auth_repo.create(**create_payload)
                return UserResponse(**user.model_dump())
            except DuplicateKeyError as e:
                raise ValueError("User already exists")

    async def login(self, request: LoginRequest):
        async with core_container() as cnt:
            auth_repo = await cnt.get(AuthRepository)
            user = await auth_repo.find_by_email_or_username(
                username=request.username
            )
            if not user or not self._verify_password(
                plain=request.password, hashed=user.password_hash
            ):
                raise ValueError("Invalid username or password")
            return TokenResponse(
                access_token=self.create_jwt_token(str(user.id))
            )

    async def get_user_info(self, user_id: str) -> MeResponse:
        async with core_container() as cnt:
            auth_repo = await cnt.get(AuthRepository)
            clause = (User.id == ObjectId(user_id))
            if not (user := await auth_repo.get_one(where=clause)):
                raise ValueError("User not found")
            return MeResponse(**user.model_dump())

    def create_jwt_token(
        self, user_id: str, **kwargs
    ) -> str:
        conf = CoreProvider().get_config()
        access_delta = timedelta(conf.jwt.ttl_minutes * 60)
        payload = {
            "user_id": user_id,
            "exp": datetime.now(tz=timezone.utc) + access_delta,
            **kwargs
        }
        return jwt.encode(
            payload, conf.jwt.secret_key, algorithm=conf.jwt.algorithm
        )

    def _hash_password(self, plain_pwd: str) -> str:
        conf = CoreProvider().get_config()
        salt = bcrypt.gensalt(rounds=conf.jwt.bcrypt_rounds)
        return bcrypt.hashpw(plain_pwd.encode("utf-8"), salt).decode("utf-8")

    def _verify_password(self, plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False
