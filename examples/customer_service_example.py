"""
智能客服系统示例
展示如何使用AI框架构建智能客服系统
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from fastapi.testclient import TestClient
from typing import List, Dict
import json

class SmartCustomerService:
    """智能客服系统"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.conversation_history = []
    
    def handle_inquiry(self, user_message: str, user_id: str = "anonymous") -> Dict:
        """处理用户咨询"""
        # 1. 意图识别
        intent = self._recognize_intent(user_message)
        
        # 2. 情感分析
        sentiment = self._analyze_sentiment(user_message)
        
        # 3. 生成回复
        response = self._generate_response(user_message, intent, sentiment)
        
        # 4. 记录对话历史
        self.conversation_history.append({
            "user": user_message,
            "bot": response["response"],
            "intent": intent,
            "sentiment": sentiment
        })
        
        return {
            "response": response["response"],
            "intent": intent,
            "sentiment": sentiment,
            "confidence": response["confidence"]
        }
    
    def _recognize_intent(self, message: str) -> str:
        """识别用户意图"""
        # 简单的意图识别逻辑
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["退款", "退货", "退钱"]):
            return "refund"
        elif any(word in message_lower for word in ["投诉", "不满", "差评"]):
            return "complaint"
        elif any(word in message_lower for word in ["咨询", "问题", "如何"]):
            return "inquiry"
        elif any(word in message_lower for word in ["购买", "下单", "买"]):
            return "purchase"
        else:
            return "general"
    
    def _analyze_sentiment(self, message: str) -> str:
        """分析情感"""
        # 调用情感分析接口
        response = self.client.post(
            "/api/v1/sentiment",
            params={"text": message}
        )
        
        if response.status_code == 200:
            return response.json()["sentiment"]
        return "neutral"
    
    def _generate_response(self, message: str, intent: str, sentiment: str) -> Dict:
        """生成回复"""
        # 根据意图和情感生成个性化回复
        if intent == "refund":
            if sentiment == "negative":
                response = "非常抱歉给您带来不便，我理解您的退款需求。请提供订单号，我会立即为您处理。"
            else:
                response = "好的，我来帮您处理退款申请。请提供您的订单号。"
        elif intent == "complaint":
            response = "非常抱歉让您不满意，我会认真记录您的反馈并尽快解决。请问具体是什么问题？"
        elif intent == "inquiry":
            response = "我来帮您解答这个问题。请问您想了解哪方面的信息？"
        elif intent == "purchase":
            response = "感谢您的购买意向！请问您想了解哪款产品？"
        else:
            # 调用通用对话接口
            chat_response = self.client.post(
                "/api/v1/chat",
                json={"message": message}
            )
            if chat_response.status_code == 200:
                return chat_response.json()
            response = "收到您的消息，我会尽快回复。"
        
        return {
            "response": response,
            "confidence": 0.9,
            "sources": ["knowledge_base"]
        }
    
    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history = []

def demo_customer_service():
    """演示智能客服系统"""
    print("智能客服系统演示")
    print("=" * 60)
    
    # 初始化客服系统
    cs = SmartCustomerService()
    
    # 模拟用户对话
    test_conversations = [
        ("我想退款", "user_001"),
        ("这个产品太差了，我要投诉！", "user_002"),
        ("请问如何使用这个功能？", "user_003"),
        ("我想买你们的新产品", "user_004"),
        ("你好", "user_005"),
    ]
    
    for message, user_id in test_conversations:
        print(f"\n用户 [{user_id}]: {message}")
        
        result = cs.handle_inquiry(message, user_id)
        
        print(f"客服回复: {result['response']}")
        print(f"意图: {result['intent']}")
        print(f"情感: {result['sentiment']}")
        print("-" * 60)
    
    # 显示对话历史
    print("\n对话历史:")
    print("-" * 60)
    for i, conv in enumerate(cs.get_conversation_history(), 1):
        print(f"{i}. 用户: {conv['user']}")
        print(f"   客服: {conv['bot']}")
        print(f"   意图: {conv['intent']} | 情感: {conv['sentiment']}")
        print()

def demo_content_generation():
    """演示内容生成"""
    print("\n内容生成演示")
    print("=" * 60)
    
    client = TestClient(app)
    
    # 测试不同类型的内容生成
    test_cases = [
        {
            "topic": "Python编程入门",
            "style": "教程风格",
            "length": "short"
        },
        {
            "topic": "人工智能发展趋势",
            "style": "专业分析",
            "length": "medium"
        },
        {
            "topic": "健康饮食指南",
            "style": "科普文章",
            "length": "long"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {case['topic']}")
        print(f"风格: {case['style']} | 长度: {case['length']}")
        
        response = client.post(
            "/api/v1/content/generate",
            json=case
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"生成内容长度: {data['word_count']}字")
            print(f"预计阅读时间: {data['reading_time']}")
        else:
            print("生成失败")
        
        print("-" * 60)

def demo_recommendation_system():
    """演示推荐系统"""
    print("\n推荐系统演示")
    print("=" * 60)
    
    client = TestClient(app)
    
    # 测试不同场景的推荐
    test_cases = [
        {
            "user_id": "user_001",
            "context": {"time": "morning", "device": "desktop"},
            "top_k": 5
        },
        {
            "user_id": "user_002",
            "context": {"time": "evening", "device": "mobile"},
            "top_k": 3
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: 用户 {case['user_id']}")
        print(f"场景: {case['context']}")
        
        response = client.post(
            "/api/v1/recommendations",
            json=case
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"推荐结果 ({len(data['recommendations'])}项):")
            for j, rec in enumerate(data['recommendations']):
                print(f"  {j+1}. {rec['title']} (分数: {data['scores'][j]:.2f})")
        else:
            print("推荐失败")
        
        print("-" * 60)

if __name__ == "__main__":
    print("AI应用通用框架 - 业务场景演示")
    print("=" * 60)
    
    try:
        # 演示智能客服
        demo_customer_service()
        
        # 演示内容生成
        demo_content_generation()
        
        # 演示推荐系统
        demo_recommendation_system()
        
        print("=" * 60)
        print("所有演示完成!")
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
