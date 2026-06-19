import json
import os
from typing import Optional
from llm_providers import (
    LLMRouter, DeepSeekProvider, MiMoProvider, OpenAIProvider,
    QwenProvider, GLMProvider, AgnesProvider
)

class LLMRouterConfig:
    """从数据库读取配置，动态创建提供商"""
    
    def __init__(self):
        self.router = LLMRouter()
        self._load_from_db()
    
    def _load_from_db(self):
        """从数据库加载配置"""
        try:
            from pymongo import MongoClient
            mongo_url = os.environ.get("MONGODB_URL", "mongodb://ai_mongo:ai_mongo_2024@localhost:27017")
            client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
            db = client["ai_framework"]
            settings = db["settings"].find_one({"_id": "app_settings"}) or {}
            
            default_provider = settings.get("default_provider", "agnes")
            
            providers = {
                "deepseek": (DeepSeekProvider, "https://api.deepseek.com", "deepseek-chat"),
                "mimo": (MiMoProvider, "https://api.xiaomimimo.com", "mimo-auto"),
                "agnes": (AgnesProvider, "https://apihub.agnes-ai.com", "agnes-2.0-flash"),
                "qwen": (QwenProvider, "https://dashscope.aliyuncs.com", "qwen-turbo"),
                "glm": (GLMProvider, "https://open.bigmodel.cn/api/paas/v4", "glm-4-flash"),
                "openai": (OpenAIProvider, "https://api.openai.com", "gpt-3.5-turbo"),
                "custom": (OpenAIProvider, "", ""),
            }
            
            for name, (ProviderClass, default_url, default_model) in providers.items():
                try:
                    api_key = settings.get(f"{name}_key", "")
                    base_url = settings.get(f"{name}_url") or default_url
                    model = settings.get(f"{name}_model") or default_model
                    
                    if api_key and api_key != f"your-{name}-api-key":
                        if name == "custom" and not base_url:
                            continue
                        self.router.register_provider(
                            name,
                            ProviderClass(api_key=api_key, base_url=base_url, model=model),
                            is_default=(default_provider == name)
                        )
                except Exception as e:
                    print(f"Warning: Could not load provider '{name}': {e}")
            
            if not self.router.default_provider:
                self.router.default_provider = default_provider
                
        except Exception as e:
            print(f"Warning: Could not load LLM config from DB: {e}")
    
    def refresh(self):
        """刷新配置（设置保存后调用）"""
        self.router = LLMRouter()
        self._load_from_db()

_config = LLMRouterConfig()

def get_llm_router():
    return _config.router

def refresh_llm_router():
    _config.refresh()
