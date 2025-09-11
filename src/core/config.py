import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, field_validator, Field
from dotenv import dotenv_values


_supported_extensions = (".json", ".env")

class BaseConfig(BaseModel):
    """Base configuration model that supports nested file references.

    Fields that contain a path to a supported file (.json, .env) will be
    automatically replaced with the parsed content of that file.
    """
    @classmethod
    def parse(cls, filename: str):
        data = cls._load_file(Path(filename))
        return cls.model_validate(data)

    @field_validator("*", mode="before")
    @classmethod
    def _validate_model_field(cls, value: Any):
        """Pydantic hook to load nested files referenced by field values.

        If a string value points to a .json or .env file, the file is loaded
        and the field value is replaced by the parsed data.
        """
        if isinstance(value, str):
            path = Path(value)
            if path.suffix in _supported_extensions:
                return cls._load_file(path)
        return value

    @staticmethod
    def _load_file(path: Path) -> dict:
        """Load configuration data from a .json or .env file.

        Raises:
            ValueError: If the file extension is not supported.
        """
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
    """RabbitMQ-related configuration values."""
    host: str
    port: int
    user: str
    password: str
    actions: list[str] = ["created", "updated", "deleted"]
    exchange: str = "events"

    @property
    def rabbit_uri(self):
        """AMQP URI assembled from host, port, user, and password."""
        return f"amqp://{self.user}:{self.password}@{self.host}:{self.port}/"

class RedisConfig(BaseConfig):
    """Redis-related configuration values."""
    host: str
    port: int
    password: str
    max_connections: int = 30

    @property
    def redis_uri(self):
        """Redis URI assembled from host, port and password."""
        return f"redis://:{self.password}@{self.host}:{self.port}"

class DatabaseConfig(BaseConfig):
    """MongoDB-related configuration values and computed URIs."""
    host: str
    port: int
    user: str = Field(validation_alias="mongo_user")
    password: str = Field(validation_alias="mongo_password")
    db_name: str = Field(default="main", validation_alias="mongo_db")

    @property
    def mongo_uri(self):
        """MongoDB connection URI without database name (for admin/auth)."""
        return f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}"

    @property
    def db_uri(self):
        """MongoDB connection URI targeting a specific database with authSource."""
        return (
            f"mongodb://{self.user}:"
            f"{self.password}@"
            f"{self.host}:"
            f"{self.port}/"
            f"{self.db_name}?authSource=admin"
        )


class JwtConfig(BaseConfig):
    """JWT security configuration values."""
    secret_key: str
    algorithm: str = "HS256"
    ttl_minutes: int = 30
    bcrypt_rounds: int = 12


class Config(BaseConfig):
    """Root application configuration wrapper.

    This model can be parsed from a JSON file where nested fields may point to
    other supported files (see BaseConfig).
    """
    jwt: JwtConfig
    redis: RedisConfig
    rabbit: RabbitConfig
    database: DatabaseConfig
    messages: dict