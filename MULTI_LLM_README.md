# 多LLM提供商支持

## 支持的提供商

| 提供商 | 模型 | 说明 |
|--------|------|------|
| DeepSeek | deepseek-chat, deepseek-coder | 国产大模型，性价比高 |
| MiMo | mimo-auto | 小米AI模型 |
| OpenAI | gpt-3.5-turbo, gpt-4 | 国际主流模型 |
| 通义千问 | qwen-turbo, qwen-plus | 阿里云模型 |
| 智谱GLM | glm-4-flash, glm-4 | 智谱AI模型 |

## 配置方法

### 1. 环境变量配置

在 `.env` 文件中配置各提供商的API密钥：

```bash
# DeepSeek
DEEPSEEK_API_KEY=your-deepseek-api-key

# MiMo
MIMO_API_KEY=your-mimo-api-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# 通义千问
QWEN_API_KEY=your-qwen-api-key

# 智谱GLM
GLM_API_KEY=your-glm-api-key

# 默认提供商
DEFAULT_PROVIDER=deepseek

# 降级顺序
FALLBACK_ORDER=["deepseek", "mimo", "qwen", "glm", "openai"]
```

### 2. 代码配置

```python
from llm_providers import LLMRouter, DeepSeekProvider, MiMoProvider

# 创建路由器
router = LLMRouter()

# 注册提供商
router.register_provider(
    "deepseek",
    DeepSeekProvider(api_key="your-key"),
    is_default=True
)

router.register_provider(
    "mimo",
    MiMoProvider(api_key="your-key")
)
```

## 使用方法

### 1. 基础调用

```python
import asyncio
from llm_config import llm_router

async def main():
    # 使用默认提供商
    response = await llm_router.generate("什么是机器学习？")
    print(response.content)
    
    # 指定提供商
    response = await llm_router.chat(
        [{"role": "user", "content": "你好"}],
        provider="deepseek"
    )
    print(response.content)

asyncio.run(main())
```

### 2. 降级调用

```python
async def main():
    # 主提供商失败时自动切换
    response = await llm_router.chat_with_fallback(
        messages=[{"role": "user", "content": "你好"}],
        providers=["deepseek", "mimo", "qwen"]
    )
    print(f"使用提供商: {response.provider}")
    print(response.content)
```

### 3. 多轮对话

```python
async def main():
    messages = [
        {"role": "system", "content": "你是一个助手"},
        {"role": "user", "content": "什么是Python？"}
    ]
    
    # 第一轮
    response1 = await llm_router.chat(messages)
    messages.append({"role": "assistant", "content": response1.content})
    
    # 第二轮
    messages.append({"role": "user", "content": "能给个例子吗？"})
    response2 = await llm_router.chat(messages)
    print(response2.content)
```

## API接口

### 列出可用提供商

```bash
GET /api/v1/llm/providers
```

响应：
```json
{
    "providers": [
        {
            "name": "deepseek",
            "default_model": "deepseek-chat",
            "is_default": true
        },
        {
            "name": "mimo",
            "default_model": "mimo-auto",
            "is_default": false
        }
    ],
    "default_provider": "deepseek",
    "fallback_order": ["deepseek", "mimo"]
}
```

### 指定提供商对话

```bash
POST /api/v1/chat/provider
{
    "message": "什么是机器学习？",
    "provider": "deepseek",
    "model": "deepseek-chat"
}
```

响应：
```json
{
    "response": "机器学习是人工智能的一个分支...",
    "confidence": 0.95,
    "sources": ["llm_deepseek"]
}
```

## 架构设计

```
用户请求
    ↓
LLM路由器
    ↓
┌─────────────────────────────────────┐
│  DeepSeek  │  MiMo  │  OpenAI  │ ... │
└─────────────────────────────────────┘
    ↓
降级机制（主提供商失败时自动切换）
    ↓
统一响应格式
```

## 特性

1. **统一接口**: 所有提供商使用相同的调用方式
2. **自动降级**: 主提供商失败时自动切换到备用提供商
3. **灵活配置**: 支持环境变量和代码配置
4. **易于扩展**: 添加新提供商只需继承基类
5. **类型安全**: 使用Pydantic进行数据验证

## 扩展新提供商

```python
from llm_providers import BaseLLMProvider, LLMResponse

class MyProvider(BaseLLMProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def chat(self, messages, model=None, **kwargs):
        # 实现API调用逻辑
        return LLMResponse(
            content="回复内容",
            model=model,
            usage={"prompt_tokens": 10, "completion_tokens": 20},
            provider="my_provider"
        )
    
    async def generate(self, prompt, model=None, **kwargs):
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, **kwargs)

# 注册新提供商
router.register_provider("my_provider", MyProvider(api_key="your-key"))
```

## 注意事项

1. API密钥安全：不要将API密钥提交到代码仓库
2. 费用控制：不同提供商计费方式不同，注意成本
3. 速率限制：注意各提供商的调用频率限制
4. 错误处理：生产环境建议添加重试和超时机制
