# CLAUDE.md

## Project Overview

AIT (AI Application Framework) - Full-stack AI application platform with FastAPI backend + Vue3 frontend.

## Architecture

- **Backend**: Python FastAPI on port 8000
- **Frontend**: Vue3 + Vite + Element Plus + VueFlow on port 3000
- **Database**: MongoDB (primary data), ChromaDB (vectors)
- **AI**: Multi-LLM routing (DeepSeek/MiMo/OpenAI/Qwen/GLM/Agnes), LangChain RAG, EasyOCR

## Key Files

- `main.py` — FastAPI app, all API endpoints
- `workflow_engine.py` — DAG workflow engine with 66 node types
- `llm_providers.py` — Multi-provider LLM router with fallback
- `langchain_engine.py` — RAG knowledge base engine
- `ocr_engine.py` — OCR with EasyOCR + AI enhancement
- `frontend-vue/src/views/WorkflowView.vue` — Workflow visual editor (VueFlow)

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

## Workflow Node Format

Nodes stored as: `{id, type, label, config}` (config at top level, NOT nested in data)
Frontend VueFlow wraps as: `{id, type, position, data: {label, config}}`

## Common Patterns

- Variable replacement: `{{variable_name}}` or `{{node_id.field}}`
- Context flattening: node results auto-merged to top-level context
- LLM streaming: skip `{"type": "reasoning"}` chunks, handle `[DONE]`
- MongoDB: query by `id` field (UUID string), not `_id` (ObjectId)

## Frontend API Calls

- Axios instance with `baseURL: '/api/v1'` defined in `frontend-vue/src/api/index.js`
- Local `apiPost` helper in components must prefix URLs with `/api/v1`

## Known Gotchas

- f-string prompts: escape braces as `{{` for literal `{` in LLM prompts
- `chat_stream` with agnes provider: use `enable_thinking=False` to avoid token waste
