from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel
import httpx
import json

_http_client = None

def get_http_client():
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            http2=False,
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
            timeout=httpx.Timeout(connect=3.0, read=120.0, write=3.0, pool=3.0)
        )
    return _http_client

class LLMResponse(BaseModel):
    content: str
    model: str
    usage: dict
    provider: str

class BaseLLMProvider(ABC):
    """LLM提供商基类"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        pass
    
    @property
    def chat_endpoint(self) -> str:
        url = self.base_url.rstrip('/')
        if url.endswith('/v1') or url.endswith('/v4'):
            return f"{url}/chat/completions"
        if '/v1/' in url or '/v4/' in url:
            return f"{url}/chat/completions"
        return f"{url}/v1/chat/completions"
    
    @property
    def models_endpoint(self) -> str:
        url = self.base_url.rstrip('/')
        if url.endswith('/v1') or url.endswith('/v4'):
            return f"{url}/models"
        if '/v1/' in url or '/v4/' in url:
            return f"{url}/models"
        return f"{url}/v1/models"
    
    async def list_models(self) -> List[str]:
        """获取可用模型列表"""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.models_endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                models = [m["id"] for m in data.get("data", []) if m.get("id")]
                return sorted(models)
        except Exception:
            return []
    
    async def chat(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        model = model or self.default_model
        url = self.chat_endpoint
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2048)
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data["usage"],
                provider="deepseek"
            )
    
    async def generate(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, **kwargs)

class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = model or "deepseek-chat"
    
    async def chat(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        model = model or self.default_model
        url = self.chat_endpoint
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2048)
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data["usage"],
                provider="deepseek"
            )
    
    async def generate(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, **kwargs)

class MiMoProvider(BaseLLMProvider):
    """MiMo API (Xiaomi)"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.xiaomimimo.com", model: str = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = model or "mimo-auto"
    
    async def chat(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        model = model or self.default_model
        url = self.chat_endpoint
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2048)
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data["usage"],
                provider="mimo"
            )
    
    async def generate(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, **kwargs)

class OpenAIProvider(BaseLLMProvider):
    """OpenAI API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com", model: str = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = model or "gpt-3.5-turbo"
    
    async def chat(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        model = model or self.default_model
        url = self.chat_endpoint
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2048)
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data["usage"],
                provider="openai"
            )
    
    async def generate(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, **kwargs)

class QwenProvider(BaseLLMProvider):
    """通义千问 API"""
    
    def __init__(self, api_key: str, base_url: str = "https://dashscope.aliyuncs.com", model: str = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = model or "qwen-turbo"
    
    @property
    def chat_endpoint(self) -> str:
        if "dashscope.aliyuncs.com" in self.base_url:
            return f"{self.base_url}/compatible-mode/v1/chat/completions"
        if "/v1" not in self.base_url:
            return f"{self.base_url}/v1/chat/completions"
        return f"{self.base_url}/chat/completions"
    
    @property
    def models_endpoint(self) -> str:
        if "dashscope.aliyuncs.com" in self.base_url:
            return f"{self.base_url}/compatible-mode/v1/models"
        if "/v1" not in self.base_url:
            return f"{self.base_url}/v1/models"
        return f"{self.base_url}/models"
    
    async def list_models(self) -> List[str]:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.models_endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                models = [m["id"] for m in data.get("data", []) if m.get("id")]
                return sorted(models)
        except Exception:
            return []
        model = model or self.default_model
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.chat_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2048)
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data["usage"],
                provider="qwen"
            )
    
    async def generate(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, **kwargs)

class GLMProvider(BaseLLMProvider):
    """智谱GLM API"""
    
    def __init__(self, api_key: str, base_url: str = "https://open.bigmodel.cn", model: str = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = model or "glm-4-flash"
    
    @property
    def chat_endpoint(self) -> str:
        url = self.base_url.rstrip('/')
        if '/api/paas/v4' in url:
            return f"{url}/chat/completions"
        if "open.bigmodel.cn" in url:
            return f"{url}/api/paas/v4/chat/completions"
        return super().chat_endpoint
    
    @property
    def models_endpoint(self) -> str:
        url = self.base_url.rstrip('/')
        if '/api/paas/v4' in url:
            return f"{url}/models"
        if "open.bigmodel.cn" in url:
            return f"{url}/api/paas/v4/models"
        return super().models_endpoint
    
    async def list_models(self) -> List[str]:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.models_endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                data = response.json()
                models = [m["id"] for m in data.get("data", []) if m.get("id")]
                return sorted(models)
        except Exception:
            return []
    
    async def chat(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        model = model or self.default_model
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.chat_endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2048)
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data["usage"],
                provider="glm"
            )
    
    async def generate(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, **kwargs)

class AgnesProvider(BaseLLMProvider):
    """Agnes API"""
    
    def __init__(self, api_key: str, base_url: str = "https://apihub.agnes-ai.com", model: str = None):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.default_model = model or "agnes-2.0-flash"
    
    async def chat(self, messages: List[Dict], model: str = None, **kwargs) -> LLMResponse:
        model = model or self.default_model
        url = self.chat_endpoint
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_tokens": kwargs.get("max_tokens", 2048)
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=data["model"],
                usage=data["usage"],
                provider="agnes"
            )
    
    async def generate(self, prompt: str, model: str = None, **kwargs) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, model, **kwargs)

class LLMRouter:
    """LLM路由器 - 统一管理多个提供商"""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider: Optional[str] = None
    
    def register_provider(self, name: str, provider: BaseLLMProvider, is_default: bool = False):
        self.providers[name] = provider
        if is_default:
            self.default_provider = name
    
    def get_provider(self, name: str = None) -> BaseLLMProvider:
        provider_name = name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not registered")
        return self.providers[provider_name]
    
    async def list_models(self, provider: str = None) -> List[str]:
        """获取指定提供商的可用模型列表"""
        llm = self.get_provider(provider)
        return await llm.list_models()
    
    async def chat(self, messages: List[Dict], provider: str = None, model: str = None, **kwargs) -> LLMResponse:
        llm = self.get_provider(provider)
        return await llm.chat(messages, model, **kwargs)
    
    async def generate(self, prompt: str, provider: str = None, model: str = None, **kwargs) -> LLMResponse:
        llm = self.get_provider(provider)
        return await llm.generate(prompt, model, **kwargs)
    
    async def chat_with_fallback(self, messages: List[Dict], providers: List[str] = None, **kwargs) -> LLMResponse:
        """带降级的聊天 - 主提供商失败时自动切换"""
        provider_list = providers or list(self.providers.keys())
        
        for provider_name in provider_list:
            try:
                return await self.chat(messages, provider=provider_name, **kwargs)
            except Exception as e:
                print(f"Provider {provider_name} failed: {e}")
                continue
        
        raise Exception("All providers failed")

    async def chat_stream(self, messages: List[Dict], provider: str = None, model: str = None, **kwargs):
        """流式聊天 - 返回异步生成器"""
        llm = self.get_provider(provider)
        model = model or llm.default_model
        client = get_http_client()

        payload = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True
        }

        provider_name = provider or llm.name
        if provider_name in ("agnes",) and kwargs.get("enable_thinking", True):
            payload["chat_template_kwargs"] = {"enable_thinking": True}

        async with client.stream(
            "POST",
            llm.chat_endpoint,
            headers={
                "Authorization": f"Bearer {llm.api_key}",
                "Content-Type": "application/json"
            },
            json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        yield "[DONE]"
                        break
                    try:
                        import json
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        reasoning = (
                            delta.get("reasoning_content", "")
                            or delta.get("reasoning", "")
                            or delta.get("thinking", "")
                        )
                        content = delta.get("content", "")
                        if reasoning:
                            yield json.dumps({"type": "reasoning", "content": reasoning})
                        if content:
                            yield content
                    except Exception:
                        continue
