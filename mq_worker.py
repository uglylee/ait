import asyncio
import json
import os
import sys
import platform
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from mq import (
    RABBITMQ_URL, QUEUE_LLM, QUEUE_AUTO,
    publish_result, publish_done,
)
from llm_config import get_llm_router
from langchain_engine import ALL_TOOLS

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
                        await publish_result(request_id, {"content": f"API认证失败 (key: {llm.api_key[:8]}...)"})
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


async def handle_auto_message(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body.decode())
        request_id = data["request_id"]
        user_message = data["message"]
        provider = data.get("provider")
        model = data.get("model")

        router = get_llm_router()
        tool_map = {t.name: t for t in ALL_TOOLS}

        async def push(event):
            await publish_result(request_id, event)

        os_name = platform.system()
        cwd = os.path.abspath(".")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tools_list = ", ".join([t.name for t in ALL_TOOLS])

        identity_prompt = (
            "You are an AI coding agent that helps users complete tasks by using tools.\n"
            "Be concise, clear, and efficient.\n\n"
            "## Key Rules\n"
            "- Use tools to get real results.\n"
            "- Execute commands directly.\n"
            "- After using tools, present the results clearly.\n"
        )
        env_prompt = f"## Environment\n- OS: {os_name}\n- Working directory: {cwd}\n- Current time: {current_time}\n- Available tools: {tools_list}\n"
        system_content = identity_prompt + "\n" + env_prompt

        auto_tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": {"type": "object", "properties": {"input": {"type": "string"}}, "required": ["input"]}
                }
            } for t in ALL_TOOLS
        ]

        messages = [{"role": "system", "content": system_content}, {"role": "user", "content": user_message}]
        collected_text = ""
        goal_status = "active"
        blocked_count = 0

        try:
            for round_num in range(50):
                if goal_status != "active":
                    break

                llm = router.get_provider(provider)

                await push({"round_start": {"round": round_num + 1, "max_rounds": 50}})

                import httpx
                payload = {
                    "model": model or llm.default_model,
                    "messages": messages,
                    "tools": auto_tools,
                    "tool_choice": "auto",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "enable_thinking": False,
                }

                async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
                    resp = await client.post(
                        llm.chat_endpoint,
                        headers={"Authorization": f"Bearer {llm.api_key}", "Content-Type": "application/json"},
                        json=payload,
                    )
                    data_resp = resp.json()
                    if "error" in data_resp:
                        await push({"content": f"API error: {data_resp['error']}\n"})
                        break
                    choice = data_resp["choices"][0]
                    msg = choice["message"]
                    full_response = msg.get("content", "")
                    if not isinstance(full_response, str):
                        full_response = json.dumps(full_response, ensure_ascii=False) if full_response else ""
                    tool_calls = msg.get("tool_calls")

                if not tool_calls:
                    if full_response:
                        collected_text = full_response
                        await push({"content": full_response})
                    goal_status = "complete"
                    await push({"goal_event": {"type": "complete", "round": round_num + 1}})
                    break

                if full_response:
                    await push({"content": full_response})

                messages.append({"role": "assistant", "content": full_response or "", "tool_calls": tool_calls})

                any_tool_failed = False
                for tc in tool_calls:
                    tc_id = tc["id"]
                    func = tc["function"]
                    tool_name = func["name"]
                    try:
                        tool_args = json.loads(func["arguments"])
                        tool_input = tool_args.get("input", "")
                    except (json.JSONDecodeError, KeyError):
                        tool_input = func.get("arguments", "")

                    await push({"tool_call": {"name": tool_name, "input": str(tool_input)[:500]}})

                    if tool_name in tool_map:
                        try:
                            tool_result = tool_map[tool_name].run(str(tool_input))
                        except Exception as te:
                            tool_result = f"Tool error: {te}"
                            any_tool_failed = True
                    else:
                        tool_result = f"Tool '{tool_name}' not available"
                        any_tool_failed = True

                    tool_result_str = str(tool_result)[:5000]
                    await push({"tool_result": {"name": tool_name, "result": tool_result_str[:300]}})

                    messages.append({"role": "tool", "tool_call_id": tc_id, "content": tool_result_str})

                if any_tool_failed:
                    blocked_count += 1
                else:
                    blocked_count = 0

                if blocked_count >= 3:
                    await push({"goal_event": {"type": "blocked", "round": round_num + 1}})
                    break

                messages.append({"role": "system", "content": "Continue working toward the active goal."})
                await asyncio.sleep(0.1)

            if goal_status == "active":
                goal_status = "complete"
                await push({"goal_event": {"type": "complete", "round": round_num + 1}})

        except Exception as e:
            await push({"content": f"Worker error: {e}"})

        final_text = collected_text or f"Goal {goal_status}."
        import redis.asyncio as aioredis
        r = aioredis.from_url("redis://:ai_redis_2024@localhost:6379", decode_responses=True)
        try:
            await r.set(f"auto_result:{request_id}", final_text, ex=600)
        finally:
            await r.close()

        await publish_done(request_id)


async def main():
    print("[Worker] Connecting to RabbitMQ...")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    chat_queue = await channel.declare_queue(QUEUE_LLM, durable=True)
    auto_queue = await channel.declare_queue(QUEUE_AUTO, durable=True)

    print(f"[Worker] Listening on '{QUEUE_LLM}' and '{QUEUE_AUTO}'...")

    await chat_queue.consume(handle_chat_message)
    await auto_queue.consume(handle_auto_message)

    print("[Worker] Ready. Waiting for messages...")
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
