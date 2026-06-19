"""
AI应用通用框架 - 基础使用示例
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from fastapi.testclient import TestClient

def test_chat():
    """测试智能对话接口"""
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "你好，请问如何使用这个框架？",
            "context": {"user_id": "user_123"}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    print("智能对话测试结果:")
    print(f"  回复: {data['response']}")
    print(f"  置信度: {data['confidence']}")
    print(f"  来源: {data['sources']}")
    print()

def test_content_generation():
    """测试内容生成接口"""
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/content/generate",
        json={
            "topic": "人工智能在医疗领域的应用",
            "style": "专业分析",
            "length": "medium"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    print("内容生成测试结果:")
    print(f"  内容长度: {data['word_count']}字")
    print(f"  阅读时间: {data['reading_time']}")
    print()

def test_recommendation():
    """测试推荐系统接口"""
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/recommendations",
        json={
            "user_id": "user_123",
            "context": {"time": "evening", "device": "mobile"},
            "top_k": 5
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    print("推荐系统测试结果:")
    print(f"  推荐项目数: {len(data['recommendations'])}")
    for i, rec in enumerate(data['recommendations']):
        print(f"  {i+1}. {rec['title']} (分数: {data['scores'][i]:.2f})")
    print()

def test_sentiment_analysis():
    """测试情感分析接口"""
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/sentiment",
        params={"text": "这个框架非常好用，功能很强大！"}
    )
    
    assert response.status_code == 200
    data = response.json()
    print("情感分析测试结果:")
    print(f"  情感: {data['sentiment']}")
    print(f"  置信度: {data['confidence']}")
    print(f"  详细: {data['details']}")
    print()

def test_health_check():
    """测试健康检查接口"""
    client = TestClient(app)
    
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    print("健康检查测试结果:")
    print(f"  状态: {data['status']}")
    for service, status in data['services'].items():
        print(f"  {service}: {status}")
    print()

if __name__ == "__main__":
    print("AI应用通用框架 - 基础使用示例")
    print("=" * 50)
    
    try:
        test_health_check()
        test_chat()
        test_content_generation()
        test_recommendation()
        test_sentiment_analysis()
        
        print("=" * 50)
        print("所有测试完成!")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
