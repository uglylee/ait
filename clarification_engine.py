import asyncio
from typing import List, Dict, Optional
from models.intent import ParsedIntent


class ClarificationEngine:
    def __init__(self, llm_provider):
        self.llm = llm_provider

    async def analyze_and_clarify(
        self,
        intent: ParsedIntent,
        context: List[Dict] = None,
        provider: str = None,
        model: str = None
    ) -> Optional[str]:
        missing = self._detect_missing_info(intent, context)
        if not missing:
            return None

        try:
            return await asyncio.wait_for(
                self._generate_clarify(missing, intent.goals, provider, model),
                timeout=10.0
            )
        except (asyncio.TimeoutError, Exception):
            return f"请告诉我更多信息，比如：{'、'.join(missing[:2])}"

    def _detect_missing_info(self, intent: ParsedIntent, context: List[Dict] = None) -> List[str]:
        missing = list(intent.missing_info)

        context_text = ""
        if context:
            context_text = " ".join([m.get("content", "") for m in context[-4:]])

        for subtask in intent.subtasks:
            for req in subtask.required_info:
                if req.lower() not in context_text.lower():
                    if req not in missing:
                        missing.append(req)

        return missing

    async def _generate_clarify(self, missing_info, goals, provider=None, model=None) -> str:
        missing_str = "、".join(missing_info) if isinstance(missing_info, list) else str(missing_info)
        goals_str = "、".join(goals) if isinstance(goals, list) else str(goals)

        prompt = f"""用户想要: {goals_str}
缺少信息: {missing_str}
请生成一个简洁友好的追问（只问最重要的一个问题）。直接输出问题。"""

        response = await self.llm.chat(
            [{"role": "user", "content": prompt}],
            provider=provider, model=model
        )
        return response.content if hasattr(response, 'content') else str(response)
