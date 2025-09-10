from dishka import make_async_container

from src.core.provider import CORE_PROVIDERS

container = make_async_container(
    *CORE_PROVIDERS
)