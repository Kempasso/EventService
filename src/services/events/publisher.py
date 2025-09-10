from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import aio_pika



class Publisher:
    connection: Optional[aio_pika.RobustConnection] = None
    channel: Optional[aio_pika.Channel] = None
    exchange: Optional[aio_pika.Exchange] = None

    async def connect(self, cfg: AppConfig):
        url = f"amqp://{cfg.rabbit.user}:{cfg.rabbit.password}@{cfg.rabbit.host}:{cfg.rabbit.port}/"
        self.connection = await aio_pika.connect_robust(url)
        self.channel = await self.connection.channel(publisher_confirms=False)
        self.exchange = await self.channel.declare_exchange(
            cfg.rabbit.exchange, aio_pika.ExchangeType.TOPIC, durable=True
        )

    async def close(self):
        try:
            if self.connection:
                await self.connection.close()
        finally:
            self.connection = None
            self.channel = None
            self.exchange = None

    async def publish_notification(self, routing_key: str, message: Dict[str, Any]):
        if not self.exchange:
            return  # not connected; optionally log
        body = json.dumps(message, default=str).encode("utf-8")
        msg = aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT, content_type="application/json")
        await self.exchange.publish(msg, routing_key=routing_key)


publisher = Publisher()


def build_event_message(notification_type: str, event: dict, actor_username: str, action: str) -> Dict[str, Any]:
    return {
        "type": "notification",
        "notification_type": notification_type,
        "event": {
            "id": str(event.get("_id")),
            "title": event.get("title"),
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "user": actor_username,
    }
