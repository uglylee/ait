# AI应用通用框架 - 快速开始指南

## 1. 环境准备

### 系统要求
- Python 3.8+
- Docker 20.10+ (可选)
- Docker Compose 2.0+ (可选)

### 安装依赖
```bash
# 克隆项目
git clone <repository-url>
cd ai-framework

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或者
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 2. 配置环境

### 复制环境变量文件
```bash
cp .env.example .env
```

### 编辑配置文件
```bash
# 编辑 .env 文件，根据需要修改配置
# 主要配置项：
# - DATABASE_URL: 数据库连接
# - REDIS_URL: Redis连接
# - MILVUS_HOST: Milvus地址
# - DEFAULT_LLM_MODEL: 默认大模型
```

## 3. 启动服务

### 方式一：直接启动（推荐用于开发）
```bash
# 启动API服务
python main.py

# 或者使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 方式二：Docker启动（推荐用于生产）
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

## 4. 访问服务

### API文档
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 健康检查
```bash
curl http://localhost:8000/api/v1/health
```

## 5. 快速测试

### 测试智能对话
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，请问如何使用这个框架？"}'
```

### 测试内容生成
```bash
curl -X POST http://localhost:8000/api/v1/content/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "人工智能发展趋势", "style": "专业分析"}'
```

### 测试推荐系统
```bash
curl -X POST http://localhost:8000/api/v1/recommendations \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_123", "top_k": 5}'
```

## 6. 运行示例代码

### 基础使用示例
```bash
python examples/basic_usage.py
```

### 智能客服示例
```bash
python examples/customer_service_example.py
```

## 7. 项目结构说明

```
ai-framework/
├── main.py                 # FastAPI应用入口
├── config.py              # 配置管理
├── requirements.txt       # Python依赖
├── Dockerfile            # Docker配置
├── docker-compose.yml    # Docker Compose配置
├── .env.example          # 环境变量示例
├── README.md             # 项目文档
├── SUMMARY.md            # 项目总结
├── QUICKSTART.md         # 快速开始指南
├── examples/             # 示例代码
│   ├── basic_usage.py    # 基础使用示例
│   └── customer_service_example.py  # 智能客服示例
└── docs/                 # 文档
    └── market_analysis.md  # 市场分析文档
```

## 8. 常见问题

### Q1: 启动时报错 "ModuleNotFoundError: No module named 'xxx'"
**解决方案**:
```bash
# 确保已安装所有依赖
pip install -r requirements.txt

# 如果使用虚拟环境，确保已激活
source venv/bin/activate
```

### Q2: Docker启动失败
**解决方案**:
```bash
# 检查Docker是否运行
docker info

# 检查端口是否被占用
netstat -an | grep 8000

# 重新构建镜像
docker-compose build --no-cache
```

### Q3: API响应慢
**解决方案**:
1. 检查网络连接
2. 增加服务器资源
3. 优化模型配置
4. 使用缓存

### Q4: 如何添加新的API接口？
**解决方案**:
```python
# 在 main.py 中添加新的路由
@app.post("/api/v1/new-endpoint")
async def new_endpoint(request: NewRequest):
    # 实现业务逻辑
    return {"result": "success"}
```

## 9. 开发指南

### 添加新的AI能力
1. 在能力层创建新模块
2. 实现相应的接口
3. 在应用层创建新应用
4. 添加测试用例
5. 更新文档

### 集成新的模型
1. 在模型层添加新的模型管理器
2. 实现模型加载和推理逻辑
3. 在配置文件中添加模型配置
4. 更新requirements.txt

### 数据库迁移
```bash
# 使用Alembic进行数据库迁移
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## 10. 部署指南

### 开发环境部署
```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 或者直接启动Python服务
python main.py
```

### 生产环境部署
```bash
# 1. 构建Docker镜像
docker-compose build

# 2. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 3. 配置反向代理（Nginx）
# 4. 配置SSL证书
# 5. 配置监控和日志
```

### 云环境部署
```bash
# 使用Terraform部署到AWS
terraform init
terraform plan
terraform apply

# 或者使用Kubernetes
kubectl apply -f k8s/
```

## 11. 监控和运维

### 查看服务状态
```bash
# 查看容器状态
docker-compose ps

# 查看日志
docker-compose logs -f api

# 查看资源使用
docker stats
```

### 性能监控
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

### 日志查看
```bash
# 查看应用日志
tail -f logs/app.log

# 查看Docker日志
docker-compose logs -f api
```

## 12. 贡献指南

### 报告问题
1. 在GitHub Issues中创建新问题
2. 提供详细的问题描述
3. 提供复现步骤
4. 提供环境信息

### 提交代码
1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 13. 许可证

MIT License

## 14. 联系方式

- **项目地址**: [GitHub Repository]
- **问题反馈**: [GitHub Issues]
- **邮件联系**: [your-email@example.com]
