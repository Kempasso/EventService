import json

from faststream.rabbit import RabbitBroker, RabbitExchange

class RabbitPublisher:
    def __init__(
        self, broker: RabbitBroker, exchange: RabbitExchange
    ):
        self._broker = broker
        self._exchange = exchange

    async def publish(self, message: dict, routing_key: str) -> None:
        await self._broker.publish(
            message=json.dumps(message).encode(),
            routing_key=routing_key,
            exchange=self._exchange,
            content_type="application/json"
        )