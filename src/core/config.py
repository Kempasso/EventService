import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator, Field
from dotenv import dotenv_values


_supported_extensions = (".json", ".env")

class BaseConfig(BaseModel):
    @classmethod
    def parse(cls, filename: str):
        data = cls._load_file(Path(filename))
        return cls.model_validate(data)

    @field_validator("*", mode="before")
    @classmethod
    def _validate_model_field(cls, value: Any):
        if isinstance(value, str):
            path = Path(value)
            if path.suffix in _supported_extensions:
                return cls._load_file(path)
        return value

    @staticmethod
    def _load_file(path: Path) -> dict:
        match path.suffix:
            case '.json':
                return json.loads(path.read_text())
            case '.env':
                envs = dotenv_values(path)
                envs.update({k.lower(): v for k, v in envs.items()})
                return envs
            case _:
                raise ValueError(
                    f"Unsupported file extension: {path.suffix}"
                )

class RabbitConfig(BaseConfig):
    host: str
    port: int
    user: str
    password: str
    actions: list[str] = ["created", "updated", "deleted"]
    exchange: str = "events"

    @property
    def rabbit_uri(self):
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"

class RedisConfig(BaseConfig):
    host: str
    port: int
    password: str
    max_connections: int = 30

    @property
    def redis_uri(self):
        return f"redis://:{self.password}@{self.host}:{self.port}"

class DatabaseConfig(BaseConfig):
    host: str
    port: int
    user: str = Field(validation_alias="mongo_user")
    password: str = Field(validation_alias="mongo_password")
    db_name: str = Field(default="main", validation_alias="mongo_db")

    @property
    def mongo_uri(self):
        return f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}"

    @property
    def db_uri(self):
        return (
            f"mongodb://{self.user}:"
            f"{self.password}@"
            f"{self.host}:"
            f"{self.port}/"
            f"{self.db_name}?authSource=admin"
        )


class JwtConfig(BaseConfig):
    secret_key: str
    algorithm: str = "HS256"
    ttl_minutes: int = 30
    bcrypt_rounds: int = 12


class Config(BaseConfig):
    jwt: JwtConfig
    redis: RedisConfig
    rabbit: RabbitConfig
    database: DatabaseConfig