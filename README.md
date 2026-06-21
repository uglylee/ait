# AIT - AI 应用通用框架

FastAPI + Vue3 全栈 AI 应用框架，集成多 LLM 提供商、可视化工作流引擎、RAG 知识库、OCR、多模态对话等能力。

## 功能特性

- **多 LLM 路由** — DeepSeek / MiMo / OpenAI / 通义千问 / 智谱 GLM / Agnes，自动降级切换
- **可视化工作流** — 66 种节点类型 + 14 种工具，拖拽式 DAG 编辑器（VueFlow）
- **AI 智能创建** — 自然语言描述自动生成工作流，支持模板库一键创建
- **实时执行** — SSE 流式推送节点执行状态，支持手动停止/取消
- **RAG 知识库** — ChromaDB 向量检索，支持 12 种格式批量上传，可选 AI 回答，文件追溯下载
- **多模态对话** — 文本 / 图片 / 语音输入，SSE 流式输出 + 思考链展示
- **OCR 识别** — EasyOCR + AI 后处理增强
- **代码生成** — 多语言代码生成与执行
- **批量操作** — 批量删除、批量导出工作流
- **执行队列** — 支持并发控制的工作流执行队列
- **触发器系统** — Webhook 触发、定时调度
- **邮件发送** — SMTP 发送 + 文件附件 + 测试连接
- **PDF 生成** — 支持中文字体（自动检测系统字体）

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11+ / FastAPI / Uvicorn |
| 前端 | Vue 3 / Vite / Element Plus / VueFlow |
| 数据库 | MongoDB / ChromaDB / Redis |
| AI | LangChain / EasyOCR / HuggingFace Embeddings |
| HTTP | httpx (异步) |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- MongoDB + Redis (Docker 或本地)

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
├── main.py                 # FastAPI 入口，所有 API 端点
├── workflow_engine.py       # 工作流引擎 (66种节点，Redis取消)
├── llm_providers.py         # 多 LLM 提供商路由
├── llm_config.py            # LLM 配置管理
├── langchain_engine.py      # RAG 知识库引擎 (ChromaDB + Embeddings)
├── ocr_engine.py            # OCR 识别引擎
├── orchestrator.py          # 任务编排器
├── config.py                # 全局配置
├── kb_files/                # 知识库上传文件持久存储
├── chroma_db/               # ChromaDB 向量数据
├── requirements.txt         # Python 依赖
├── docker-compose.db.yml    # MongoDB + Redis Docker
├── Dockerfile               # 后端 Docker
├── .env.example             # 环境变量模板
├── frontend-vue/            # Vue3 前端
│   ├── src/
│   │   ├── views/
│   │   │   ├── ChatView.vue        # AI 对话
│   │   │   ├── WorkflowView.vue    # 工作流编辑器
│   │   │   ├── KnowledgeView.vue   # 知识库管理
│   │   │   ├── CodegenView.vue     # 代码生成
│   │   │   └── ...
│   │   ├── api/
│   │   │   └── index.js            # API 封装
│   │   └── router/
│   │       └── index.js            # 路由配置
│   ├── package.json
│   └── vite.config.js
└── test_all_nodes.py        # 工作流节点测试
```

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

## 工作流执行

- **实时状态** — SSE 流式推送每个节点执行状态（运行中/完成/失败）
- **手动停止** — 执行中可点击停止按钮，当前节点完成后立即终止
- **自动取消** — 关闭对话框、关闭页面时自动发送取消信号
- **取消机制** — Redis 标记 + 内存标记双重保障

## 知识库

- **文件上传** — 支持批量上传 12 种格式：PDF/Word/Excel/PPT/TXT/CSV/HTML/MD/JSON/XML/LOG
- **文件追溯** — 搜索结果显示来源文档名称，支持直接下载原文
- **检索模式** — 纯向量检索（默认）或 AI 回答（可选开关）
- **RAG 流程** — 用户问题 → Embedding 编码 → 向量检索 → 拼接 Prompt → LLM 生成回答
- **清空功能** — 一键清空所有上传文件和向量数据
- **并发安全** — 线程锁保护上传/搜索/清空并发操作

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

# Redis
REDIS_URL=redis://:ai_redis_2024@localhost:6379
```

## License

MIT
