import json
import re
import asyncio
from typing import List, Dict, Optional
from models.intent import ParsedIntent, SubTask, ToolRequirement, IntentType


TOOL_KEYWORDS = {
    "calculator": ["计算", "多少", "加", "减", "乘", "除", "求和", "平均"],
    "datetime": ["几点", "时间", "日期", "今天", "明天", "昨天", "星期"],
    "web_search": ["搜索", "查找", "查一下", "搜一下", "google", "百度"],
    "open_url": ["打开网页", "打开网站", "打开url", "open url"],
    "open_app": ["打开应用", "打开软件", "启动", "open app", "chrome", "edge", "vscode", "记事本", "微信", "word", "excel", "ppt"],
    "run_command": ["运行命令", "执行命令", "运行命令", "执行命令", "cmd", "terminal", "ipconfig", "dir", "ls"],
    "code_generate": ["写代码", "生成代码", "写程序", "创建项目", "code generate"],
    "open_file": ["打开文件", "读取文件"],
    "list_dir": ["列出目录", "查看目录", "目录内容"],
}

MULTI_STEP_PATTERNS = [
    r"并且|然后|接着|同时|再.*也",
    r"先.*再.*",
    r"一.*二.*三",
    r"以及|还有|另外",
    r"和.*一起",
    r"写.*并.*配",
    r"生成.*和.*",
    r"创建.*并.*",
]

CREATIVE_KEYWORDS = ["写", "创作", "文章", "作文", "故事", "诗", "小说", "文案", "周报", "报告", "总结", "方案", "策划"]
ANALYSIS_KEYWORDS = ["分析", "对比", "比较", "评估", "研究", "调研"]
INFO_KEYWORDS = ["什么是", "怎么", "如何", "为什么", "介绍", "解释", "了解", "知道"]


class IntentEngine:
    def __init__(self, llm_provider):
        self.llm = llm_provider

    async def parse_intent(self, message: str, context: List[Dict] = None,
                           provider: str = None, model: str = None) -> ParsedIntent:
        intent = self._heuristic_parse(message, context)

        if intent.confidence >= 0.8:
            return intent

        try:
            llm_intent = await asyncio.wait_for(
                self._llm_parse(message, context, provider, model),
                timeout=15.0
            )
            if llm_intent and llm_intent.confidence > intent.confidence:
                return llm_intent
        except (asyncio.TimeoutError, Exception) as e:
            print(f"[IntentEngine] LLM parse skipped: {e}")

        return intent

    def _heuristic_parse(self, message: str, context: List[Dict] = None) -> ParsedIntent:
        msg_lower = message.lower().strip()

        if len(msg_lower) <= 5 and not any(kw in msg_lower for kw in ["计算", "几点", "时间"]):
            return ParsedIntent(
                original_message=message,
                intent_type=IntentType.CONVERSATION,
                goals=[message],
                subtasks=[],
                confidence=0.95
            )

        if re.search(r"^\d+[\+\-\*\/]\d+", msg_lower):
            return ParsedIntent(
                original_message=message,
                intent_type=IntentType.SINGLE_ACTION,
                goals=["计算数学表达式"],
                subtasks=[SubTask(
                    id="step_0",
                    description=f"计算: {message}",
                    required_tools=[ToolRequirement(tool_name="calculator", parameters={"expression": message})]
                )],
                confidence=0.95
            )

        detected_tools = []
        for tool_name, keywords in TOOL_KEYWORDS.items():
            for kw in keywords:
                if kw in msg_lower:
                    detected_tools.append(tool_name)
                    break

        if not detected_tools:
            open_match = re.match(r'打开(\S+)', message.strip())
            if open_match:
                app_name = open_match.group(1)
                detected_tools.append("open_app")
                return ParsedIntent(
                    original_message=message,
                    intent_type=IntentType.SINGLE_ACTION,
                    goals=[f"打开 {app_name}"],
                    subtasks=[SubTask(
                        id="step_0",
                        description=f"打开 {app_name}",
                        required_tools=[ToolRequirement(
                            tool_name="open_app",
                            parameters={"app_name": app_name}
                        )]
                    )],
                    confidence=0.9
                )

        is_multi_step = False
        for pattern in MULTI_STEP_PATTERNS:
            if re.search(pattern, message):
                is_multi_step = True
                break

        if is_multi_step and len(detected_tools) >= 2:
            subtasks = []
            for i, tool in enumerate(detected_tools):
                subtasks.append(SubTask(
                    id=f"step_{i}",
                    description=f"使用 {tool} 工具",
                    required_tools=[ToolRequirement(tool_name=tool)]
                ))
            return ParsedIntent(
                original_message=message,
                intent_type=IntentType.MULTI_STEP_TASK,
                goals=[f"执行 {len(detected_tools)} 个步骤"],
                subtasks=subtasks,
                confidence=0.7
            )

        if len(detected_tools) == 1:
            return ParsedIntent(
                original_message=message,
                intent_type=IntentType.SINGLE_ACTION,
                goals=[f"使用 {detected_tools[0]}"],
                subtasks=[SubTask(
                    id="step_0",
                    description=f"使用 {detected_tools[0]}: {message}",
                    required_tools=[ToolRequirement(tool_name=detected_tools[0])]
                )],
                confidence=0.85
            )

        if any(kw in msg_lower for kw in CREATIVE_KEYWORDS):
            missing = []
            if not any(k in msg_lower for k in ["关于", "主题", "题目"]):
                missing.append("主题")
            return ParsedIntent(
                original_message=message,
                intent_type=IntentType.CREATIVE_TASK,
                goals=[message],
                subtasks=[SubTask(id="step_0", description=message)],
                missing_info=missing,
                confidence=0.75 if not missing else 0.5
            )

        if any(kw in msg_lower for kw in ANALYSIS_KEYWORDS):
            return ParsedIntent(
                original_message=message,
                intent_type=IntentType.ANALYSIS_TASK,
                goals=[message],
                subtasks=[SubTask(id="step_0", description=message)],
                confidence=0.8
            )

        if any(kw in msg_lower for kw in INFO_KEYWORDS):
            return ParsedIntent(
                original_message=message,
                intent_type=IntentType.INFORMATION_REQUEST,
                goals=[message],
                subtasks=[SubTask(id="step_0", description=message)],
                confidence=0.85
            )

        return ParsedIntent(
            original_message=message,
            intent_type=IntentType.CONVERSATION,
            goals=[message],
            subtasks=[],
            confidence=0.8
        )

    async def _llm_parse(self, message: str, context: List[Dict],
                         provider: str = None, model: str = None) -> Optional[ParsedIntent]:
        context_str = ""
        if context:
            recent = context[-4:]
            context_str = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')[:100]}" for m in recent])

        prompt = f"""分析用户意图，返回JSON（仅返回JSON，无其他内容）:
{{"intent_type":"single_action|multi_step_task|conversation","goals":["目标"],"subtasks":[{{"id":"step_0","description":"描述","required_tools":[{{"tool_name":"工具名","parameters":{{}}}}],"required_info":[],"dependencies":[]}}],"missing_info":[],"confidence":0.9}}

可用工具: calculator, datetime, web_search, open_url, open_app, run_command, code_generate
用户: {message}"""

        response = await self.llm.chat(
            [{"role": "user", "content": prompt}],
            provider=provider, model=model
        )
        content = response.content if hasattr(response, 'content') else str(response)
        parsed = self._parse_json_response(content)
        return self._build_intent(message, parsed)

    def _parse_json_response(self, text: str) -> dict:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return {"intent_type": "conversation", "goals": [text], "subtasks": [], "missing_info": [], "confidence": 0.5}

    def _build_intent(self, message: str, data: dict) -> ParsedIntent:
        if not isinstance(data, dict):
            return self._fallback_intent(message)

        intent_type_str = data.get("intent_type", "conversation")
        if not isinstance(intent_type_str, str):
            intent_type_str = "conversation"
        try:
            intent_type = IntentType(intent_type_str)
        except ValueError:
            intent_type = IntentType.CONVERSATION

        goals = data.get("goals", [message])
        if not isinstance(goals, list):
            goals = [message]

        subtasks = []
        raw_subtasks = data.get("subtasks", [])
        if isinstance(raw_subtasks, list):
            for st in raw_subtasks:
                if not isinstance(st, dict):
                    continue
                tools = []
                raw_tools = st.get("required_tools", [])
                if isinstance(raw_tools, list):
                    for t in raw_tools:
                        if isinstance(t, dict):
                            tools.append(ToolRequirement(
                                tool_name=t.get("tool_name", ""),
                                parameters=t.get("parameters", {}),
                                confidence=t.get("confidence", 0.8),
                            ))
                subtasks.append(SubTask(
                    id=st.get("id", f"step_{len(subtasks)}"),
                    description=st.get("description", ""),
                    intent_type=intent_type,
                    required_tools=tools,
                    required_info=st.get("required_info", []) if isinstance(st.get("required_info"), list) else [],
                    dependencies=st.get("dependencies", []) if isinstance(st.get("dependencies"), list) else []
                ))

        missing_info = data.get("missing_info", [])
        if not isinstance(missing_info, list):
            missing_info = []
        confidence = data.get("confidence", 0.7)
        if not isinstance(confidence, (int, float)):
            confidence = 0.7

        return ParsedIntent(
            original_message=message,
            intent_type=intent_type,
            goals=goals,
            subtasks=subtasks,
            missing_info=missing_info,
            confidence=confidence
        )

    def _fallback_intent(self, message: str) -> ParsedIntent:
        return ParsedIntent(
            original_message=message,
            intent_type=IntentType.CONVERSATION,
            goals=[message],
            subtasks=[],
            missing_info=[],
            confidence=0.5
        )
