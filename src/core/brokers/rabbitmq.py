import json

from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

class RabbitMqPublisher:
    def __init__(
        self,
        broker: RabbitBroker,
        exchange: RabbitExchange,
        queue_map: dict[str, RabbitQueue]
    ):
        self._broker = broker
        self._exchange = exchange
        self._queue_map = queue_map

    async def publish(self, message: dict, routing_key: str) -> None:
        await self._broker.publish(
            message=json.dumps(message).encode(),
            routing_key=routing_key,
            exchange=self._exchange,
            content_type="application/json"
        )