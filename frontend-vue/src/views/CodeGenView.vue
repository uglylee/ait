<template>
  <div class="max-w-3xl mx-auto px-6 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800">AI 代码生成</h1>
      <p class="text-sm text-gray-400 mt-1">输入需求描述，自动生成项目代码</p>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-4">
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">项目描述</label>
        <textarea v-model="form.description" rows="3"
          class="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:border-indigo-400 focus:outline-none resize-y"
          placeholder="描述你想要的项目，例如：&#10;- 写一个贪吃蛇游戏&#10;- 做一个待办事项网站&#10;- 创建一个Python爬虫"
        ></textarea>
      </div>
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">技术栈</label>
        <div class="flex gap-2">
          <button v-for="l in langs" :key="l.value"
            :class="['px-5 py-2 rounded-full text-sm border transition-all',
              form.lang === l.value ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-white text-gray-500 border-gray-200 hover:border-indigo-300']"
            @click="form.lang = l.value"
          >{{ l.label }}</button>
        </div>
      </div>
      <button
        :disabled="generating || !form.description.trim()"
        :class="['w-full py-3 rounded-lg text-sm font-medium transition-colors',
          generating || !form.description.trim() ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-indigo-500 text-white hover:bg-indigo-600']"
        @click="generate"
      >{{ generating ? '生成中...' : '生成项目' }}</button>
    </div>

    <div v-if="logs.length" class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-4">
      <div class="flex justify-between items-center mb-3 text-sm font-semibold text-gray-700">
        <span>生成过程</span>
        <span v-if="done" class="px-2 py-0.5 rounded-full text-xs bg-green-50 text-green-600 font-normal">完成</span>
        <span v-else-if="failed" class="px-2 py-0.5 rounded-full text-xs bg-red-50 text-red-500 font-normal">失败</span>
        <span v-else class="px-2 py-0.5 rounded-full text-xs bg-blue-50 text-blue-500 font-normal">运行中</span>
      </div>
      <div class="max-h-[180px] overflow-y-auto bg-gray-50 rounded-lg p-3" ref="logList">
        <div v-for="(log, i) in logs" :key="i" :class="['flex items-center gap-2 py-1 text-xs', log.type === 'error' ? 'text-red-500' : log.type === 'done' ? 'text-green-600' : 'text-gray-600']">
          <span :class="['w-1.5 h-1.5 rounded-full flex-shrink-0', log.type === 'status' ? 'bg-blue-400' : log.type === 'error' ? 'bg-red-400' : log.type === 'done' ? 'bg-green-400' : 'bg-gray-300']"></span>
          {{ log.text }}
        </div>
      </div>
    </div>

    <div v-if="code" class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-4">
      <div class="flex justify-between items-center mb-3 text-sm font-semibold text-gray-700">
        <span>生成代码</span>
        <div class="flex gap-1.5">
          <button class="px-3 py-1.5 border border-gray-200 rounded-md text-xs text-gray-500 hover:border-indigo-400 hover:text-indigo-500 transition-colors" @click="copyCode">复制代码</button>
          <button class="px-3 py-1.5 rounded-md text-xs text-white bg-indigo-500 hover:bg-indigo-600 transition-colors" @click="runCode" :disabled="running">{{ running ? '运行中...' : '运行项目' }}</button>
        </div>
      </div>
      <pre class="bg-gray-900 text-gray-300 p-4 rounded-lg text-xs leading-relaxed overflow-auto max-h-[400px] whitespace-pre-wrap break-all font-mono"><code>{{ code }}</code></pre>
    </div>

    <div v-if="output" class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-4">
      <div class="text-sm font-semibold text-gray-700 mb-3">运行输出</div>
      <pre class="bg-gray-900 text-green-400 p-4 rounded-lg text-xs leading-relaxed overflow-auto max-h-[300px] whitespace-pre-wrap font-mono">{{ output }}</pre>
    </div>

    <div v-if="htmlPath" class="bg-white rounded-xl shadow-sm border border-gray-100 p-5 mb-4">
      <div class="flex justify-between items-center mb-3 text-sm font-semibold text-gray-700">
        <span>页面预览</span>
        <button class="px-3 py-1.5 border border-gray-200 rounded-md text-xs text-gray-500 hover:border-indigo-400 hover:text-indigo-500 transition-colors" @click="openBrowser">新窗口打开</button>
      </div>
      <div class="rounded-lg overflow-hidden border border-gray-100">
        <iframe :src="'file:///' + htmlPath.replace(/\\\\/g, '/')" sandbox="allow-scripts" class="w-full h-[400px] border-none"></iframe>
      </div>
    </div>

    <div v-if="!logs.length" class="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
      <div class="text-sm font-semibold text-gray-700 mb-3">快捷模板</div>
      <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div class="text-center p-4 border border-gray-100 rounded-xl cursor-pointer transition-all hover:border-indigo-300 hover:shadow-sm" v-for="t in templates" :key="t.name" @click="useTpl(t)">
          <div class="text-2xl mb-1.5">{{ t.icon }}</div>
          <div class="text-sm font-semibold text-gray-700">{{ t.name }}</div>
          <div class="text-xs text-gray-400 mt-0.5">{{ t.desc }}</div>
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
