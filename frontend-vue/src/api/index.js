import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 对话管理
export const getConversations = () => api.get('/conversations')
export const getConversation = (id) => api.get(`/conversations/${id}`)
export const createConversation = (title, provider) => api.post('/conversations', { title, provider })
export const deleteConversation = (id) => api.delete(`/conversations/${id}`)

// 流式对话（SSE via Fetch）
export const chatStream = (conversationId, message, provider, systemPrompt, images, onChunk, onDone, onToolEvent, options = {}) => {
  const body = { conversation_id: conversationId, message, provider, web_search: options.web_search === true }
  if (options.enable_thinking !== undefined) body.enable_thinking = options.enable_thinking
  if (systemPrompt) body.system_prompt = systemPrompt
  if (images && images.length) body.images = images
  fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: options.signal
  }).then(async response => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let done = false
    while (true) {
      const { done: streamDone, value } = await reader.read()
      if (streamDone) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (data === '[DONE]') { done = true; continue }
        try {
          const parsed = JSON.parse(data)
          if (parsed.reasoning && onToolEvent) onToolEvent({ type: 'reasoning', data: parsed.reasoning })
          if (parsed.content && parsed.content !== '[DONE]') onChunk(parsed.content)
          if (parsed.status && onToolEvent) onToolEvent({ type: 'status', message: parsed.status })
          if (parsed.intent && onToolEvent) onToolEvent({ type: 'intent', data: parsed.intent })
          if (parsed.thought && onToolEvent) onToolEvent({ type: 'thought', data: parsed.thought, step_id: parsed.step_id })
          if (parsed.tool_status && onToolEvent) onToolEvent({ type: 'status', message: parsed.tool_status })
          if (parsed.tool_result && onToolEvent) onToolEvent({ type: 'result', data: parsed.tool_result })
          if (parsed.clarification && onToolEvent) onToolEvent({ type: 'clarification', question: parsed.clarification })
          if (parsed.task_start && onToolEvent) onToolEvent({ type: 'task_start', data: parsed.task_start })
          if (parsed.step_complete && onToolEvent) onToolEvent({ type: 'step_complete', data: parsed.step_complete })
          if (parsed.suggestions) { onDone && onDone(null, parsed.suggestions); return }
          if (parsed.error) { onDone && onDone(parsed.error); return }
        } catch (e) {}
      }
    }
    if (!done) { onDone && onDone() }
  }).catch(err => onDone && onDone(err.message))
}

// WebSocket 流式对话（首包更快）
let wsConnection = null
export const chatStreamWS = (conversationId, message, provider, systemPrompt, images, onChunk, onDone, onToolEvent, options = {}) => {
  // 关闭旧连接
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.close()
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/chat/ws`)
  wsConnection = ws

  ws.onopen = () => {
  const body = { conversation_id: conversationId, message, provider, web_search: options.web_search === true, enable_thinking: options.enable_thinking !== false }
    if (systemPrompt) body.system_prompt = systemPrompt
    if (images && images.length) body.images = images
    ws.send(JSON.stringify(body))
  }

  ws.onmessage = (event) => {
    const data = event.data
    if (!data.startsWith('data: ')) return
    const payload = data.slice(6).trim()
    if (payload === '[DONE]') { onDone && onDone(); return }
    try {
      const parsed = JSON.parse(payload)
      if (parsed.content && parsed.content !== '[DONE]') onChunk(parsed.content)
      if (parsed.status && onToolEvent) onToolEvent({ type: 'status', message: parsed.status })
      if (parsed.intent && onToolEvent) onToolEvent({ type: 'intent', data: parsed.intent })
      if (parsed.thought && onToolEvent) onToolEvent({ type: 'thought', data: parsed.thought })
      if (parsed.tool_status && onToolEvent) onToolEvent({ type: 'status', message: parsed.tool_status })
      if (parsed.tool_result && onToolEvent) onToolEvent({ type: 'result', data: parsed.tool_result })
      if (parsed.task_start && onToolEvent) onToolEvent({ type: 'task_start', data: parsed.task_start })
      if (parsed.step_complete && onToolEvent) onToolEvent({ type: 'step_complete', data: parsed.step_complete })
      if (parsed.suggestions) { onDone && onDone(null, parsed.suggestions); return }
      if (parsed.error) { onDone && onDone(parsed.error); return }
    } catch (e) {}
  }

  ws.onerror = (err) => { onDone && onDone('WebSocket error') }
  ws.onclose = () => { wsConnection = null }
}

// 智能对话
export const chat = (message, provider) => api.post('/chat/provider', { message, provider })

// 内容生成
export const generateContent = (topic, style, length) => api.post('/content/generate', { topic, style, length })

// 推荐系统
export const getRecommendations = (userId, topK = 5) => api.post('/recommendations', { user_id: userId, top_k: topK })

// OCR识别
export const ocrRecognize = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/ocr', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
}
export const ocrEnhance = (text) => {
  return api.post(`/ocr/enhance?text=${encodeURIComponent(text)}`)
}

// 情感分析
export const sentimentAnalysis = (text) => api.post('/sentiment', null, { params: { text } })

// 获取可用提供商
export const getProviders = () => api.get('/llm/providers')

// 健康检查
export const healthCheck = () => api.get('/health')

// 工作台数据
export const getDashboard = () => api.get('/dashboard')

// 智能体
export const getAgents = () => api.get('/agents')
export const createAgent = (data) => api.post('/agents', data)
export const deleteAgent = (id) => api.delete(`/agents/${id}`)

// 配置
export const getSettings = () => api.get('/settings')
export const saveSettings = (data) => api.post('/settings', data)
export const getModelList = (apiKey, baseUrl) => api.get(`/llm/models?api_key=${encodeURIComponent(apiKey)}&base_url=${encodeURIComponent(baseUrl)}`)
export const testLLM = (provider, apiKey, baseUrl, model) => api.post(`/llm/test?provider=${provider}&api_key=${encodeURIComponent(apiKey)}&base_url=${encodeURIComponent(baseUrl)}&model=${encodeURIComponent(model)}`)
export const testImageModel = (apiKey, baseUrl, model) => api.post(`/llm/test-image?api_key=${encodeURIComponent(apiKey)}&base_url=${encodeURIComponent(baseUrl)}&model=${encodeURIComponent(model)}`)
export const testVideoModel = (apiKey, baseUrl, model) => api.post(`/llm/test-video?api_key=${encodeURIComponent(apiKey)}&base_url=${encodeURIComponent(baseUrl)}&model=${encodeURIComponent(model)}`)

// 任务管理
export const getTask = (taskId) => api.get(`/tasks/${taskId}`)
export const listTasks = (conversationId) => {
  const params = conversationId ? { conversation_id: conversationId } : {}
  return api.get('/tasks', { params })
}
export const resumeTask = (taskId, onEvent) => {
  fetch(`/api/v1/tasks/${taskId}/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }).then(async response => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (data === '[DONE]') { onEvent({ type: 'done' }); return }
        try {
          onEvent(JSON.parse(data))
        } catch (e) {}
      }
    }
    onEvent({ type: 'done' })
  }).catch(err => onEvent({ type: 'error', content: err.message }))
}

// LangChain
export const agentChat = (message, provider) => {
  return api.post('/langchain/agent/chat', { message, provider })
}

export const langchainAgentChat = agentChat

// 代码生成（流式）
export const codeGenerateStream = (description, lang, provider, onEvent) => {
  fetch('/api/v1/codegen/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: `${description}|${lang}`, provider })
  }).then(async response => {
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (data === '[DONE]') { onEvent({ type: 'done_all' }); return }
        try {
          onEvent(JSON.parse(data))
        } catch (e) {}
      }
    }
    onEvent({ type: 'done_all' })
  }).catch(err => onEvent({ type: 'error', content: err.message }))
}

export const langchainToolExecute = (toolName, input = '') => {
  return api.post(`/langchain/tools/execute?tool_name=${toolName}&input=${encodeURIComponent(input)}`)
}

export const langchainToolList = () => api.get('/langchain/tools/list')

// 工作流
export const getWorkflows = () => api.get('/workflows')
export const createWorkflow = (data) => api.post('/workflows', data)
export const getWorkflow = (id) => api.get(`/workflows/${id}`)
export const updateWorkflow = (id, data) => api.put(`/workflows/${id}`, data)
export const deleteWorkflow = (id) => api.delete(`/workflows/${id}`)
export const runWorkflow = (id, inputs = {}) => api.post(`/workflows/${id}/run`, { inputs }, { timeout: 300000 })
export const runWorkflowStream = async (id, inputs, onEvent, signal) => {
  const resp = await fetch(`/api/v1/workflows/${id}/run-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ inputs }),
    signal
  })
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const text = decoder.decode(value)
    const lines = text.split('\n')
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const event = JSON.parse(line.slice(6))
          onEvent(event)
        } catch {}
      }
    }
  }
}
export const getWorkflowRuns = (id) => api.get(`/workflows/${id}/runs`)
export const getWorkflowRun = (runId) => api.get(`/workflow-runs/${runId}`)
export const exportWorkflow = (id) => api.get(`/workflows/${id}/export`)
export const importWorkflow = (data) => api.post('/workflows/import', data)
export const saveWorkflowVersion = (id, comment = '') => api.post(`/workflows/${id}/versions`, { comment })
export const getWorkflowVersions = (id) => api.get(`/workflows/${id}/versions`)
export const getWorkflowVersion = (id, version) => api.get(`/workflows/${id}/versions/${version}`)
export const restoreWorkflowVersion = (id, version) => api.post(`/workflows/${id}/versions/${version}/restore`)
export const deleteWorkflowVersion = (id, version) => api.delete(`/workflows/${id}/versions/${version}`)

// 知识库
export const ragAddText = (text, metadata) => {
  const params = new URLSearchParams()
  if (text) params.append('text', text)
  return api.post(`/langchain/rag/add?${params.toString()}`, null)
}
export const ragAddFiles = (files) => {
  const formData = new FormData()
  for (const file of files) {
    formData.append('uploaded_files', file)
  }
  return api.post('/langchain/rag/add', formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000 })
}
export const ragAddFile = (file) => ragAddFiles([file])
export const ragQuery = (query, topK = 3, provider = null, useAi = false) => {
  const params = new URLSearchParams({ query, top_k: topK, use_ai: useAi })
  if (provider) params.append('provider', provider)
  return api.post(`/langchain/rag/query?${params.toString()}`)
}
export const ragClear = () => api.post('/langchain/rag/clear')
export const ragStatus = () => api.get('/langchain/status')
export const ragListFiles = () => api.get('/langchain/rag/files')
export const ragDownloadFile = (fileId) => `/api/v1/langchain/rag/files/${fileId}/download`
export const ragDeleteFile = (fileId) => api.delete(`/langchain/rag/files/${fileId}`)

export default api
