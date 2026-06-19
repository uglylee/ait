"""
多LLM提供商使用示例
展示如何调用DeepSeek、MiMo等多种AI接口
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_providers import (
    LLMRouter, DeepSeekProvider, MiMoProvider, OpenAIProvider,
    QwenProvider, GLMProvider, LLMResponse
)
from llm_config import llm_router

async def demo_single_provider():
    """单提供商调用示例"""
    print("=" * 60)
    print("单提供商调用示例")
    print("=" * 60)
    
    # 直接调用DeepSeek
    deepseek = DeepSeekProvider(api_key="your-deepseek-api-key")
    
    response = await deepseek.chat([
        {"role": "system", "content": "你是一个有帮助的助手"},
        {"role": "user", "content": "什么是机器学习？"}
    ])
    
    print(f"提供商: {response.provider}")
    print(f"模型: {response.model}")
    print(f"回复: {response.content}")
    print(f"Token使用: {response.usage}")
    print()

async def demo_router_with_provider():
    """路由器指定提供商调用"""
    print("=" * 60)
    print("路由器指定提供商调用")
    print("=" * 60)
    
    # 使用路由器，指定提供商
    response = await llm_router.chat(
        messages=[
            {"role": "user", "content": "解释一下什么是RAG"}
        ],
        provider="deepseek"
    )
    
    print(f"提供商: {response.provider}")
    print(f"模型: {response.model}")
    print(f"回复: {response.content}")
    print()

async def demo_router_default_provider():
    """路由器默认提供商调用"""
    print("=" * 60)
    print("路由器默认提供商调用")
    print("=" * 60)
    
    # 使用路由器的默认提供商
    response = await llm_router.generate(
        prompt="写一个Python快速排序算法"
    )
    
    print(f"提供商: {response.provider}")
    print(f"模型: {response.model}")
    print(f"回复: {response.content}")
    print()

async def demo_fallback():
    """降级调用示例"""
    print("=" * 60)
    print("降级调用示例（主提供商失败时自动切换）")
    print("=" * 60)
    
    try:
        response = await llm_router.chat_with_fallback(
            messages=[
                {"role": "user", "content": "你好"}
            ],
            providers=["deepseek", "mimo", "qwen"]
        )
        
        print(f"最终使用提供商: {response.provider}")
        print(f"模型: {response.model}")
        print(f"回复: {response.content}")
    except Exception as e:
        print(f"所有提供商都失败: {e}")
    print()

async def demo_multi_turn_conversation():
    """多轮对话示例"""
    print("=" * 60)
    print("多轮对话示例")
    print("=" * 60)
    
    messages = [
        {"role": "system", "content": "你是一个Python编程助手"},
        {"role": "user", "content": "如何读取JSON文件？"}
    ]
    
    # 第一轮对话
    response1 = await llm_router.chat(messages, provider="deepseek")
    print(f"助手: {response1.content}")
    
    # 添加助手回复到历史
    messages.append({"role": "assistant", "content": response1.content})
    
    # 第二轮对话
    messages.append({"role": "user", "content": "能给个完整例子吗？"})
    response2 = await llm_router.chat(messages, provider="deepseek")
    print(f"助手: {response2.content}")
    print()

async def demo_different_models():
    """不同模型调用示例"""
    print("=" * 60)
    print("不同模型调用示例")
    print("=" * 60)
    
    prompt = "用一句话解释什么是深度学习"
    
    # DeepSeek Chat
    try:
        response = await llm_router.generate(prompt, provider="deepseek", model="deepseek-chat")
        print(f"DeepSeek Chat: {response.content}")
    except Exception as e:
        print(f"DeepSeek 失败: {e}")
    
    # DeepSeek Coder
    try:
        response = await llm_router.generate(prompt, provider="deepseek", model="deepseek-coder")
        print(f"DeepSeek Coder: {response.content}")
    except Exception as e:
        print(f"DeepSeek Coder 失败: {e}")
    
    # MiMo
    try:
        response = await llm_router.generate(prompt, provider="mimo", model="mimo-auto")
        print(f"MiMo Auto: {response.content}")
    except Exception as e:
        print(f"MiMo 失败: {e}")
    
    # 通义千问
    try:
        response = await llm_router.generate(prompt, provider="qwen", model="qwen-turbo")
        print(f"通义千问 Turbo: {response.content}")
    except Exception as e:
        print(f"通义千问失败: {e}")
    
    print()

async def demo_streaming():
    """流式响应示例（如果提供商支持）"""
    print("=" * 60)
    print("流式响应示例")
    print("=" * 60)
    
    # 注意：当前实现是同步的，这里展示概念
    # 实际使用时需要支持SSE
    print("流式响应需要在HTTP层实现SSE支持")
    print("当前框架支持基础的同步调用")
    print()

async def main():
    """主函数"""
    print("多LLM提供商调用示例")
    print("=" * 60)
    print()
    
    # 注意：实际运行需要配置真实的API密钥
    # 这里展示代码结构和使用方式
    
    print("配置说明：")
    print("1. 在 .env 文件中配置各提供商的API密钥")
    print("2. 设置 DEFAULT_PROVIDER 选择默认提供商")
    print("3. 设置 FALLBACK_ORDER 配置降级顺序")
    print()
    
    print("示例 .env 配置：")
    print("""
DEEPSEEK_API_KEY=your-deepseek-api-key
MIMO_API_KEY=your-mimo-api-key
OPENAI_API_KEY=your-openai-api-key
QWEN_API_KEY=your-qwen-api-key
GLM_API_KEY=your-glm-api-key

DEFAULT_PROVIDER=deepseek
FALLBACK_ORDER=["deepseek", "mimo", "qwen", "glm", "openai"]
""")
    
    # 运行示例（需要真实API密钥）
    # await demo_single_provider()
    # await demo_router_with_provider()
    # await demo_router_default_provider()
    # await demo_fallback()
    # await demo_multi_turn_conversation()
    # await demo_different_models()

if __name__ == "__main__":
    asyncio.run(main())
