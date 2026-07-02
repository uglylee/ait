# AIT - AI 应用通用框架

FastAPI + Vue3 全栈 AI 应用框架，集成多 LLM 提供商、RabbitMQ 消息队列、可视化工作流引擎、RAG 知识库等能力。

## 功能特性

- **多 LLM 路由** — DeepSeek / MiMo / OpenAI / 通义千问 / 智谱 GLM / Agnes，多 Key 轮询 + 自动降级
- **消息队列架构** — RabbitMQ 异步处理 LLM 请求，支持高并发，不阻塞主服务
- **自动化 Agent** — 多轮工具调用循环，支持代码执行、文件操作、Web 搜索等 9 种工具
- **可视化工作流** — 66 种节点类型 + 14 种工具，拖拽式 DAG 编辑器（VueFlow）
- **RAG 知识库** — ChromaDB 向量检索，支持 12 种格式批量上传，可选 AI 回答
- **多模态对话** — 文本 / 图片输入，SSE 流式输出 + 思考链展示
- **OCR 识别** — EasyOCR + AI 后处理增强
- **代码生成** — 多语言代码生成与执行
- **图像/视频生成** — 集成多模态生成能力

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / Uvicorn |
| 前端 | Vue 3 / Vite / Element Plus / VueFlow |
| 数据库 | MongoDB / ChromaDB / Redis |
| 消息队列 | RabbitMQ (aio-pika) |
| AI | LangChain / HuggingFace Embeddings |
| HTTP | httpx (异步) |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Docker (运行 MongoDB + Redis + RabbitMQ)

### 1. 克隆项目

```bash
git clone https://github.com/uglylee/ait.git
cd ait
```

### 2. 启动基础服务

```bash
docker-compose -f docker-compose.db.yml up -d
```

启动 MongoDB、Redis、RabbitMQ。

### 3. 安装依赖并启动后端

```bash
pip install -r requirements.txt
python main.py
```

后端运行在 `http://localhost:8000`，API 文档: `http://localhost:8000/docs`

### 4. 启动 MQ Worker（必须）

```bash
python mq_worker.py
```

MQ Worker 消费 RabbitMQ 中的 LLM 请求。**不启动 Worker 则 AI 对话和自动化功能不可用。**

### 5. 启动前端

```bash
cd frontend-vue
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

前端运行在 `http://localhost:3000`

### 6. 配置 LLM

在前端设置页面（`/settings`）填入至少一个 LLM 提供商的 API Key，或直接调用 API：

```bash
curl -X POST http://localhost:8000/api/v1/settings \
  -H "Content-Type: application/json" \
  -d '{"deepseek_key": "sk-your-key", "default_provider": "deepseek"}'
```

## 项目结构

```
ait/
├── main.py                 # FastAPI 入口，所有 API 端点
├── mq.py                   # RabbitMQ 发布/订阅封装
├── mq_worker.py            # MQ Worker（消费 LLM 请求）
├── mq_worker_chat.py       # 仅处理普通对话的 Worker
├── mq_worker_auto.py       # 仅处理自动化的 Worker
├── task_queue.py           # 异步任务队列
├── llm_providers.py         # 多 LLM 提供商路由 + 多 Key 轮询
├── llm_config.py            # 从 MongoDB 加载 LLM 配置
├── langchain_engine.py      # RAG 知识库引擎 (ChromaDB + Embeddings)
├── workflow_engine.py       # 工作流引擎 (66种节点，Redis取消)
├── orchestrator.py          # 任务编排器
├── ocr_engine.py            # OCR 识别引擎
├── config.py                # 全局配置
├── kb_files/                # 知识库上传文件持久存储
├── chroma_db/               # ChromaDB 向量数据
├── requirements.txt         # Python 依赖
├── docker-compose.db.yml    # MongoDB + Redis + RabbitMQ Docker
├── frontend-vue/            # Vue3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── ChatView.vue        # AI 对话
│   │   │   ├── WorkflowView.vue    # 工作流编辑器
│   │   │   ├── KnowledgeView.vue   # 知识库管理
│   │   │   └── ...
│   │   ├── api/
│   │   │   └── index.js            # API 封装
│   │   └── router/
│   │       └── index.js            # 路由配置
│   ├── package.json
│   └── vite.config.js
└── test_all_nodes.py        # 工作流节点测试
```

## 架构说明

### 消息队列架构

```
前端 → FastAPI → RabbitMQ → MQ Worker → LLM API
                  (llm_chat)  ↗              ↓
                  (llm_auto)  ↗    Redis Pub/Sub → FastAPI → SSE → 前端
```

- **main.py**: 接收前端请求，发布到 RabbitMQ 队列，订阅 Redis 接收结果
- **mq_worker.py**: 消费 RabbitMQ 消息，调用 LLM API，通过 Redis 推送结果
- **队列**: `llm_chat`（普通对话）、`llm_auto`（自动化 Agent）

### 自动化 Agent

自动化模式下，AI 会自动执行多轮工具调用：
1. 用户发送任务描述
2. AI 分析任务，决定使用哪个工具
3. 执行工具，获取结果
4. 根据结果决定下一步（继续/完成/失败）
5. 最多执行 50 轮，支持手动取消

可用工具：calculator, run_command, web_search, code_generate, open_url, open_file, open_app, list_dir, datetime

## 工作流节点类型 (66种)

### 核心节点
输入、输出、LLM 调用、工具调用(14种)、条件分支、多分支、循环、并行、延时、重试、错误处理、子工作流

### 数据处理
数学计算、日期时间、CSV 解析、Excel 读取/写入、数据过滤、数据排序、数据合并、去重、透视表、相关性分析、统计计算、JSON 构建、正则替换、哈希编码、UUID 生成、类型转换

### 办公自动化
Word 读取/写入、PDF 生成、图表生成、邮件发送（支持附件）、日历事件、模板渲染、审批流程

### AI 扩展
情感分析、文本摘要、文本翻译、图像生成、Markdown→HTML

### 网络与系统
HTTP 请求、WebSocket、SSH 执行、数据库查询、文件操作、日志分析、备份、网络 Ping

### 安全与认证
加密/解密、JWT 生成、哈希校验

### 调度与通知
定时触发、Webhook 触发、通知推送

## 常见问题

### AI 对话无响应

1. 确认 `mq_worker.py` 正在运行（`ps aux | grep mq_worker`）
2. 确认 RabbitMQ 正常（访问 `http://localhost:15672`，用户 `ai_rabbit`）
3. 确认已配置至少一个有效的 LLM API Key

### Worker 启动报错

```bash
# 缺少依赖
pip install aio-pika langchain-core langchain-community langchain-text-splitters

# 然后重启
python mq_worker.py
```

## License

MIT
