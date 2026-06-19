<template>
  <div class="codegen-page">
    <div class="page-header">
      <h1>AI 代码生成</h1>
      <p>输入需求描述，自动生成项目代码</p>
    </div>

    <div class="form-card">
      <div class="form-group">
        <label>项目描述</label>
        <textarea v-model="form.description" rows="3" placeholder="描述你想要的项目，例如：&#10;- 写一个贪吃蛇游戏&#10;- 做一个待办事项网站&#10;- 创建一个Python爬虫"></textarea>
      </div>
      <div class="form-group">
        <label>技术栈</label>
        <div class="lang-btns">
          <button v-for="l in langs" :key="l.value" :class="{ active: form.lang === l.value }" @click="form.lang = l.value">
            {{ l.label }}
          </button>
        </div>
      </div>
      <button class="btn-primary" :disabled="generating || !form.description.trim()" @click="generate">
        {{ generating ? '生成中...' : '生成项目' }}
      </button>
    </div>

    <div v-if="logs.length" class="process-card">
      <div class="card-title">
        <span>生成过程</span>
        <span v-if="done" class="tag-done">完成</span>
        <span v-else-if="failed" class="tag-fail">失败</span>
        <span v-else class="tag-run">运行中</span>
      </div>
      <div class="log-list" ref="logList">
        <div v-for="(log, i) in logs" :key="i" class="log-item" :class="log.type">
          <span class="log-dot" :class="log.type"></span>
          {{ log.text }}
        </div>
      </div>
    </div>

    <div v-if="code" class="code-card">
      <div class="card-title">
        <span>生成代码</span>
        <div class="btn-group">
          <button class="btn-sm" @click="copyCode">复制代码</button>
          <button class="btn-sm btn-run" @click="runCode" :disabled="running">{{ running ? '运行中...' : '运行项目' }}</button>
        </div>
      </div>
      <pre class="code-block"><code>{{ code }}</code></pre>
    </div>

    <div v-if="output" class="output-card">
      <div class="card-title"><span>运行输出</span></div>
      <pre class="output-block">{{ output }}</pre>
    </div>

    <div v-if="htmlPath" class="preview-card">
      <div class="card-title">
        <span>页面预览</span>
        <button class="btn-sm" @click="openBrowser">新窗口打开</button>
      </div>
      <div class="preview-box">
        <iframe :src="'file:///' + htmlPath.replace(/\\\\/g, '/')" sandbox="allow-scripts"></iframe>
      </div>
    </div>

    <div v-if="!logs.length" class="tpl-card">
      <div class="card-title"><span>快捷模板</span></div>
      <div class="tpl-grid">
        <div class="tpl-item" v-for="t in templates" :key="t.name" @click="useTpl(t)">
          <div class="tpl-icon">{{ t.icon }}</div>
          <div class="tpl-name">{{ t.name }}</div>
          <div class="tpl-sub">{{ t.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { getProviders } from '../api'

const form = ref({ description: '', lang: 'python' })
const langs = [
  { label: 'Python', value: 'python' },
  { label: 'HTML/CSS/JS', value: 'html' },
  { label: 'Node.js', value: 'javascript' },
]
const templates = [
  { name: '贪吃蛇', desc: 'Python命令行游戏', lang: 'python', icon: '🐍', full: '用Python写一个命令行贪吃蛇游戏，使用curses库' },
  { name: '待办事项', desc: 'HTML网页应用', lang: 'html', icon: '📝', full: '做一个漂亮的待办事项网页应用，支持添加、完成、删除' },
  { name: '天气查询', desc: 'Python工具', lang: 'python', icon: '🌤', full: '写一个Python命令行天气查询工具' },
  { name: '聊天界面', desc: 'HTML聊天网页', lang: 'html', icon: '💬', full: '做一个好看的聊天机器人网页界面' },
  { name: '时钟应用', desc: 'HTML数字时钟', lang: 'html', icon: '⏰', full: '做一个精美的数字时钟网页，显示当前时间' },
  { name: '计算器', desc: 'HTML计算器', lang: 'html', icon: '🔢', full: '做一个功能完整的计算器网页应用' },
]

const generating = ref(false)
const running = ref(false)
const logs = ref([])
const code = ref('')
const output = ref('')
const done = ref(false)
const failed = ref(false)
const htmlPath = ref('')
const provider = ref('')
const logList = ref(null)
const projectPath = ref('')

onMounted(async () => {
  try {
    const { data } = await getProviders()
    provider.value = data.default_provider || 'agnes'
  } catch (e) { provider.value = 'agnes' }
})

const scrollDown = () => { nextTick(() => { if (logList.value) logList.value.scrollTop = logList.value.scrollHeight }) }

const addLog = (type, text) => { logs.value.push({ type, text }); scrollDown() }

const generate = async () => {
  if (!form.value.description.trim()) return
  generating.value = true
  logs.value = []
  code.value = ''
  output.value = ''
  done.value = false
  failed.value = false
  htmlPath.value = ''
  projectPath.value = ''

  try {
    const resp = await fetch('/api/v1/codegen/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: form.value.description + '|' + form.value.lang, provider: provider.value })
    })
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done: streamDone, value } = await reader.read()
      if (streamDone) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (raw === '[DONE]') { done.value = true; generating.value = false; continue }
        try {
          const evt = JSON.parse(raw)
          if (evt.type === 'status') { addLog('status', evt.content) }
          else if (evt.type === 'code') { code.value += evt.content }
          else if (evt.type === 'output') { output.value += evt.content }
          else if (evt.type === 'error') { addLog('error', evt.content); failed.value = true }
          else if (evt.type === 'done') { projectPath.value = evt.path; addLog('done', '项目路径: ' + evt.path) }
        } catch (e) {}
      }
    }
    if (!failed.value) done.value = true
  } catch (e) {
    addLog('error', '请求失败: ' + e.message)
    failed.value = true
  }
  generating.value = false
}

const copyCode = () => {
  const ta = document.createElement('textarea')
  ta.value = code.value
  document.body.appendChild(ta)
  ta.select()
  document.execCommand('copy')
  document.body.removeChild(ta)
  alert('已复制')
}

const runCode = async () => {
  if (!projectPath.value) return alert('没有可运行的项目')
  running.value = true
  output.value = ''
  htmlPath.value = ''
  try {
    const resp = await fetch('/api/v1/codegen/run?path=' + encodeURIComponent(projectPath.value), { method: 'POST' })
    const data = await resp.json()
    output.value = data.output || data.errors || '完成'
    if (data.path) htmlPath.value = data.path
  } catch (e) {
    output.value = '运行失败: ' + e.message
  }
  running.value = false
}

const openBrowser = () => { if (htmlPath.value) window.open('file:///' + htmlPath.value.replace(/\\/g, '/'), '_blank') }

const useTpl = (t) => { form.value.description = t.full; form.value.lang = t.lang }
</script>

<style scoped>
.codegen-page { max-width: 880px; margin: 0 auto; padding: 24px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 26px; color: #1a1a1a; margin-bottom: 6px; }
.page-header p { color: #999; font-size: 14px; }

.form-card, .process-card, .code-card, .output-card, .preview-card, .tpl-card {
  background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}

.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 14px; font-weight: 500; color: #333; margin-bottom: 8px; }
.form-group textarea {
  width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px;
  font-size: 14px; resize: vertical; font-family: inherit; outline: none;
}
.form-group textarea:focus { border-color: #409eff; }

.lang-btns { display: flex; gap: 8px; }
.lang-btns button {
  padding: 8px 20px; border: 1px solid #ddd; border-radius: 20px;
  font-size: 13px; cursor: pointer; background: #fff; color: #666; transition: all 0.2s;
}
.lang-btns button.active { background: #409eff; color: #fff; border-color: #409eff; }

.btn-primary {
  width: 100%; padding: 12px; background: #409eff; color: #fff; border: none;
  border-radius: 8px; font-size: 15px; cursor: pointer; transition: background 0.2s;
}
.btn-primary:hover { background: #337ecc; }
.btn-primary:disabled { background: #ccc; cursor: not-allowed; }

.card-title {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
  font-size: 14px; font-weight: 600; color: #333;
}
.tag-done { background: #e8f5e9; color: #4caf50; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 400; }
.tag-fail { background: #fce4ec; color: #f44336; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 400; }
.tag-run { background: #e3f2fd; color: #2196f3; padding: 2px 8px; border-radius: 10px; font-size: 12px; font-weight: 400; }

.log-list { max-height: 180px; overflow-y: auto; background: #f8f9fa; border-radius: 8px; padding: 12px; }
.log-item { padding: 4px 0; font-size: 13px; color: #555; display: flex; align-items: center; gap: 8px; }
.log-item.error { color: #f44336; }
.log-item.done { color: #4caf50; }
.log-dot { width: 6px; height: 6px; border-radius: 50%; background: #bbb; flex-shrink: 0; }
.log-dot.status { background: #2196f3; }
.log-dot.error { background: #f44336; }
.log-dot.done { background: #4caf50; }

.btn-group { display: flex; gap: 6px; }
.btn-sm {
  padding: 6px 14px; border: 1px solid #ddd; border-radius: 6px;
  font-size: 12px; cursor: pointer; background: #fff; color: #666; transition: all 0.2s;
}
.btn-sm:hover { border-color: #409eff; color: #409eff; }
.btn-run { background: #409eff; color: #fff; border-color: #409eff; }
.btn-run:hover { background: #337ecc; }

.code-block {
  background: #1e1e2e; color: #cdd6f4; padding: 16px; border-radius: 8px;
  font-size: 13px; line-height: 1.6; overflow: auto; max-height: 400px;
  white-space: pre-wrap; word-break: break-all; font-family: Consolas, monospace;
}
.output-block {
  background: #1a1a1a; color: #4ade80; padding: 16px; border-radius: 8px;
  font-size: 13px; line-height: 1.6; overflow: auto; max-height: 300px;
  white-space: pre-wrap; font-family: Consolas, monospace;
}
.preview-box { border-radius: 8px; overflow: hidden; border: 1px solid #eee; }
.preview-box iframe { width: 100%; height: 400px; border: none; }

.tpl-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.tpl-item {
  text-align: center; padding: 16px 8px; border: 1px solid #eee; border-radius: 10px;
  cursor: pointer; transition: all 0.2s;
}
.tpl-item:hover { border-color: #409eff; box-shadow: 0 2px 8px rgba(64,158,255,0.15); }
.tpl-icon { font-size: 28px; margin-bottom: 6px; }
.tpl-name { font-size: 14px; font-weight: 600; color: #333; }
.tpl-sub { font-size: 12px; color: #999; margin-top: 2px; }

@media (max-width: 768px) { .tpl-grid { grid-template-columns: repeat(2, 1fr); } }
</style>
