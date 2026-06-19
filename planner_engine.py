import json
import asyncio
from typing import AsyncGenerator, Dict, List, Optional
from datetime import datetime
from models.intent import ParsedIntent, SubTask
from models.task import StepResult, StepStatus


REPLAN_PROMPT = """已完成步骤: {completed_desc}
结果: {result}
原始目标: {goals}

是否需要额外步骤？如需要返回JSON数组（每项含description和required_tools），否则返回[]。"""


class PlannerEngine:
    def __init__(self, llm_provider, tool_map: Dict = None):
        self.llm = llm_provider
        self.tool_map = tool_map or {}
        self.max_iterations = 10
        self.max_tool_calls_per_step = 3

    async def execute_plan(
        self,
        intent: ParsedIntent,
        context: List[Dict] = None,
        provider: str = None,
        model: str = None
    ) -> AsyncGenerator[Dict, None]:
        steps = self._build_execution_queue(intent.subtasks)
        results = {}
        step_count = 0

        while steps and step_count < self.max_iterations:
            step = steps.pop(0)
            step_count += 1

            if step.dependencies:
                deps_met = all(d in results for d in step.dependencies)
                if not deps_met:
                    steps.append(step)
                    continue

            async for event in self._execute_step(step, results, intent, provider, model):
                yield event

            if step.result:
                results[step.id] = step.result

    async def _execute_step(
        self,
        step: SubTask,
        previous_results: Dict,
        intent: ParsedIntent,
        provider: str = None,
        model: str = None
    ) -> AsyncGenerator[Dict, None]:
        yield {"type": "step_start", "step_id": step.id, "description": step.description}

        if step.required_tools:
            tool_names = ", ".join([t.tool_name for t in step.required_tools])
            yield {"type": "thought", "step_id": step.id, "content": f"准备使用工具: {tool_names}"}

            for tool_req in step.required_tools[:self.max_tool_calls_per_step]:
                tool_name = tool_req.tool_name
                tool_input = self._build_tool_input(tool_req, previous_results)

                if tool_name in self.tool_map:
                    yield {"type": "action", "step_id": step.id, "tool": tool_name, "input": tool_input}

                    observation = self._observe_sync(tool_name, tool_input)
                    yield {"type": "observation", "step_id": step.id, "tool": tool_name, "content": observation}

                    step.result = observation
                    step.status = "completed"
                else:
                    step.result = f"工具 '{tool_name}' 不可用"
                    step.status = "failed"
                    yield {"type": "observation", "step_id": step.id, "tool": tool_name, "content": step.result}
        else:
            response = await self._generate_text_response(step, previous_results, intent, provider, model)
            yield {"type": "response", "step_id": step.id, "content": response}
            step.result = response
            step.status = "completed"

        yield {"type": "step_complete", "step_id": step.id, "result": step.result}

    def _observe_sync(self, tool_name: str, tool_input: str) -> str:
        if tool_name in self.tool_map:
            try:
                result = self.tool_map[tool_name].run(tool_input)
                return result
            except Exception as e:
                return f"工具执行出错: {e}"
        return f"工具 '{tool_name}' 不可用"

    async def _generate_text_response(
        self, step: SubTask, context: Dict, intent: ParsedIntent,
        provider: str = None, model: str = None
    ) -> str:
        context_summary = self._summarize_context(context)
        prompt = f"""任务: {step.description}
之前的结果: {context_summary}
用户目标: {', '.join(intent.goals)}

请完成这个任务，输出结果。"""

        try:
            response = await self.llm.chat(
                [{"role": "user", "content": prompt}],
                provider=provider, model=model
            )
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"生成失败: {e}"

    def _build_tool_input(self, tool_req, previous_results: Dict) -> str:
        params = dict(tool_req.parameters)
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$ref:"):
                ref_key = value[5:]
                if ref_key in previous_results:
                    params[key] = previous_results[ref_key]

        if not params:
            return ""

        if len(params) == 1:
            val = list(params.values())[0]
            if isinstance(val, str):
                return val

        parts = [f"{k}: {v}" for k, v in params.items() if v]
        return ", ".join(parts) if parts else ""

    def _build_execution_queue(self, subtasks: List[SubTask]) -> List[SubTask]:
        no_deps = [s for s in subtasks if not s.dependencies]
        with_deps = [s for s in subtasks if s.dependencies]
        return no_deps + with_deps

    def _summarize_context(self, context: Dict) -> str:
        if not context:
            return "无"
        parts = []
        for k, v in context.items():
            val_str = str(v)[:200]
            parts.append(f"{k}: {val_str}")
        return "; ".join(parts)
