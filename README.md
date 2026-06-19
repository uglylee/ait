# AIT - AI 应用通用框架

FastAPI + Vue3 全栈 AI 应用框架，集成多 LLM 提供商、可视化工作流引擎、RAG 知识库、OCR、多模态对话等能力。

## 功能特性

- **多 LLM 路由** — DeepSeek / MiMo / OpenAI / 通义千问 / 智谱 GLM / Agnes，自动降级切换
- **可视化工作流** — 46 种节点类型 + 14 种工具，拖拽式 DAG 编辑器（VueFlow）
- **RAG 知识库** — LangChain + ChromaDB 向量检索，支持多文档格式
- **多模态对话** — 文本 / 图片 / 语音输入，SSE 流式输出 + 思考链展示
- **OCR 识别** — EasyOCR + AI 后处理增强
- **代码生成** — 多语言代码生成与执行
- **工作流节点** — 数学计算、日期时间、类型转换、CSV/Excel 解析、正则替换、哈希编码、UUID、文本嵌入、语音转文字、文字转语音、图片处理、Markdown→HTML、WebSocket、HTTP 流式、Ping、URL 缩短、二维码生成/识别、PDF 生成、JSON 对比等

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / Uvicorn |
| 前端 | Vue 3 / Vite / Element Plus / VueFlow |
| 数据库 | MongoDB / ChromaDB |
| AI | LangChain / EasyOCR / PyTorch |
| HTTP | httpx (异步) |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- MongoDB (Docker 或本地)

### 1. 克隆项目

```bash
git clone https://github.com/uglylee/ait.git
cd ait
```

### 2. 启动数据库

```bash
docker-compose -f docker-compose.db.yml up -d
```

### 3. 启动后端

```bash
cp .env.example .env
# 编辑 .env 填入 API Key
pip install -r requirements.txt
python main.py
```

后端运行在 `http://localhost:8000`，API 文档: `http://localhost:8000/docs`

### 4. 启动前端

```bash
cd frontend-vue
npm install
npm run dev -- --host 0.0.0.0 --port 3000
```

前端运行在 `http://localhost:3000`

## 项目结构

```
ait/
├── main.py                 # FastAPI 入口
├── workflow_engine.py       # 工作流引擎 (46种节点)
├── llm_providers.py         # 多 LLM 提供商路由
├── llm_config.py            # LLM 配置管理
├── langchain_engine.py      # RAG 知识库引擎
├── ocr_engine.py            # OCR 识别引擎
├── orchestrator.py          # 任务编排器
├── config.py                # 全局配置
├── requirements.txt         # Python 依赖
├── docker-compose.db.yml    # 数据库 Docker
├── Dockerfile               # 后端 Docker
├── .env.example             # 环境变量模板
├── frontend-vue/            # Vue3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── ChatView.vue      # AI 对话
│   │   │   ├── WorkflowView.vue  # 工作流编辑器
│   │   │   ├── CodegenView.vue   # 代码生成
│   │   │   └── ...
│   │   ├── api/
│   │   │   └── index.js          # API 封装
│   │   └── router/
│   │       └── index.js          # 路由配置
│   ├── package.json
│   └── vite.config.js
└── test_all_nodes.py        # 工作流节点测试
```

## 工作流节点类型

### 数据处理
数学计算、日期时间、类型转换、CSV 解析、Excel 读取、正则替换、哈希编码、UUID 生成

### AI 扩展
文本嵌入、语音转文字、文字转语音、图片处理、Markdown→HTML

### 网络通信
WebSocket、HTTP 流式、网络 Ping、URL 缩短

### 实用工具
二维码生成/识别、PDF 生成、JSON 对比

### 核心节点
输入、LLM 调用、工具调用(14种)、条件分支、数据转换、延时、循环、并行、数据库、文件操作、Webhook、代码执行、图像生成、错误处理、多分支、子工作流、重试、通知推送、输出

## 环境变量

```env
# LLM 提供商
DEEPSEEK_API_KEY=your-key
OPENAI_API_KEY=your-key
QWEN_API_KEY=your-key
GLM_API_KEY=your-key
AGNES_API_KEY=your-key

# 默认提供商
DEFAULT_PROVIDER=deepseek
FALLBACK_ORDER=["deepseek","openai","qwen","glm"]

# 数据库
MONGODB_URL=mongodb://localhost:27017
```

## License

MIT
