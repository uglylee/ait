import json
from typing import AsyncGenerator, Dict, List, Optional
from intent_engine import IntentEngine
from clarification_engine import ClarificationEngine
from task_manager import TaskManager
from planner_engine import PlannerEngine
from models.intent import ParsedIntent, IntentType
from models.task import Task, TaskStatus, StepResult, StepStatus


class Orchestrator:
    def __init__(self, llm_provider, tool_map: Dict = None, mongodb=None):
        self.intent_engine = IntentEngine(llm_provider)
        self.clarification_engine = ClarificationEngine(llm_provider)
        self.planner = PlannerEngine(llm_provider, tool_map)
        self.task_manager = TaskManager(mongodb) if mongodb is not None else None
        self.llm = llm_provider
        self.tool_map = tool_map or {}

    async def handle_message(
        self,
        message: str,
        conversation_id: str = None,
        context: List[Dict] = None,
        provider: str = None,
        model: str = None,
        automation: bool = True,
        web_search: bool = False
    ) -> AsyncGenerator[Dict, None]:
        if not automation:
            if web_search:
                search_result = self._run_tool("web_search", message)
                message_with_context = f"以下是关于该问题的搜索结果:\n{search_result}\n\n请基于以上搜索结果回答用户问题: {message}"
                messages = [{"role": "system", "content": "你是一个友好的AI助手，用中文回答问题。请基于提供的搜索结果回答。"}]
                if context:
                    messages.extend(context[-6:])
                messages.append({"role": "user", "content": message_with_context})
                try:
                    async for chunk in self.llm.chat_stream(messages, provider=provider, model=model):
                        if chunk and chunk.strip() != "[DONE]":
                            yield {"type": "stream_chunk", "content": chunk}
                except Exception as e:
                    yield {"type": "stream_chunk", "content": f"抱歉，出错了: {e}"}
            else:
                async for chunk in self._simple_chat_stream(message, context, provider=provider, model=model):
                    yield chunk
            return

        yield {"type": "status", "content": "正在分析意图..."}

        intent = await self.intent_engine.parse_intent(message, context, provider=provider, model=model)

        type_labels = {
            "single_action": "单一操作",
            "multi_step_task": "多步骤任务",
            "information_request": "信息查询",
            "creative_task": "创作任务",
            "analysis_task": "分析任务",
            "conversation": "普通对话",
        }
        type_label = type_labels.get(intent.intent_type.value, intent.intent_type.value)
        goals_str = " → ".join(intent.goals[:3])
        tool_names = []
        for st in intent.subtasks:
            for t in st.required_tools:
                tool_names.append(t.tool_name)
        tool_str = f"，使用工具: {', '.join(tool_names)}" if tool_names else ""
        detail = f"意图类型: {type_label}{tool_str}\n目标: {goals_str}"

        if intent.intent_type == IntentType.CONVERSATION and intent.confidence > 0.7:
            async for chunk in self._simple_chat_stream(message, context, provider=provider, model=model):
                yield chunk
            return

        needs_tool = any(
            st.required_tools
            for st in intent.subtasks
        )
        if not needs_tool:
            async for chunk in self._simple_chat_stream(message, context, provider=provider, model=model):
                yield chunk
            return

        all_tools = []
        for st in intent.subtasks:
            for t in st.required_tools:
                all_tools.append(t)

        if len(all_tools) == 1:
            tool_req = all_tools[0]
            tool_name = tool_req.tool_name
            tool_input = self._build_single_tool_input(tool_req)

            yield {"type": "thought", "content": f"使用工具 {tool_name}: {tool_input}"}
            yield {"type": "action", "tool": tool_name, "input": tool_input}

            observation = self._run_tool(tool_name, tool_input)
            yield {"type": "observation", "tool": tool_name, "content": observation}

            prompt = f"工具 {tool_name} 返回: {observation}\n用户原始问题: {message}\n请基于工具结果用自然语言简洁回答。"
            yield {"type": "stream_start"}
            try:
                async for chunk in self.llm.chat_stream(
                    [{"role": "user", "content": prompt}],
                    provider=provider, model=model
                ):
                    if chunk and chunk.strip() != "[DONE]":
                        yield {"type": "stream_chunk", "content": chunk}
            except Exception as e:
                yield {"type": "stream_chunk", "content": f"\n\n{observation}"}
            return

        yield {"type": "thought", "content": detail}

        if intent.confidence < 0.6 and intent.missing_info:
            clarification = await self.clarification_engine.analyze_and_clarify(intent, context)
            if clarification:
                yield {"type": "clarification", "question": clarification}
                return

        task = None
        if self.task_manager:
            try:
                task = await self.task_manager.create_task(message, intent, conversation_id)
                yield {"type": "task_start", "task_id": task.id, "total_steps": len(intent.subtasks)}
            except Exception as e:
                print(f"[Orchestrator] Task create error: {e}")

        final_response = ""
        step_results = {}

        async for event in self.planner.execute_plan(intent, context, provider=provider, model=model):
            yield event

            if event.get("type") == "step_complete":
                step_results[event["step_id"]] = event.get("result", "")

            if event.get("type") == "response":
                final_response = event.get("content", "")

        if not final_response:
            final_response = await self._generate_summary(intent, step_results, message, provider=provider, model=model)
            yield {"type": "response", "content": final_response}

        if task and self.task_manager:
            try:
                await self.task_manager.complete_task(task.id, step_results)
            except Exception as e:
                print(f"[Orchestrator] Task complete error: {e}")

        yield {"type": "done"}

    async def resume_task(self, task_id: str) -> AsyncGenerator[Dict, None]:
        if not self.task_manager:
            yield {"type": "error", "content": "任务管理器未初始化"}
            return

        task = await self.task_manager.get_task(task_id)
        if not task:
            yield {"type": "error", "content": f"任务 {task_id} 不存在"}
            return

        if task.status not in [TaskStatus.PAUSED, TaskStatus.IN_PROGRESS]:
            yield {"type": "error", "content": f"任务状态为 {task.status}，无法恢复"}
            return

        intent_data = task.intent
        if isinstance(intent_data, dict):
            intent = ParsedIntent(**intent_data)
        else:
            intent = intent_data

        yield {"type": "task_resume", "task_id": task_id}

        async for event in self.planner.execute_plan(intent):
            yield event

        if self.task_manager:
            await self.task_manager.complete_task(task_id)

        yield {"type": "done"}

    async def _simple_chat(self, message: str, context: List[Dict] = None,
                           provider: str = None, model: str = None):
        messages = [{"role": "system", "content": "你是一个友好的AI助手，用中文回答问题。"}]
        if context:
            messages.extend(context[-6:])
        messages.append({"role": "user", "content": message})

        try:
            async for chunk in self.llm.chat_stream(messages, provider=provider, model=model):
                if chunk and chunk.strip() != "[DONE]":
                    yield {"type": "stream_chunk", "content": chunk}
        except Exception as e:
            import traceback
            print(f"[Orchestrator] _simple_chat error: {type(e).__name__}: {e}")
            traceback.print_exc()
            yield {"type": "stream_chunk", "content": f"抱歉，处理您的消息时出错了: {e}"}

    async def _simple_chat_stream(self, message: str, context: List[Dict] = None,
                                  provider: str = None, model: str = None):
        messages = [{"role": "system", "content": "你是一个友好的AI助手，用中文回答问题。"}]
        if context:
            messages.extend(context[-6:])
        messages.append({"role": "user", "content": message})

        try:
            async for chunk in self.llm.chat_stream(messages, provider=provider, model=model):
                if chunk and chunk.strip() != "[DONE]":
                    yield {"type": "stream_chunk", "content": chunk}
        except Exception as e:
            import traceback
            print(f"[Orchestrator] _simple_chat_stream error: {type(e).__name__}: {e}")
            traceback.print_exc()
            yield {"type": "stream_chunk", "content": f"抱歉，处理您的消息时出错了: {e}"}

    def _build_single_tool_input(self, tool_req) -> str:
        params = dict(tool_req.parameters)
        if not params:
            return ""
        if len(params) == 1:
            val = list(params.values())[0]
            if isinstance(val, str):
                return val
        return ", ".join([str(v) for v in params.values() if v])

    def _run_tool(self, tool_name: str, tool_input: str) -> str:
        if tool_name in self.tool_map:
            try:
                return self.tool_map[tool_name].run(tool_input)
            except Exception as e:
                return f"工具执行出错: {e}"
        return f"工具 '{tool_name}' 不可用"

    async def _generate_summary(
        self,
        intent: ParsedIntent,
        step_results: Dict,
        original_message: str,
        provider: str = None,
        model: str = None
    ) -> str:
        results_text = "\n".join([
            f"步骤 {k}: {str(v)[:300]}"
            for k, v in step_results.items()
        ])

        prompt = f"""用户请求: {original_message}
执行目标: {', '.join(intent.goals)}
各步骤结果:
{results_text}

请根据以上结果，用自然语言给用户一个完整的汇总回答。"""

        try:
            response = await self.llm.chat(
                [{"role": "user", "content": prompt}],
                provider=provider, model=model
            )
            return response.content if hasattr(response, 'content') else str(response)
        except Exception:
            parts = [str(v) for v in step_results.values()]
            return "\n\n".join(parts) if parts else "任务已完成，但无法生成汇总。"
