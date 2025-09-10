from typing import AsyncIterator

from dishka import Provider, Scope, provide
from faststream.rabbit import RabbitBroker, RabbitPublisher, RabbitExchange, ExchangeType

from src.core.config import Config


class MessagingProvider(Provider):
    scope = Scope.APP
    _broker: RabbitBroker | None = None

    @provide
    async def get_broker(self, conf: Config) -> RabbitBroker:
        if self._broker is None:
            self._broker = RabbitBroker(conf.rabbit.rabbit_uri)
        return self._broker

    @provide
    async def get_publisher(
        self, broker: RabbitBroker, conf: Config
    ) -> AsyncIterator[RabbitPublisher]:
        exchange = RabbitExchange(
            name=conf.rabbit.exchange, type=ExchangeType.TOPIC,
            durable=True, auto_delete=False, declare=True, robust=True
        )
        publisher = RabbitPublisher(broker=broker, exchange=exchange)
        await self._broker.connect()
        await self._broker.declare_exchange(exchange)
        yield publisher
        await self._broker.stop()