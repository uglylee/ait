import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from mq import RABBITMQ_URL, QUEUE_LLM, publish_result, publish_done
from llm_config import get_llm_router

import aio_pika


async def handle_chat_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        request_id = data["request_id"]
        messages = data["messages"]
        provider = data.get("provider")
        model = data.get("model")
        enable_thinking = data.get("enable_thinking", True)

        router = get_llm_router()

        try:
            llm = router.get_provider(provider)
            model = model or llm.default_model

            import httpx
            payload = {
                "model": model,
                "messages": messages,
                "temperature": data.get("temperature", 0.7),
                "max_tokens": data.get("max_tokens", 4096),
                "stream": True,
            }
            if provider in ("agnes",) and enable_thinking:
                payload["chat_template_kwargs"] = {"enable_thinking": True}

            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                async with client.stream(
                    "POST",
                    llm.chat_endpoint,
                    headers={"Authorization": f"Bearer {llm.api_key}", "Content-Type": "application/json"},
                    json=payload,
                ) as resp:
                    if resp.status_code in (401, 403):
                        await publish_result(request_id, {"content": f"API认证失败"})
                        await publish_done(request_id)
                        return
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                reasoning = (
                                    delta.get("reasoning_content", "")
                                    or delta.get("reasoning", "")
                                    or delta.get("thinking", "")
                                )
                                if reasoning:
                                    await publish_result(request_id, {"reasoning": reasoning})
                                if content:
                                    await publish_result(request_id, {"content": content})
                            except Exception:
                                continue
        except Exception as e:
            await publish_result(request_id, {"content": f"错误: {e}"})

        await publish_done(request_id)


async def main():
    print("[ChatWorker] Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    chat_queue = await channel.declare_queue(QUEUE_LLM, durable=True)

    print(f"[ChatWorker] Listening on '{QUEUE_LLM}'...")
    await chat_queue.consume(handle_chat_message)
    print("[ChatWorker] Ready.")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
