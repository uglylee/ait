import json
import uuid
import asyncio
import aio_pika
import redis.asyncio as aioredis

RABBITMQ_URL = "amqp://ai_rabbit:ai_rabbit_2024@localhost:5672"
REDIS_URL = "redis://:ai_redis_2024@localhost:6379"
QUEUE_LLM = "llm_chat"
QUEUE_AUTO = "llm_auto"

_connection = None
_channel = None


async def get_rabbitmq():
    global _connection, _channel
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(RABBITMQ_URL)
        _channel = await _connection.channel()
        await _channel.declare_queue(QUEUE_LLM, durable=True)
        await _channel.declare_queue(QUEUE_AUTO, durable=True)
    return _channel


async def publish_chat(request_id: str, data: dict):
    channel = await get_rabbitmq()
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(data).encode(), message_id=request_id),
        routing_key=QUEUE_LLM,
    )


async def publish_auto(request_id: str, data: dict):
    channel = await get_rabbitmq()
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(data).encode(), message_id=request_id),
        routing_key=QUEUE_AUTO,
    )


async def publish_result(request_id: str, event: dict):
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        await r.publish(f"llm_result:{request_id}", json.dumps(event))
    finally:
        await r.close()


async def publish_done(request_id: str):
    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        await r.publish(f"llm_result:{request_id}", json.dumps({"_done": True}))
    finally:
        await r.close()


class ResultSubscriber:
    """先订阅 Redis，再发布到 RabbitMQ，确保不丢事件"""

    def __init__(self, request_id: str):
        self.request_id = request_id
        self.queue = asyncio.Queue()
        self._task = None
        self._redis = None
        self._pubsub = None

    async def start(self):
        self._redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        await self._pubsub.subscribe(f"llm_result:{self.request_id}")
        self._task = asyncio.create_task(self._listen())

    async def _listen(self):
        try:
            while True:
                msg = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg["type"] == "message":
                    data = json.loads(msg["data"])
                    await self.queue.put(data)
                    if data.get("_done"):
                        break
        except asyncio.CancelledError:
            pass
        finally:
            try:
                await self._pubsub.unsubscribe(f"llm_result:{self.request_id}")
                await self._pubsub.close()
                await self._redis.close()
            except Exception:
                pass

    async def get(self, timeout: float = 1.0):
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def stop(self):
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
