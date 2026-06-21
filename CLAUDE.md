# CLAUDE.md

## Project Overview

AIT (AI Application Framework) - Full-stack AI application platform with FastAPI backend + Vue3 frontend.

## Architecture

- **Backend**: Python FastAPI on port 8000
- **Frontend**: Vue3 + Vite + Element Plus + VueFlow on port 3000
- **Database**: MongoDB (primary data), ChromaDB (vectors), Redis (cancel signals)
- **AI**: Multi-LLM routing (DeepSeek/MiMo/OpenAI/Qwen/GLM/Agnes), LangChain RAG, EasyOCR

## Key Files

- `main.py` — FastAPI app, all API endpoints, SSE streaming
- `workflow_engine.py` — DAG workflow engine with 66 node types, Redis-based cancel
- `llm_providers.py` — Multi-provider LLM router with fallback
- `llm_config.py` — LLM config management from MongoDB settings
- `langchain_engine.py` — RAG knowledge base engine (ChromaDB + HuggingFace embeddings)
- `ocr_engine.py` — OCR with EasyOCR + AI enhancement
- `frontend-vue/src/views/WorkflowView.vue` — Workflow visual editor (VueFlow)
- `frontend-vue/src/views/KnowledgeView.vue` — Knowledge base management
- `kb_files/` — Persistent storage for uploaded knowledge base files

## Development

### Start backend
```bash
python main.py
```

### Start frontend
```bash
cd frontend-vue && npm run dev -- --host 0.0.0.0 --port 3000
```

### Run tests
```bash
python test_all_nodes.py
```

## Code Conventions

- Backend: Python 3.11+, type hints, async/await
- Frontend: Vue3 Composition API, Element Plus components
- API: RESTful, prefix `/api/v1/`
- Database: MongoDB with UUID string IDs (`id` field, not `_id`)
- LLM streaming: SSE with `data: {...}\n\n` format, `[DONE]` terminator
- Cancel mechanism: Redis key `wf:cancel:{run_id}` + in-memory set

## Workflow Node Format

Nodes stored as: `{id, type, label, config}` (config at top level, NOT nested in data)
Frontend VueFlow wraps as: `{id, type, position, data: {label, config}}`

## Workflow Execution (SSE Streaming)

- Endpoint: `POST /api/v1/workflows/{id}/run-stream` returns SSE events
- Events: `start` → `node_start` → `node_done`/`node_error` → `done`
- Cancel: `POST /api/v1/workflows/{id}/cancel` sets Redis key, checked between nodes
- Generator `finally` block also calls `cancel_workflow()` on disconnect

## Knowledge Base (RAG)

- Embedding: HuggingFace `all-MiniLM-L6-v2` (preloaded at startup)
- Vector store: ChromaDB persistent storage in `./chroma_db`
- File storage: uploaded files saved to `./kb_files/` with timestamp prefix
- Upload: supports PDF, Word, Excel, PPT, TXT, CSV, HTML, MD, JSON, XML, LOG (batch upload)
- Query flow: User question → Embedding encoding → Vector search → Splice prompt → LLM answer
- `use_ai=false` (default): returns only search results; `use_ai=true`: full RAG with LLM
- Search results include source `file_name` and `file_id` for download
- Thread-safe: `threading.Lock` protects concurrent add/search/clear operations
- Clear: deletes ChromaDB collection + directory, resets `_cleared` flag

## Common Patterns

- Variable replacement: `{{variable_name}}` or `{{node_id.field}}`
- Context flattening: node results auto-merged to top-level context
- LLM streaming: skip `{"type": "reasoning"}` chunks, handle `[DONE]`
- MongoDB: query by `id` field (UUID string), not `_id` (ObjectId)
- Thread-safe cancel: `_cancelled_run_ids` set + Redis key checked per-node

## Frontend API Calls

- Axios instance with `baseURL: '/api/v1'` defined in `frontend-vue/src/api/index.js`
- Local `apiPost` helper in components must prefix URLs with `/api/v1`
- `runWorkflowStream` uses fetch ReadableStream for SSE
- `sendBeacon` used for cancel on page unload

## Known Gotchas

- f-string prompts: escape braces as `{{` for literal `{` in LLM prompts
- `chat_stream` with agnes provider: use `enable_thinking=False` to avoid token waste
- ChromaDB `get_stats()`: reads directly without loading embedding model
- PyPDF needed for PDF upload: `pip install pypdf`
- `langchain.schema` → use `langchain_core.documents` for Document import
- ChromaDB file locks: `clear()` uses `shutil.rmtree` with retries + `gc.collect()`
- uvicorn single worker: SSE streaming blocks cancel API, use Redis for cancel signals
